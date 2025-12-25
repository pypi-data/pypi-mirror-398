"""api_signature package

提供生成和验证基于 HMAC-SHA256 的 API 请求签名的工具。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import string
import time
import typing as t
from urllib.parse import urlencode


def query_stringify(query: None | dict | str) -> str:
    """将查询参数字典或查询字符串转换为以 '?' 开头的查询字符串。

    如果 query 为 None 或空，返回空字符串。
    """
    if not query:
        return ""
    if isinstance(query, str):
        return query if query.startswith("?") else f"?{query}"
    # dict 等可用 urlencode 处理
    qs = urlencode(query, doseq=True)
    return f"?{qs}" if qs else ""


class signatureParam(t.TypedDict):
    appid: str
    timestamp: str
    nonce: str
    signature: str


class GenerateSignatureResult(t.TypedDict):
    """`generate_signature` 的返回类型。

    字段：
      - raw_str: 用于计算 HMAC 的原始字符串（每段以换行分隔，且末尾包含换行）。
      - signature: 计算得到的签名（hex 小写，默认使用 HMAC-SHA256）。
      - url: 完整 URL（包含 query 部分）。
    """

    raw_str: str
    """用于计算签名的原始字符串"""
    signature: str
    """计算得到的签名（hex 小写，默认使用 HMAC-SHA256）"""
    url: str
    """完整 URL（包含 query 部分）"""


class GenerateSignatureHeaderResult(t.TypedDict):
    """`generate_signature_header` 的返回类型。

    字段：
      - url: 完整 URL（包含 query 部分）。
      - timestamp: 时间戳字符串。
      - nonce: 随机串。
      - raw_str: 用于计算签名的原始字符串（与 `GenerateSignatureResult.raw_str` 同名）。
      - signature: 计算得到的签名（hex 小写）。
      - header_value: 用于 HTTP 请求的 header 值（可能带哈希名称前缀）。
    """

    url: str
    timestamp: str
    nonce: str
    raw_str: str
    signature: str
    header_value: str


class VerifyResult(t.TypedDict, total=False):
    """`verify_signature` / `verify_signature_header` 的返回类型。

    使用 total=False 表示部分字段为可选（例如验证失败时不一定包含 appid/signature）。
    字段：
      - code: 状态码（0=成功, 1=签名错误, 2=时间戳错误, 3=hash 名称错误, 4=appid 无效）。
      - message: 可读的错误或成功信息。
      - appid: 当校验成功时返回的 appid（可选）。
      - signature: 当校验成功时返回的签名（可选）。
    """

    code: int
    message: str
    appid: str
    signature: str


def parse_signature_item(
    signature_str: str, pair_value: bool = False
) -> signatureParam:
    """解析签名项。

    - 当 `pair_value=True` 时，解析键值对（形式："k1=v1&k2=v2"），返回 `dict[str, str]`；
    - 否则按 ':' 分割为 `appid:timestamp:nonce:signature` 并返回包含键 `appid`, `timestamp`, `nonce`, `signature` 的字典（与 `signatureParam` 字段相同）。
    """
    if pair_value:
        items: list[str] = [p for p in signature_str.split("&") if p]
        res: dict[str, str] = {}
        for it in items:
            if "=" in it:
                k, v = it.split("=", 1)
                res[k.strip()] = v.strip()
        return res  # type: ignore
    parts = signature_str.split(":")
    partsLen = len(parts)
    return {
        "appid": parts[0] if partsLen > 0 else "",
        "timestamp": parts[1] if partsLen > 1 else "",
        "nonce": parts[2] if partsLen > 2 else "",
        "signature": parts[3] if partsLen > 3 else "",
    }


def hmac_hash(
    message: str, secret: str, hash_name: str = "SHA-256", to_hex: bool = True
) -> str:
    """基于 HMAC 计算摘要，默认使用 SHA-256 并返回 hex 编码字符串（小写）。"""
    key = secret.encode("utf-8")
    msg = message.encode("utf-8")
    # 支持 "SHA-256" 或 "sha256" 等写法，尝试从 hashlib 获取对应算法
    algo_name = hash_name.replace("-", "").lower()
    algo = getattr(hashlib, algo_name, hashlib.sha256)
    mac = hmac.new(key, msg, algo)
    if to_hex:
        return mac.hexdigest().upper()
    digest = mac.digest()
    return base64.b64encode(digest).decode("utf-8")


def random_str(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def generate_signature(
    appid: str,
    secret_key: str,
    url: str,
    method: str = "GET",
    body: str | dict | None = None,
    query: str | dict | None = None,
    timestamp: str | None = None,
    nonce: str | None = None,
    ends_with_secret_key: bool = False,
) -> GenerateSignatureResult:
    """生成用于请求的签名原始字符串与 HMAC 签名。

    说明：
      - 生成的原始字符串由若干部分按顺序以换行符连接（最后包含一个换行）：
        appid, METHOD, url(含query), [body（仅在非 GET 且 body 非空时）], timestamp, nonce[, secret_key（可选）]
      - 使用 `hmac_hash` 对原始字符串计算 HMAC（默认 SHA-256），返回 hex（小写）。

    参数：
      - appid: 应用 ID。
      - secret_key: 用于 HMAC 的密钥。
      - url: 请求 URL。
      - method: HTTP 方法，默认 "GET"；非 GET 请求会把 body 纳入签名。
      - body: 请求体，支持字符串或 dict。
      - query: 查询参数，支持 dict 或字符串，会使用 `query_stringify` 生成带问号的查询字符串。
      - timestamp: 可指定时间戳（字符串），默认使用当前时间戳（单位秒）。
      - nonce: 可指定随机串，默认生成 8 位随机字母数字串。
      - ends_with_secret_key: 是否在原始签名字符串末尾附加 secret_key。

    返回：
      - GenerateSignatureResult 字典，包含 `raw_str`, `signature`, `url`。

    示例：
    >>> import asyncio
    >>> from api_signature import generate_signature
    >>> res = asyncio.run(generate_signature("app1", "secret", "https://api.example.com/p", method="POST", body={"a":1}))
    >>> print(res["signature"])  # 输出签名 hex 字符串
    """
    m = method.upper()

    url_full = f"{url}{query_stringify(query)}"
    sign_arr: list[str] = [appid, m, url_full]

    if m != "GET" and body and body != "{}":
        b = body
        if not isinstance(b, str):
            b = json.dumps(b, separators=(",", ":"), ensure_ascii=False)
        sign_arr.append(b)

    timestamp = timestamp or str(int(time.time()))
    nonce = nonce or random_str(8)
    sign_arr.extend([timestamp, nonce])

    if ends_with_secret_key:
        sign_arr.append(secret_key)

    sign_str = "\n".join(sign_arr) + "\n"
    signature = hmac_hash(sign_str, secret_key)
    return {"raw_str": sign_str, "signature": signature, "url": url_full}


async def generate_signature_header(
    appid: str,
    secret_key: str,
    url: str,
    method: str = "GET",
    body: str | dict | None = None,
    query: str | dict | None = None,
    ends_with_secret_key: bool = False,
    with_hash_name: bool = True,
    pair_value: bool = False,
) -> GenerateSignatureHeaderResult:
    """生成完整签名信息（包含用于 HTTP 请求的 header 值）。

    参数：
      - appid: 应用 ID。
      - secret_key: 用于 HMAC 的密钥。
      - url: 请求 URL（不含 query）。
      - method: HTTP 方法，默认 "GET"。
      - body: 请求体（字符串或 dict）。
      - query: 查询参数（dict 或字符串）。
      - ends_with_secret_key: 是否在签名前将 secret_key 附加到源字符串末尾。
      - with_hash_name: header 值是否以哈希名称前缀（例如 "HMAC-SHA256 ") 开头。
      - pair_value: 是否使用 k=v&amp;k=v 的键值对形式代替冒号分隔形式。

    返回：
      - GenerateSignatureHeaderResult 包含 `url`, `timestamp`, `nonce`, `rawStr`, `signature`, `headerValue`。

    示例：
    >>> import asyncio
    >>> from api_signature import generate_signature_header
    >>> res = asyncio.run(generate_signature_header("app1", "secret", "https://api.example.com/p"))
    >>> print(res["headerValue"])  # 类似: HMAC-SHA256 appid:timestamp:nonce:signature
    """
    timestamp = str(int(time.time()))
    nonce = random_str(8)
    res = await generate_signature(
        appid=appid,
        secret_key=secret_key,
        url=url,
        method=method,
        body=body,
        query=query,
        timestamp=timestamp,
        nonce=nonce,
        ends_with_secret_key=ends_with_secret_key,
    )
    header_prefix = "HMAC-SHA256 " if with_hash_name else ""
    if pair_value:
        header_value = f"appid={appid}&timestamp={timestamp}&nonce={nonce}&signature={res['signature']}"
    else:
        header_value = f"{appid}:{timestamp}:{nonce}:{res['signature']}"
    return {
        "url": res["url"],
        "timestamp": timestamp,
        "nonce": nonce,
        "raw_str": res["raw_str"],
        "signature": res["signature"],
        "header_value": f"{header_prefix}{header_value}",
    }


async def verify_signature(
    appid: str,
    secret_key: str,
    url: str,
    method: str = "GET",
    body: str | dict | None = None,
    query: str | dict | None = None,
    timestamp: str | None = None,
    nonce: str | None = None,
    ends_with_secret_key: bool = False,
    verify_timestamp: bool = True,
    timestamp_valid_time: int = 300,
    signature: str = "",
) -> VerifyResult:
    """验证签名是否正确并可选校验时间戳。

    参数：
      - appid: 应用 ID。
      - secret_key: 对应 appid 的 secret_key。
      - url、method、body、query: 与签名生成时一致的请求信息。
      - timestamp、nonce: 应与被验证的签名中携带的值一致。
      - ends_with_secret_key: 与生成签名时保持一致的选项。
      - verify_timestamp: 是否校验时间戳有效期（默认 True）。
      - timestamp_valid_time: 时间戳有效期（秒），默认为 300 秒。
      - signature: 待校验的签名字符串。

    返回：
      - VerifyResult：包含 `code`（状态码）、`message`、以及在成功时返回 `appid` 和 `signature`。
        状态码说明：0=成功, 1=签名错误, 2=时间戳错误。

    示例：
    >>> import asyncio
    >>> from api_signature import verify_signature
    >>> res = asyncio.run(verify_signature("app1", "secret", "https://api.example.com/p", signature="...", timestamp="...", nonce="..."))
    >>> print(res)
    {"code": 0, "message": "success", "appid": "app1", "signature": "..."}
    """
    now_ts = int(time.time())
    if verify_timestamp:
        ts = int(timestamp or 0)
        if now_ts - ts > int(timestamp_valid_time):
            return {
                "code": 2,
                "message": f"timestamp is invalid: {ts} - {now_ts}",
            }

    sign_res = await generate_signature(
        appid=appid,
        secret_key=secret_key,
        url=url,
        method=method,
        body=body,
        query=query,
        timestamp=timestamp,
        nonce=nonce,
        ends_with_secret_key=ends_with_secret_key,
    )
    if sign_res["signature"] == signature:
        return {
            "code": 0,
            "message": "success",
            "appid": appid,
            "signature": sign_res["signature"],
        }
    return {
        "code": 1,
        "message": f"signature is invalid: {signature} - {sign_res['signature']}({sign_res['raw_str']})",
    }


async def verify_signature_header(
    url: str,
    method: str = "GET",
    body: str | dict | None = None,
    query: str | dict | None = None,
    timestamp: str | None = None,
    nonce: str | None = None,
    ends_with_secret_key: bool = False,
    verify_timestamp: bool = True,
    timestamp_valid_time: int = 300,
    signature: str = "",
    verify_hash_name: bool = True,
    with_hash_name: bool = True,
    pair_value: bool = False,
    header_value: str = "",
    get_secretkey_by_appid: t.Callable[[str], t.Coroutine[t.Any, t.Any, str]]
    | None = None,
) -> VerifyResult:
    """解析并验证签名请求头。

    说明：
      - 函数支持两种 header 编码方式：带哈希名称前缀（`HMAC-SHA256 `）或不带；
      - 支持两种签名项格式：冒号分隔（appid:timestamp:nonce:signature）或键值对（appid=...&timestamp=...）。

    参数：
      - header_value: 来自请求头的完整值（例如："HMAC-SHA256 appid:timestamp:nonce:signature"）。
      - get_secretkey_by_appid: 异步函数，传入 appid 返回对应的 secret_key。
      - 其它参数与 `verify_signature` 相同，用于生成并比对签名。

    返回：
      - VerifyResult（同 `verify_signature`），包含 `code` 与 `message` 等信息。

    示例：
    >>> import asyncio
    >>> from api_signature import verify_signature_header
    >>> async def mock_get_secret(appid: str):
    ...     return "secret"
    >>> res = asyncio.run(verify_signature_header("https://api.example.com/p", header_value="HMAC-SHA256 app1:123:abc:...", get_secretkey_by_appid=mock_get_secret, timestamp="123", nonce="abc"))
    >>> print(res)
    {"code": 0, "message": "success", "appid": "app1"}
    """

    signature = header_value
    if not signature:
        return {"code": 1, "message": "signature is empty"}

    if with_hash_name:
        parts = signature.split(" ")
        if len(parts) < 2:
            return {"code": 1, "message": "signature is empty or malformed"}
        signature = parts[1]
        if verify_hash_name and parts[0] != "HMAC-SHA256":
            return {
                "code": 3,
                "message": f"hash name is invalid: {parts[0]} - HMAC-SHA256",
            }

    sig_item = parse_signature_item(signature, pair_value)
    appid: str = sig_item.get("appid", "")
    extracted_signature: str = sig_item.get("signature", "")
    # 优先使用 header 中的 timestamp/nonce（当外部未传入时）
    timestamp = timestamp or sig_item.get("timestamp")
    nonce = nonce or sig_item.get("nonce")

    secret_key = ""
    if get_secretkey_by_appid:
        secret_key = await get_secretkey_by_appid(appid)

    if not secret_key:
        return {"code": 4, "message": f"appid is invalid: {appid}"}

    # 验证签名（将 header 中解析出的签名值传入）
    return await verify_signature(
        appid=appid,
        secret_key=secret_key,
        url=url,
        method=method,
        body=body,
        query=query,
        timestamp=timestamp,
        nonce=nonce,
        ends_with_secret_key=ends_with_secret_key,
        verify_timestamp=verify_timestamp,
        timestamp_valid_time=timestamp_valid_time,
        signature=extracted_signature,
    )
