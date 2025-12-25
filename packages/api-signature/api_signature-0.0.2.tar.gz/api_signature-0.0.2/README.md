# api-signature

用于生成和验证基于 HMAC-SHA256 的 API 请求签名的轻量工具库。

## 安装 ✅

```bash
pip install api-signature
```

## 简要说明 🔧

- 签名基于 HMAC-SHA256，默认返回 **hex（大写）** 字符串（通过 `hmac_hash` 可选择返回 Base64）。
- 支持将请求中的 `query`（字典或字符串）格式化为以 `?` 开头的查询字符串。
- 提供生成签名、生成用于 `Authorization`/自定义 header 的签名头，以及验证签名/签名头的工具。

---

## 公共函数（简短说明） 📚

- `generate_signature(appid, secret_key, url, method='GET', body=None, query=None, timestamp=None, nonce=None, ends_with_secret_key=False)`：生成原始签名字符串与签名（返回 `raw_str`, `signature`, `url`）。

- `generate_signature_header(appid, secret_key, url, method='GET', body=None, query=None, ends_with_secret_key=False, with_hash_name=True, pair_value=False)`：在 `generate_signature` 基础上生成用于 HTTP header 的签名字符串（可选带 `HMAC-SHA256 ` 前缀或键值对形式）。

- `verify_signature(appid, secret_key, url, method='GET', body=None, query=None, timestamp=None, nonce=None, ends_with_secret_key=False, verify_timestamp=True, timestamp_valid_time=300, signature='')`：验证签名是否匹配并可选校验时间戳，返回 `code/message` 等信息。

- `verify_signature_header(url, method='GET', body=None, query=None, timestamp=None, nonce=None, ends_with_secret_key=False, verify_timestamp=True, timestamp_valid_time=300, signature='', verify_hash_name=True, with_hash_name=True, pair_value=False, header_value='', get_secretkey_by_appid=None)`：解析并验证签名头，`get_secretkey_by_appid` 为异步函数，接收 `appid` 并返回对应的 `secret_key`。

---

## 示例 ✨

```python
import asyncio
from api_signature import (
    generate_signature,
    generate_signature_header,
    verify_signature,
    verify_signature_header,
)

appid = "appid"
secret_key = "secret_key"

async def main():
    # 生成签名（GET）
    sig = await generate_signature(appid, secret_key, "/path", "GET")
    print("generate_signature ->", sig)

    # 生成带 header 的签名（POST）
    header = await generate_signature_header(
        appid, secret_key, "/path", "POST", {"a": "a", "b": 1}, {"_t": "1234567890"}
    )
    print("generate_signature_header ->", header)

    # 验证签名（直接传 signature）
    vs = await verify_signature(
        url="/path",
        appid=appid,
        secret_key=secret_key,
        nonce="IsJRqILi",
        timestamp="1766335905",
        signature="FCAA034551D699945D5B6FD44562D977B0E924DDE8DA4732D5E8F53A3B929141",
    )
    print("verify_signature ->", vs)

    # 验证签名头（需提供异步回调根据 appid 获取 secret key）
    async def get_secret(appid_):
        return secret_key

    vsh = await verify_signature_header(
        url="/path",
        method="POST",
        body={"a": "a", "b": 1},
        query={"_t": "1234567890"},
        header_value="HMAC-SHA256 appid:1766336579:Ob0Fy5Xd:D6F3973B00B7463EDA081284775D4770B60430E620E9C804D8B267290AC5BD4D",
        get_secretkey_by_appid=get_secret,
    )
    print("verify_signature_header ->", vsh)

asyncio.run(main())
```
