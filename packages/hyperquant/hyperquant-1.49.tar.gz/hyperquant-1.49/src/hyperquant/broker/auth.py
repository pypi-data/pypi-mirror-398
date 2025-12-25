import base64
import hmac
import urllib.parse
import time
import hashlib
from functools import lru_cache
from typing import Any
from aiohttp import ClientWebSocketResponse, FormData, JsonPayload
from multidict import CIMultiDict
from yarl import URL
import pybotters
import json as pyjson
from urllib.parse import urlencode
from datetime import datetime, timezone
from eth_account import Account
try:
    from eth_account.messages import encode_typed_data
except ImportError:
    from eth_account.messages import encode_structured_data as encode_typed_data
from eth_utils import keccak, to_checksum_address
import secrets
from random import random

try:
    from coincurve import PrivateKey as _CoincurvePrivateKey
except Exception:  # pragma: no cover - optional dependency
    _CoincurvePrivateKey = None

POLY_ADDRESS = "POLY_ADDRESS"
POLY_SIGNATURE = "POLY_SIGNATURE"
POLY_TIMESTAMP = "POLY_TIMESTAMP"
POLY_NONCE = "POLY_NONCE"
POLY_API_KEY = "POLY_API_KEY"
POLY_PASSPHRASE = "POLY_PASSPHRASE"
CLOB_AUTH_DOMAIN = {"name": "ClobAuthDomain", "version": "1"}
CLOB_AUTH_MESSAGE = "This message attests that I control the given wallet"

