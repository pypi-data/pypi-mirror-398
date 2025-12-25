from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import urllib3
import requests

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TapoAuthError(RuntimeError):
    pass

@dataclass(frozen=True)
class LoginState:
    cnonce: str
    stok: Optional[str] = None
    nonce: Optional[str] = None
    digest_passwd: Optional[str] = None
    user_group: Optional[str] = None
    start_seq: Optional[int] = None
    raw_response: Optional[dict[str, Any]] = None


class Camera:
    def __init__(
        self,
        ip_address: str,
        *,
        username: str = "admin",
        password: Optional[str] = None,
        encrypt_type: str = "3",
        timeout_s: float = 10.0,
        session: Optional[requests.Session] = None,
        auto_connect: bool = True,
    ) -> None:
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.encrypt_type = encrypt_type
        self.timeout_s = timeout_s

        self._session = session or requests.Session()
        self._cnonce = secrets.token_hex(8).upper()
        self._login_state: Optional[LoginState] = None
        self._seq: Optional[int] = None

        if auto_connect:
            self.connect()

    @property
    def cnonce(self) -> str:
        return self._cnonce

    @property
    def login_state(self) -> Optional[LoginState]:
        return self._login_state

    @property
    def stok(self) -> Optional[str]:
        return self._login_state.stok if self._login_state else None

    @staticmethod
    def generate_digest_passwd(*, password: str, cnonce: str, nonce: str) -> str:
        """Generate digest password used by Tapo secure v3 login.

        Formula:
            SHA256(SHA256(password) + cnonce + nonce) + cnonce + nonce
        """
        p1 = hashlib.sha256(password.encode()).hexdigest().upper()
        p2 = hashlib.sha256((p1 + cnonce + nonce).encode()).hexdigest().upper()
        return p2 + cnonce + nonce

    @staticmethod
    def _H(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()

    def _compute_tapo_tag(self, *, content: dict[str, Any], seq: int) -> str:
        if not self.password:
            raise TapoAuthError("Password is required for tapo_tag header")

        password_hash = self._H(self.password)
        first_hash = self._H(password_hash + self._cnonce)

        json_payload = self._json_dumps_gsonish(content)

        return self._H(first_hash + json_payload + str(seq))

    @staticmethod
    def _json_dumps_gsonish(obj: Any) -> str:
        s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        return s.replace("/", "\\/")

    @staticmethod
    def _sha256_bytes(s: str) -> bytes:
        return hashlib.sha256(s.encode("utf-8")).digest()

    @classmethod
    def _derive_lsk_ivb(cls, *, password: str, cnonce: str, nonce: str) -> Tuple[bytes, bytes]:
        cnonce_u = cnonce.upper()
        nonce_u = nonce.upper()

        password_hash = cls._H(password)
        first2 = cls._H(cnonce_u + password_hash + nonce_u)

        lsk = cls._sha256_bytes("lsk" + cnonce_u + nonce_u + first2)[:16]
        ivb = cls._sha256_bytes("ivb" + cnonce_u + nonce_u + first2)[:16]
        return lsk, ivb

    @staticmethod
    def _aes_cbc_encrypt_pkcs7(*, plaintext: bytes, key: bytes, iv: bytes) -> bytes:
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    @staticmethod
    def _aes_cbc_decrypt_pkcs7(*, ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded_plaintext) + unpadder.finalize()

    def _url(self) -> str:
        return f"https://{self.ip_address}/"

    def _api_url(self) -> str:
        if not self.stok:
            raise TapoAuthError("Not connected: missing stok. Call connect() first.")
        return f"https://{self.ip_address}/stok={self.stok}/ds"

    def _headers(
        self,
        *,
        seq: Optional[int] = None,
        tapo_tag: Optional[str] = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = {
            "accept": "*/*",
            "content-type": "application/json",
            "accept-language": "en-US;q=1",
            "referer": f"http://{self.ip_address}",
            "user-agent": "IOS",
            "priority": "u=3, i",
        }

        if seq is not None:
            headers["Seq"] = str(seq)

        if tapo_tag is not None:
            headers["tapo_tag"] = tapo_tag

        return headers

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post_url(self._url(), payload=payload)

    def _post_url(
        self,
        url: str,
        *,
        payload: dict[str, Any],
        seq: Optional[int] = None,
        tapo_tag: Optional[str] = None,
    ) -> dict[str, Any]:
        body = self._json_dumps_gsonish(payload)
        resp = self._session.post(
            url,
            headers=self._headers(seq=seq, tapo_tag=tapo_tag),
            data=body,
            verify=False,
            timeout=self.timeout_s,
        )
        return resp.json()

    def _encrypt_secure_passthrough_request(self, inner_payload: dict[str, Any]) -> str:
        if not self.password:
            raise TapoAuthError("Password is required for securePassthrough encryption")
        if not self._login_state or not self._login_state.nonce:
            raise TapoAuthError(
                "Missing nonce from login challenge; cannot derive encryption keys. "
                "Make sure connect() received code -40401 and stored nonce."
            )

        lsk, ivb = self._derive_lsk_ivb(
            password=self.password,
            cnonce=self._cnonce,
            nonce=self._login_state.nonce,
        )
        plaintext = self._json_dumps_gsonish(inner_payload).encode("utf-8")
        ciphertext = self._aes_cbc_encrypt_pkcs7(plaintext=plaintext, key=lsk, iv=ivb)
        return base64.b64encode(ciphertext).decode("ascii")

    def _decrypt_secure_passthrough_response(self, *, b64_payload: str) -> Any:
        if not self.password:
            raise TapoAuthError("Password is required for securePassthrough decryption")
        if not self._login_state or not self._login_state.nonce:
            raise TapoAuthError("Missing nonce from login challenge; cannot decrypt response")

        lsk, ivb = self._derive_lsk_ivb(
            password=self.password,
            cnonce=self._cnonce,
            nonce=self._login_state.nonce,
        )
        ciphertext = base64.b64decode(b64_payload)
        plaintext_bytes = self._aes_cbc_decrypt_pkcs7(ciphertext=ciphertext, key=lsk, iv=ivb)
        plaintext = plaintext_bytes.decode("utf-8")
        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            return plaintext

    def _seq_from_state(self) -> int:
        """Get sequence number from login state, defaulting to 0."""
        if not self._login_state or self._login_state.start_seq is None:
            return 0
        try:
            return int(self._login_state.start_seq)
        except (ValueError, TypeError):
            return 0

    def connect(self) -> LoginState:
        """Login and cache the resulting auth state.

        Most devices first respond with code -40401 and provide a nonce.
        We then retry with digest_passwd.
        """
        first_payload: dict[str, Any] = {
            "method": "login",
            "params": {
                "cnonce": self._cnonce,
                "username": self.username,
                "encrypt_type": self.encrypt_type,
            },
        }

        first = self._post(first_payload)

        code = first.get("result", {}).get("data", {}).get("code")

        if code == -40401:
            nonce = first.get("result", {}).get("data", {}).get("nonce", "")
            if not nonce:
                raise TapoAuthError("Login challenge missing nonce")
            if not self.password:
                raise TapoAuthError(
                    "Password required to complete digest login (got challenge -40401)"
                )

            digest = self.generate_digest_passwd(
                password=self.password,
                cnonce=self._cnonce,
                nonce=nonce,
            )
            second_payload = {
                "method": "login",
                "params": {
                    "cnonce": self._cnonce,
                    "username": self.username,
                    "encrypt_type": self.encrypt_type,
                    "digest_passwd": digest,
                },
            }
            second = self._post(second_payload)
            result = second.get("result", {}) if isinstance(second, dict) else {}
            self._login_state = LoginState(
                cnonce=self._cnonce,
                stok=result.get("stok"),
                nonce=nonce,
                digest_passwd=digest,
                user_group=result.get("user_group"),
                start_seq=result.get("start_seq"),
                raw_response=second,
            )
            self._seq = self._seq_from_state()
            return self._login_state

        # If the device logged in directly (or returned something else), still store it.
        result = first.get("result", {}) if isinstance(first, dict) else {}
        self._login_state = LoginState(
            cnonce=self._cnonce,
            stok=result.get("stok"),
            user_group=result.get("user_group"),
            start_seq=result.get("start_seq"),
            raw_response=first,
        )
        self._seq = self._seq_from_state()
        return self._login_state

    def login(self) -> LoginState:
        return self.connect()

    def custom_request(self, inner_payload: dict[str, Any]) -> Any:
        """Send an encrypted securePassthrough request to the authenticated /ds endpoint.

        - Encrypts the inner payload (inverse of decode.py)
        - Wraps it in {"method":"securePassthrough","params":{"request":"<b64>"}}
        - Sends to https://<ip>/stok=<stok>/ds with an incrementing "seq" header
        - Returns decrypted inner response when possible
        """

        if not self._login_state or not self.stok:
            self.connect()

        if self._seq is None:
            self._seq = 0
            
        seq = self._seq

        outer_payload: dict[str, Any] = {
            "method": "securePassthrough",
            "params": {
                "request": self._encrypt_secure_passthrough_request(inner_payload),
                "extra": None,
            },
        }

        tapo_tag = self._compute_tapo_tag(content=outer_payload, seq=seq)

        outer_response = self._post_url(
            self._api_url(),
            payload=outer_payload,
            seq=seq,
            tapo_tag=tapo_tag,
        )

        self._seq = seq + 1
        b64_response = (
            outer_response.get("result", {})
            .get("response")
            if isinstance(outer_response, dict)
            else None
        )
        if isinstance(b64_response, str) and b64_response:
            return self._decrypt_secure_passthrough_response(b64_payload=b64_response)
        return outer_response

    def relative_move(self, x_coord: int, y_coord: int) -> Any:
        """Move camera relatively."""
        return self.custom_request(
            {
                "method": "multipleRequest",
                "params": {
                    "requests": [
                        {
                            "method": "relativeMove",
                            "params": {
                                "motor": {
                                    "move": {
                                        "x_coord": str(x_coord),
                                        "y_coord": str(y_coord),
                                    }
                                }
                            },
                        }
                    ]
                },
            }
        )