_PM_DOMAIN_TYPEHASH = keccak(b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
_PM_ORDER_TYPEHASH = keccak(
    b"Order(uint256 salt,address maker,address signer,address taker,uint256 tokenId,uint256 makerAmount,uint256 takerAmount,uint256 expiration,uint256 nonce,uint256 feeRateBps,uint8 side,uint8 signatureType)"
)
_PM_DOMAIN_NAME_HASH = keccak(text="Polymarket CTF Exchange")
_PM_DOMAIN_VERSION_HASH = keccak(text="1")


def _int_to_32(val: int) -> bytes:
    return int(val).to_bytes(32, "big", signed=False)


def _addr_to_32(addr: str) -> bytes:
    # Normalize to checksum to match eth signing behavior
    normalized = to_checksum_address(addr)
    return int(normalized, 16).to_bytes(32, "big", signed=False)


@lru_cache(maxsize=32)
def _pm_domain_separator(chain_id: int, verifying_contract: str) -> bytes:
    return keccak(
        _PM_DOMAIN_TYPEHASH
        + _PM_DOMAIN_NAME_HASH
        + _PM_DOMAIN_VERSION_HASH
        + _int_to_32(chain_id)
        + _addr_to_32(verifying_contract),
    )


def _pm_order_hash(message: dict[str, Any]) -> bytes:
    """Manually hash the Polymarket Order struct for EIP-712."""
    return keccak(
        _PM_ORDER_TYPEHASH
        + _int_to_32(message["salt"])
        + _addr_to_32(message["maker"])
        + _addr_to_32(message["signer"])
        + _addr_to_32(message["taker"])
        + _int_to_32(message["tokenId"])
        + _int_to_32(message["makerAmount"])
        + _int_to_32(message["takerAmount"])
        + _int_to_32(message["expiration"])
        + _int_to_32(message["nonce"])
        + _int_to_32(message["feeRateBps"])
        + _int_to_32(message["side"])
        + _int_to_32(message["signatureType"]),
    )


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()



def serialize(obj, prefix=''):
    """
    Python 版 UK/v：递归排序 + urlencode + 展平
    """
    def _serialize(obj, prefix=''):
        if obj is None:
            return []
        if isinstance(obj, dict):
            items = []
            for k in sorted(obj.keys()):
                v = obj[k]
                n = f"{prefix}[{k}]" if prefix else k
                items.extend(_serialize(v, n))
            return items
        elif isinstance(obj, list):
            # JS style: output key once, then join values by &
            values = []
            for v in obj:
                if isinstance(v, dict):
                    # Recursively serialize dict, but drop key= part (just use value part)
                    sub = _serialize(v, prefix)
                    # sub is a list of key=value, but we want only value part
                    for s in sub:
                        # s is like 'key=value', need only value
                        parts = s.split('=', 1)
                        if len(parts) == 2:
                            values.append(parts[1])
                        else:
                            values.append(parts[0])
                else:
                    # Handle booleans and empty strings
                    if isinstance(v, bool):
                        val = "true" if v else "false"
                    elif v == "":
                        val = ""
                    else:
                        val = str(v)
                    values.append(val)
            return [f"{urllib.parse.quote(str(prefix))}={'&'.join(values)}"]
        else:
            # Handle booleans and empty strings
            if isinstance(obj, bool):
                val = "true" if obj else "false"
            elif obj == "":
                val = ""
            else:
                val = str(obj)
            return [f"{urllib.parse.quote(str(prefix))}={val}"]
    return "&".join(_serialize(obj, prefix))

# 🔑 Ourbit 的鉴权函数
class Auth:
    @staticmethod
    def edgex(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data = kwargs.get("data") or {}
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        api_key:str = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][0]
        secret = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][1]
        passphrase:str = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][2]
        passphrase = passphrase.split("-")[0]
        timestamp = str(int(time.time() * 1000))
        # timestamp = "1758535055061"

        raw_body = ""
        if data and method.upper() in ["POST", "PUT", "PATCH"] and data:
            raw_body = serialize(data)
        else:
            raw_body = serialize(dict(url.query.items()))


        secret_quoted = urllib.parse.quote(secret, safe="")
        b64_secret = base64.b64encode(secret_quoted.encode("utf-8")).decode()
        message = f"{timestamp}{method.upper()}{url.raw_path}{raw_body}"
        sign = hmac.new(b64_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
        
        sigh_header =  {
                "X-edgeX-Api-Key": api_key,
                "X-edgeX-Passphrase": passphrase,
                "X-edgeX-Signature": sign,
                "X-edgeX-Timestamp": timestamp,
        }
        # ws单独进行签名
        if headers.get("Upgrade") == "websocket":
            json_str = pyjson.dumps(sigh_header, separators=(",", ":"))
            b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
            b64_str.replace("=", "")
            headers.update({"Sec-WebSocket-Protocol": b64_str})
        else:
            headers.update(sigh_header)

        if data:
            kwargs.update({"data": JsonPayload(data)})

        return args
    
    @staticmethod
    def ourbit(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data = kwargs.get("data") or {}
        headers: CIMultiDict = kwargs["headers"]

        # 从 session 里取 token
        session = kwargs["session"]
        token = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][0]

        # 时间戳 & body
        now_ms = int(time.time() * 1000)
        raw_body_for_sign = (
            data
            if isinstance(data, str)
            else pyjson.dumps(data, separators=(",", ":"), ensure_ascii=False)
        )

        # 签名
        mid_hash = md5_hex(f"{token}{now_ms}")[7:]
        final_hash = md5_hex(f"{now_ms}{raw_body_for_sign}{mid_hash}")

        # 设置 headers
        headers.update(
            {
                "Authorization": token,
                "Language": "Chinese",
                "language": "Chinese",
                "Content-Type": "application/json",
                "x-ourbit-sign": final_hash,
                "x-ourbit-nonce": str(now_ms),
            }
        )

        # 更新 kwargs.body，保证发出去的与签名一致
        kwargs.update({"data": raw_body_for_sign})

        return args

    @staticmethod
    def ourbit_spot(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data = kwargs.get("data") or {}
        headers: CIMultiDict = kwargs["headers"]

        # 从 session 里取 token
        session = kwargs["session"]
        token = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][0]
        cookie = f"uc_token={token}; u_id={token}; "
        headers.update({"cookie": cookie})
        return args

    @staticmethod
    def lbank(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data = kwargs.get("data") or {}
        headers: CIMultiDict = kwargs["headers"]

        # 从 session 里取 api_key & secret
        session = kwargs["session"]
        token = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name][0]


        # 设置 headers
        headers.update(
            {
                "ex-language": 'zh-TW',
                "ex-token": token,
                "source": "4",
                "versionflage": "true",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
            }
        )

        # 更新 kwargs.body，保证发出去的与签名一致
        # kwargs.update({"data": raw_body_for_sign})

        return args

    @staticmethod
    def deepcoin(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0].upper()
        url: URL = args[1]
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        creds = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name]
        if len(creds) < 3:
            raise RuntimeError("DeepCoin credentials must include api_key, secret, passphrase")
        api_key, secret, passphrase = creds[0], creds[1], creds[2]

        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        body_str = ""
        json_body = kwargs.pop("json", None)
        data_body = kwargs.get("data")
        if method in {"POST", "PUT", "PATCH"}:
            payload = json_body if json_body is not None else data_body
            if payload is not None:
                if isinstance(payload, (dict, list)):
                    body_str = pyjson.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                    kwargs["data"] = body_str
                else:
                    body_str = str(payload)
                    kwargs["data"] = body_str
            else:
                kwargs["data"] = body_str
        else:
            if json_body is not None:
                # GET requests should not carry JSON bodies
                kwargs.pop("json", None)
            if data_body is not None:
                kwargs["data"] = data_body

        request_path = url.raw_path_qs or url.raw_path
        message = f"{timestamp}{method}{request_path}{body_str}"
        secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
        signature = hmac.new(secret_bytes, message.encode("utf-8"), hashlib.sha256).digest()
        sign_b64 = base64.b64encode(signature).decode()

        headers.update(
            {
                "DC-ACCESS-KEY": api_key,
                "DC-ACCESS-PASSPHRASE": passphrase,
                "DC-ACCESS-TIMESTAMP": timestamp,
                "DC-ACCESS-SIGN": sign_b64,
                "Content-Type": headers.get("Content-Type", "application/json"),
            }
        )

        return args

    @staticmethod
    def bitmart(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        host_key = url.host
        try:
            api_name = pybotters.auth.Hosts.items[host_key].name
        except (KeyError, AttributeError):
            api_name = host_key

        creds = session.__dict__.get("_apis", {}).get(api_name)
        if not creds or len(creds) < 3:
            raise RuntimeError("Bitmart credentials (accessKey, accessSalt, device) are required")

        access_key = creds[0]
        access_salt = creds[1]
        access_salt = access_salt.decode("utf-8")
        device = creds[2]
        extra_cookie = creds[3] if len(creds) > 3 else None

        cookie_parts = [
            f"accessKey={access_key}",
            f"accessSalt={access_salt}",
            "hasDelegation=false",
            "delegationType=0",
            "delegationTypeList=[]",
        ]
        if extra_cookie:
            if isinstance(extra_cookie, str) and extra_cookie:
                cookie_parts.append(extra_cookie.strip(";"))

        headers["cookie"] = "; ".join(cookie_parts)

        headers.setdefault("x-bm-client", "WEB")
        headers.setdefault("x-bm-contract", "2")
        headers.setdefault("x-bm-device", device)
        headers.setdefault("x-bm-timezone", "Asia/Shanghai")
        headers.setdefault("x-bm-timezone-offset", "-480")
        headers.setdefault("x-bm-tag", "")
        headers.setdefault("x-bm-version", "5e13905")
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0')

        ua = headers.get("User-Agent") or headers.get("user-agent")
        if ua:
            headers.setdefault("x-bm-ua", ua)

        return args

    @staticmethod
    def bitmart_api(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        """Bitmart OpenAPI (futures v2) signing for api-cloud-v2.bitmart.com.

        Spec per docs:
        X-BM-SIGN = hex_lower(HMAC_SHA256(secret, timestamp + '#' + memo + '#' + payload_string))
        - For POST: payload_string is the JSON body string
        - For GET: payload_string is the query string (if any), otherwise empty
        Headers required: X-BM-KEY, X-BM-TIMESTAMP, X-BM-SIGN
        """
        method: str = args[0]
        url: URL = args[1]
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        try:
            api_name = pybotters.auth.Hosts.items[url.host].name
        except (KeyError, AttributeError):
            api_name = url.host

        creds = session.__dict__.get("_apis", {}).get(api_name)
        if not creds or len(creds) < 3:
            raise RuntimeError("Bitmart API credentials (access_key, secret, memo) are required")

        access_key = creds[0]
        secret = creds[1]
        memo = creds[2]
        if isinstance(secret, str):
            secret_bytes = secret.encode("utf-8")
        else:
            secret_bytes = secret
        if isinstance(memo, bytes):
            memo = memo.decode("utf-8")

        timestamp = str(int(time.time() * 1000))
        method_upper = method.upper()

        # Build query string
        params = kwargs.get("params")
        if isinstance(params, dict) and params:
            query_items = [f"{k}={v}" for k, v in params.items() if v is not None]
            query_string = "&".join(query_items)
        else:
            query_string = url.query_string

        # Build body string for signing and ensure sending matches signature
        body = None
        body_str = ""
        if method_upper == "GET":
            body_str = query_string or ""
        else:
            # Prefer original JSON object if present for deterministic signing
            if kwargs.get("json") is not None:
                body = kwargs.get("json")
            else:
                body = kwargs.get("data")

            # If upstream already turned JSON into JsonPayload, extract its value
            if isinstance(body, JsonPayload):
                body_value = getattr(body, "_value", None)
            else:
                body_value = body

            if isinstance(body_value, (dict, list)):
                # Compact JSON to avoid whitespace discrepancies and sign exact bytes we send
                body_str = pyjson.dumps(body_value, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = body_str
                kwargs.pop("json", None)
            elif isinstance(body_value, (str, bytes)):
                # Sign and send exactly this string/bytes
                body_str = body_value.decode("utf-8") if isinstance(body_value, bytes) else body_value
                kwargs["data"] = body_str
                kwargs.pop("json", None)
            elif body_value is None:
                body_str = ""
            else:
                # Fallback: string conversion (should still be JSON-like)
                body_str = str(body_value)
                kwargs["data"] = body_str
                kwargs.pop("json", None)

        # Prehash format: timestamp#memo#payload
        message = f"{timestamp}#{memo}#{body_str}"
        signature_hex = hmac.new(secret_bytes, message.encode("utf-8"), hashlib.sha256).hexdigest()

        headers.update(
            {
                "X-BM-KEY": access_key,
                "X-BM-TIMESTAMP": timestamp,
                "X-BM-SIGN": signature_hex,
                "Content-Type": "application/json; charset=UTF-8",
            }
        )

        return args

    @staticmethod
    def coinw(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        try:
            api_key, secret, _ = session.__dict__["_apis"][pybotters.auth.Hosts.items[url.host].name]
        except (KeyError, ValueError):
            raise RuntimeError("CoinW credentials (api_key, secret) are required")

        timestamp = str(int(time.time() * 1000))
        method_upper = method.upper()

        params = kwargs.get("params")
        query_string = ""
        if isinstance(params, dict) and params:
            query_items = [
                f"{key}={value}"
                for key, value in params.items()
                if value is not None
            ]
            query_string = "&".join(query_items)
        elif url.query_string:
            query_string = url.query_string

        body_str = ""

        if method_upper == "GET":
            body = None
            data = None
        else:
            body = kwargs.get("json")
            data = kwargs.get("data")
            payload = body if body is not None else data
            if isinstance(payload, (dict, list)):
                body_str = pyjson.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = body_str
                kwargs.pop("json", None)
            elif payload is not None:
                body_str = str(payload)
                kwargs["data"] = body_str
                kwargs.pop("json", None)

        if query_string:
            path = f"{url.raw_path}?{query_string}"
        else:
            path = url.raw_path

        message = f"{timestamp}{method_upper}{path}{body_str}"
        signature = hmac.new(
            secret, message.encode("utf-8"), hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode("ascii")

        headers.update(
            {
                "sign": signature_b64,
                "api_key": api_key,
                "timestamp": timestamp,
            }
        )

        if method_upper in {"POST", "PUT", "PATCH", "DELETE"} and "data" in kwargs:
            headers.setdefault("Content-Type", "application/json")

        return args

    @staticmethod
    def polymarket_back(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        method: str = args[0].upper()
        url: URL = args[1]
        headers: CIMultiDict = kwargs["headers"]

        session = kwargs["session"]
        try:
            api_name = pybotters.auth.Hosts.items[url.host].name
            creds = session.__dict__["_apis"].get(api_name)
        except (KeyError, AttributeError):
            return args

        if not creds:
            return args

        if isinstance(creds, tuple):
            creds = list(creds)
            session.__dict__["_apis"][api_name] = creds

        private_key = creds[0] if len(creds) > 0 and creds[0] else None
        if private_key:
            pk_str = str(private_key)
            if not pk_str.startswith("0x"):
                pk_str = f"0x{pk_str}"
                try:
                    session.__dict__["_apis"][api_name][0] = pk_str
                except Exception:
                    pass
            private_key = pk_str

        packed_extra = creds[2] if len(creds) > 2 else None
        packed_api_key = packed_api_secret = packed_passphrase = None
        packed_chain_id = packed_wallet = None
        if isinstance(packed_extra, (list, tuple)):
            def _packed_value(idx: int):
                if idx >= len(packed_extra):
                    return None
                value = packed_extra[idx]
                if isinstance(value, str):
                    value = value.strip()
                return value or None

            packed_api_key = _packed_value(0)
            packed_api_secret = _packed_value(1)
            packed_passphrase = _packed_value(2)
            packed_chain_id = _packed_value(3)
            packed_wallet = _packed_value(4)
        elif isinstance(packed_extra, str):
            packed_wallet = packed_extra or None

        existing_chain_id = session.__dict__.get("_polymarket_chain_id")
        if existing_chain_id is None:
            chain_id = 137
            if packed_chain_id is not None:
                try:
                    chain_id = int(packed_chain_id)
                except (TypeError, ValueError):
                    chain_id = 137
            session.__dict__["_polymarket_chain_id"] = chain_id
        else:
            chain_id = existing_chain_id

        api_meta = session.__dict__.get("_polymarket_api_creds") or {}
        if (not api_meta.get("api_key") or not api_meta.get("api_secret") or not api_meta.get("api_passphrase")) and (
            packed_api_key and packed_api_secret and packed_passphrase
        ):
            api_meta = {
                "api_key": packed_api_key,
                "api_secret": packed_api_secret,
                "api_passphrase": packed_passphrase,
            }
            session.__dict__["_polymarket_api_creds"] = api_meta

        if packed_wallet and len(creds) > 2 and isinstance(creds[2], (list, tuple)):
            creds[2] = packed_wallet

        api_key = api_meta.get("api_key")
        api_secret = api_meta.get("api_secret")
        api_passphrase = api_meta.get("api_passphrase")

        raw_path = url.raw_path
        path_with_query = url.raw_path_qs or raw_path
        level1_only_paths = {"/auth/api-key", "/auth/derive-api-key"}
        requires_level1 = raw_path in level1_only_paths

        if requires_level1:
            if not private_key:
                raise RuntimeError("Polymarket private key is required for auth endpoints")
            params = kwargs.get("params")
            nonce = 0
            if isinstance(params, dict) and "nonce" in params:
                try:
                    nonce = int(params.pop("nonce"))
                except (TypeError, ValueError):
                    nonce = 0
                if not params:
                    kwargs.pop("params", None)
            timestamp = int(time.time())
            typed_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                    ],
                    "ClobAuth": [
                        {"name": "address", "type": "address"},
                        {"name": "timestamp", "type": "string"},
                        {"name": "nonce", "type": "uint256"},
                        {"name": "message", "type": "string"},
                    ],
                },
                "domain": {**CLOB_AUTH_DOMAIN, "chainId": chain_id},
                "primaryType": "ClobAuth",
                "message": {
                    "address": Account.from_key(private_key).address,
                    "timestamp": str(timestamp),
                    "nonce": nonce,
                    "message": CLOB_AUTH_MESSAGE,
                },
            }
            encoded = encode_typed_data(full_message=typed_data)
            signature = Account.sign_message(encoded, private_key).signature.hex()
            if not signature.startswith("0x"):
                signature = f"0x{signature}"

            headers.update(
                {
                    POLY_ADDRESS: Account.from_key(private_key).address,
                    POLY_SIGNATURE: signature,
                    POLY_TIMESTAMP: str(timestamp),
                    POLY_NONCE: str(int(nonce)),
                }
            )
            return args

        if not (private_key and api_key and api_secret and api_passphrase):
            return args

        timestamp = int(time.time())
        json_body = kwargs.pop("json", None)
        data_body = kwargs.get("data")
        body_for_sign = None
        body_str = ""

        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Preserve Python object for signature to mimic official client
            if json_body is not None:
                body_for_sign = json_body
                body_str = pyjson.dumps(json_body, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = body_str
            elif isinstance(data_body, (dict, list)):
                body_for_sign = data_body
                body_str = pyjson.dumps(data_body, separators=(",", ":"), ensure_ascii=False)
                kwargs["data"] = body_str
            elif data_body is not None:
                body_for_sign = data_body
                body_str = str(data_body)
                kwargs["data"] = body_str
            else:
                kwargs["data"] = ""
        else:
            if data_body is not None and not isinstance(data_body, (FormData, JsonPayload)):
                kwargs.pop("data", None)
            body_str = ""
            body_for_sign = None

        try:
            secret_bytes = base64.urlsafe_b64decode(api_secret)
        except Exception:
            secret_bytes = base64.urlsafe_b64decode(str(api_secret))

        # Build message like py_clob_client: str(body).replace('\'', '"') when body present
        if body_for_sign is not None:
            serialized = str(body_for_sign).replace("'", '"')
        else:
            serialized = ""
        message = f"{timestamp}{method}{raw_path}{serialized}"
        signature = hmac.new(secret_bytes, message.encode("utf-8"), hashlib.sha256).digest()
        sign_b64 = base64.urlsafe_b64encode(signature).decode("utf-8")

        headers.update(
            {
                POLY_ADDRESS: Account.from_key(private_key).address,
                POLY_SIGNATURE: sign_b64,
                POLY_TIMESTAMP: str(timestamp),
                POLY_API_KEY: api_key,
                POLY_PASSPHRASE: api_passphrase,
            }
        )
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            headers.setdefault("Content-Type", "application/json")

        return args

    @staticmethod
    def polymarket(args: tuple[str, URL], kwargs: dict[str, Any]) -> tuple[str, URL]:
        """Alias kept for backward compatibility with pybotters host registration."""
        return Auth.polymarket_back(args, kwargs)

    # --------------------------
    # Polymarket order signing
    # --------------------------
    @staticmethod
    def sign_polymarket_order(
        *,
        private_key: str,
        chain_id: int,
        exchange_address: str,
        order: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Sign a Polymarket CTF order via EIP-712 and return a submission-ready dict.

        Expects 'order' to contain raw fields:
        - maker, signer, taker (addresses)
        - tokenId, makerAmount, takerAmount, expiration, nonce, feeRateBps (ints)
        - side (0=BUY, 1=SELL), signatureType (int), salt (optional)
        """
        # Prepare message fields
        # Salt generation mirrors py_order_utils (round(now * random()))
        try:
            now_ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
            generated_salt = round(now_ts * random())
        except Exception:
            generated_salt = int(time.time())
        side = int(order.get("side", 0))
        signature_type = int(order.get("signatureType", 1))
        # Normalize addresses to checksum
        try:
            from web3 import Web3
            maker_addr = Web3.to_checksum_address(order["maker"]) if order.get("maker") else None
            signer_addr = Web3.to_checksum_address(order.get("signer") or Account.from_key(private_key).address)
            taker_addr = Web3.to_checksum_address(order.get("taker") or "0x0000000000000000000000000000000000000000")
            exchange_addr = Web3.to_checksum_address(exchange_address)
        except Exception:
            maker_addr = order.get("maker")
            signer_addr = order.get("signer") or Account.from_key(private_key).address
            taker_addr = order.get("taker") or "0x0000000000000000000000000000000000000000"
            exchange_addr = exchange_address

        message = {
            "salt": int(order.get("salt") or generated_salt),
            "maker": maker_addr,
            "signer": signer_addr,
            "taker": taker_addr,
            "tokenId": int(order["tokenId"]),
            "makerAmount": int(order["makerAmount"]),
            "takerAmount": int(order["takerAmount"]),
            "expiration": int(order.get("expiration", 0)),
            "nonce": int(order.get("nonce", 0)),
            "feeRateBps": int(order.get("feeRateBps", 0)),
            "side": side,
            "signatureType": signature_type,
        }

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Order": [
                    {"name": "salt", "type": "uint256"},
                    {"name": "maker", "type": "address"},
                    {"name": "signer", "type": "address"},
                    {"name": "taker", "type": "address"},
                    {"name": "tokenId", "type": "uint256"},
                    {"name": "makerAmount", "type": "uint256"},
                    {"name": "takerAmount", "type": "uint256"},
                    {"name": "expiration", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "feeRateBps", "type": "uint256"},
                    {"name": "side", "type": "uint8"},
                    {"name": "signatureType", "type": "uint8"},
                ],
            },
            "domain": {
                "name": "Polymarket CTF Exchange",
                "version": "1",
                "chainId": int(chain_id),
                "verifyingContract": exchange_addr,
            },
            "primaryType": "Order",
            "message": message,
        }

        encoded = encode_typed_data(full_message=typed_data)
        signature = Account.sign_message(encoded, private_key).signature.hex()
        if not signature.startswith("0x"):
            signature = f"0x{signature}"

        # Convert to submission-friendly dict (stringify big ints; side as BUY/SELL)
        out = {
            # keep salt as int to mirror official client
            "salt": int(message["salt"]),
            "maker": message["maker"],
            "signer": message["signer"],
            "taker": message["taker"],
            "tokenId": str(message["tokenId"]),
            "makerAmount": str(message["makerAmount"]),
            "takerAmount": str(message["takerAmount"]),
            "expiration": str(message["expiration"]),
            "nonce": str(message["nonce"]),
            "feeRateBps": str(message["feeRateBps"]),
            "side": "BUY" if side == 0 else "SELL",
            "signatureType": int(signature_type),
            "signature": signature,
        }
        return out

    @staticmethod
    def sign_polymarket_order2(
        *,
        private_key: str,
        chain_id: int,
        exchange_address: str,
        order: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fast EIP-712 signer using coincurve + manual hashing.

        Avoids heavy typed-data helpers by caching type/domain hashes and
        signing the final digest directly.
        """
        if _CoincurvePrivateKey is None:
            raise RuntimeError("coincurve is required for sign_polymarket_order2")

        try:
            now_ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
            generated_salt = round(now_ts * random())
        except Exception:
            generated_salt = int(time.time())

        side = int(order.get("side", 0))
        signature_type = int(order.get("signatureType", 1))
        signer_addr = order.get("signer") or Account.from_key(private_key).address
        taker_addr = order.get("taker") or "0x0000000000000000000000000000000000000000"

        message = {
            "salt": int(order.get("salt") or generated_salt),
            "maker": order.get("maker"),
            "signer": signer_addr,
            "taker": taker_addr,
            "tokenId": int(order["tokenId"]),
            "makerAmount": int(order["makerAmount"]),
            "takerAmount": int(order["takerAmount"]),
            "expiration": int(order.get("expiration", 0)),
            "nonce": int(order.get("nonce", 0)),
            "feeRateBps": int(order.get("feeRateBps", 0)),
            "side": side,
            "signatureType": signature_type,
        }

        # Normalize addresses for hashing
        exchange_addr = to_checksum_address(exchange_address)
        message["maker"] = to_checksum_address(message["maker"])
        message["signer"] = to_checksum_address(message["signer"])
        message["taker"] = to_checksum_address(message["taker"])

        domain_sep = _pm_domain_separator(int(chain_id), exchange_addr)
        msg_hash = _pm_order_hash(message)
        typed_hash = keccak(b"\x19\x01" + domain_sep + msg_hash)

        pk_bytes = bytes.fromhex(private_key[2:] if private_key.startswith("0x") else private_key)
        sig65 = _CoincurvePrivateKey(pk_bytes).sign_recoverable(typed_hash, hasher=None)
        r, s, rec_id = sig65[:32], sig65[32:64], sig65[64]
        v = rec_id + 27  # align with eth_account v
        signature = "0x" + (r + s + bytes([v])).hex()

        return {
            "salt": int(message["salt"]),
            "maker": message["maker"],
            "signer": message["signer"],
            "taker": message["taker"],
            "tokenId": str(message["tokenId"]),
            "makerAmount": str(message["makerAmount"]),
            "takerAmount": str(message["takerAmount"]),
            "expiration": str(message["expiration"]),
            "nonce": str(message["nonce"]),
            "feeRateBps": str(message["feeRateBps"]),
            "side": "BUY" if side == 0 else "SELL",
            "signatureType": int(signature_type),
            "signature": signature,
        }

pybotters.auth.Hosts.items["futures.ourbit.com"] = pybotters.auth.Item(
    "ourbit", Auth.ourbit
)
pybotters.auth.Hosts.items["www.ourbit.com"] = pybotters.auth.Item(
    "ourbit", Auth.ourbit_spot
)

pybotters.auth.Hosts.items["www.ourbit.com"] = pybotters.auth.Item(
    "ourbit", Auth.ourbit_spot
)

pybotters.auth.Hosts.items["pro.edgex.exchange"] = pybotters.auth.Item(
    "edgex", Auth.edgex
)


pybotters.auth.Hosts.items["quote.edgex.exchange"] = pybotters.auth.Item(
    "edgex", Auth.edgex
)

pybotters.auth.Hosts.items["uuapi.rerrkvifj.com"] = pybotters.auth.Item(
    "lbank", Auth.lbank
)

pybotters.auth.Hosts.items["api.coinw.com"] = pybotters.auth.Item(
    "coinw", Auth.coinw
)

pybotters.auth.Hosts.items["derivatives.bitmart.com"] = pybotters.auth.Item(
    "bitmart", Auth.bitmart
)

pybotters.auth.Hosts.items["api-cloud-v2.bitmart.com"] = pybotters.auth.Item(
    "bitmart_api", Auth.bitmart_api
)

pybotters.auth.Hosts.items["api.deepcoin.com"] = pybotters.auth.Item(
    "deepcoin", Auth.deepcoin
)
pybotters.auth.Hosts.items["www.deepcoin.com"] = pybotters.auth.Item(
    "deepcoin", Auth.deepcoin
)
pybotters.auth.Hosts.items["clob.polymarket.com"] = pybotters.auth.Item(
    "polymarket", Auth.polymarket
)
pybotters.auth.Hosts.items["qa-clob.polymarket.com"] = pybotters.auth.Item(
    "polymarket", Auth.polymarket
)
