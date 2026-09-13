# -*- coding: utf-8 -*-
"""
China Data Toolkit API —— 中国数据校验与合规脱敏 API

设计原则（重要）：
    只用纯算法 + 极小内置字表，不抓取任何外部数据、不依赖任何在线服务。
    好处：不会因为上游改版而失效，维护成本接近 0。
    这是它能在 RapidAPI 上"挂上去就基本不用管"的根本原因。

面向市场：
    RapidAPI 是全球英文开发者市场，所以**所有对外文案和响应值都是英文**。
    需要中文时传 lang=zh。

启动本地调试：
    python3 -m uvicorn main:app --reload --port 8000
然后打开 http://127.0.0.1:8000/docs 就能看到交互式文档。
"""

import copy
import json
import os
import random
import re
import string
from datetime import date, datetime
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

# ==========================================================================
# 常量与内置数据（都很小，且永不失效）
# ==========================================================================

BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://china-data-toolkit-api.onrender.com")

# 身份证前 2 位省级代码：代码 -> (英文名, 中文名)
PROVINCE = {
    "11": ("Beijing", "北京市"), "12": ("Tianjin", "天津市"), "13": ("Hebei", "河北省"),
    "14": ("Shanxi", "山西省"), "15": ("Inner Mongolia", "内蒙古自治区"),
    "21": ("Liaoning", "辽宁省"), "22": ("Jilin", "吉林省"), "23": ("Heilongjiang", "黑龙江省"),
    "31": ("Shanghai", "上海市"), "32": ("Jiangsu", "江苏省"), "33": ("Zhejiang", "浙江省"),
    "34": ("Anhui", "安徽省"), "35": ("Fujian", "福建省"), "36": ("Jiangxi", "江西省"),
    "37": ("Shandong", "山东省"),
    "41": ("Henan", "河南省"), "42": ("Hubei", "湖北省"), "43": ("Hunan", "湖南省"),
    "44": ("Guangdong", "广东省"), "45": ("Guangxi", "广西壮族自治区"), "46": ("Hainan", "海南省"),
    "50": ("Chongqing", "重庆市"), "51": ("Sichuan", "四川省"), "52": ("Guizhou", "贵州省"),
    "53": ("Yunnan", "云南省"), "54": ("Tibet", "西藏自治区"),
    "61": ("Shaanxi", "陕西省"), "62": ("Gansu", "甘肃省"), "63": ("Qinghai", "青海省"),
    "64": ("Ningxia", "宁夏回族自治区"), "65": ("Xinjiang", "新疆维吾尔自治区"),
    "71": ("Taiwan", "台湾省"), "81": ("Hong Kong", "香港特别行政区"),
    "82": ("Macau", "澳门特别行政区"), "91": ("Foreign", "国外"),
}

# 身份证校验位
ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
ID_CHECK = "10X98765432"

# 统一社会信用代码（GB 32100-2015）
USCC_CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"      # 31 个，去掉 I O S V Z
USCC_WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]

# 手机号段前缀（工信部公开号段）：前缀 -> (英文运营商, 中文运营商)
PHONE_PREFIX = {
    "134": ("China Mobile", "中国移动"), "135": ("China Mobile", "中国移动"),
    "136": ("China Mobile", "中国移动"), "137": ("China Mobile", "中国移动"),
    "138": ("China Mobile", "中国移动"), "139": ("China Mobile", "中国移动"),
    "147": ("China Mobile", "中国移动"), "150": ("China Mobile", "中国移动"),
    "151": ("China Mobile", "中国移动"), "152": ("China Mobile", "中国移动"),
    "157": ("China Mobile", "中国移动"), "158": ("China Mobile", "中国移动"),
    "159": ("China Mobile", "中国移动"), "172": ("China Mobile", "中国移动"),
    "178": ("China Mobile", "中国移动"), "182": ("China Mobile", "中国移动"),
    "183": ("China Mobile", "中国移动"), "184": ("China Mobile", "中国移动"),
    "187": ("China Mobile", "中国移动"), "188": ("China Mobile", "中国移动"),
    "198": ("China Mobile", "中国移动"),
    "130": ("China Unicom", "中国联通"), "131": ("China Unicom", "中国联通"),
    "132": ("China Unicom", "中国联通"), "145": ("China Unicom", "中国联通"),
    "155": ("China Unicom", "中国联通"), "156": ("China Unicom", "中国联通"),
    "166": ("China Unicom", "中国联通"), "171": ("China Unicom", "中国联通"),
    "175": ("China Unicom", "中国联通"), "176": ("China Unicom", "中国联通"),
    "185": ("China Unicom", "中国联通"), "186": ("China Unicom", "中国联通"),
    "133": ("China Telecom", "中国电信"), "149": ("China Telecom", "中国电信"),
    "153": ("China Telecom", "中国电信"), "173": ("China Telecom", "中国电信"),
    "177": ("China Telecom", "中国电信"), "180": ("China Telecom", "中国电信"),
    "181": ("China Telecom", "中国电信"), "189": ("China Telecom", "中国电信"),
    "190": ("China Telecom", "中国电信"), "191": ("China Telecom", "中国电信"),
    "193": ("China Telecom", "中国电信"), "199": ("China Telecom", "中国电信"),
    "192": ("China Broadnet", "中国广电"), "197": ("China Broadnet", "中国广电"),
    "165": ("MVNO", "虚拟运营商"), "167": ("MVNO", "虚拟运营商"),
    "170": ("MVNO", "虚拟运营商"), "162": ("MVNO", "虚拟运营商"),
}

# 假数据字表
SURNAMES = ("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾"
            "肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤")
GIVEN_CHARS = "伟芳娜秀英敏静丽强磊军洋勇艳杰娟涛明超霞平刚建华文博雨欣宇泽轩浩然思远嘉怡子墨紫萱晨曦"
COMPANY_SUFFIX = ["Technology Co., Ltd.", "Network Technology Co., Ltd.", "Information Technology Co., Ltd.",
                  "Trading Co., Ltd.", "Culture & Media Co., Ltd.", "Industrial Co., Ltd.",
                  "E-Commerce Co., Ltd.", "Supply Chain Management Co., Ltd."]
CITY = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", "Chengdu", "Wuhan", "Nanjing",
        "Xi'an", "Chongqing", "Suzhou", "Tianjin", "Changsha", "Zhengzhou", "Qingdao", "Ningbo"]
CITY_DISTRICT = {
    "Beijing": ["Chaoyang", "Haidian", "Dongcheng", "Xicheng", "Fengtai", "Tongzhou"],
    "Shanghai": ["Pudong", "Xuhui", "Jing'an", "Huangpu", "Changning", "Minhang"],
    "Guangzhou": ["Tianhe", "Yuexiu", "Haizhu", "Baiyun", "Panyu", "Liwan"],
    "Shenzhen": ["Nanshan", "Futian", "Luohu", "Bao'an", "Longgang", "Longhua"],
    "Hangzhou": ["Xihu", "Gongshu", "Shangcheng", "Binjiang", "Yuhang", "Xiaoshan"],
    "Chengdu": ["Wuhou", "Jinjiang", "Qingyang", "Jinniu", "Chenghua", "Gaoxin"],
    "Wuhan": ["Wuchang", "Hongshan", "Jianghan", "Qiaokou", "Hanyang", "Jiang'an"],
    "Nanjing": ["Gulou", "Xuanwu", "Qinhuai", "Jianye", "Qixia", "Jiangning"],
    "Xi'an": ["Yanta", "Beilin", "Lianhu", "Weiyang", "Xincheng", "Chang'an"],
    "Chongqing": ["Yuzhong", "Jiangbei", "Shapingba", "Nan'an", "Jiulongpo", "Yubei"],
    "Suzhou": ["Gusu", "Wuzhong", "Xiangcheng", "Huqiu", "Wujiang", "Industrial Park"],
    "Tianjin": ["Heping", "Hexi", "Nankai", "Hedong", "Hebei", "Hongqiao"],
    "Changsha": ["Yuelu", "Furong", "Tianxin", "Kaifu", "Yuhua", "Wangcheng"],
    "Zhengzhou": ["Jinshui", "Zhongyuan", "Erqi", "Guancheng", "Huiji", "Zhengdong"],
    "Qingdao": ["Shinan", "Shibei", "Licang", "Laoshan", "Chengyang", "Huangdao"],
    "Ningbo": ["Haishu", "Jiangbei", "Yinzhou", "Zhenhai", "Beilun", "Fenghua"],
}
ROAD = ["Zhongshan Rd", "Renmin Rd", "Jianshe Ave", "Jiefang Rd", "Keji Rd",
        "Changjiang Rd", "Huanghe Ave", "Wenhua Rd"]

app = FastAPI(
    title="China Data Toolkit API",
    version="1.0.0",
    description=(
        "Validation and PII-masking utilities for **Chinese data**.\n\n"
        "Every endpoint is a pure algorithm — no scraping, no external data sources, no third-party "
        "calls, and **nothing is stored**. Typical response time is under 50 ms.\n\n"
        "### What you get\n\n"
        "| Group | Endpoints |\n"
        "|---|---|\n"
        "| **PII masking** | `/v1/mask` |\n"
        "| **Validation** | `/v1/validate/idcard`, `/v1/validate/uscc`, `/v1/validate/bankcard`, `/v1/validate/phone` |\n"
        "| **Text tools** | `/v1/count`, `/v1/pinyin`, `/v1/fake` |\n\n"
        "### Language\n\n"
        "Responses are in **English** by default. Pass `?lang=zh` to any endpoint to get Chinese "
        "labels instead — useful when the output is shown to Chinese end-users.\n\n"
        "### Privacy\n\n"
        "Request bodies are never persisted or logged. The service holds no database."
    ),
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

LANG_DOC = "Response language: `en` (default) or `zh`"


def _L(lang: str):
    """返回一个取词函数：优先返回指定语言的字符串"""
    zh = str(lang).lower().startswith("zh")

    def pick(en: str, cn: str) -> str:
        return cn if zh else en
    return pick


# ==========================================================================
# 请求模型（描述全部英文 —— 会显示在 RapidAPI 的调用界面上）
# ==========================================================================

class MaskIn(BaseModel):
    text: str = Field(
        ..., description="Text to mask. Phone numbers, ID cards, emails and bank cards are detected "
                         "automatically. Max 20,000 characters.",
        examples=["Customer Zhang Wei, phone 13812345678, ID 11010519491231002X"])
    mask_char: str = Field("*", max_length=1, description="Character used to replace masked characters")
    keep_head: int = Field(3, ge=0, le=10, description="How many leading characters to keep visible")
    keep_tail: int = Field(4, ge=0, le=10, description="How many trailing characters to keep visible")


class TextIn(BaseModel):
    text: str = Field(..., description="Text to analyse", examples=["你好world 123，测试。"])


class PinyinIn(BaseModel):
    text: str = Field(..., description="Chinese text to convert", examples=["中国银行"])
    style: str = Field("plain", description="`plain` = no tones, `tone` = numbered tones, `first` = initials only")
    separator: str = Field(" ", description="String placed between syllables")


class FakeIn(BaseModel):
    kind: str = Field("name", description="`name` / `phone` / `idcard` / `company` / `address` / `all`")
    count: int = Field(5, ge=1, le=100, description="How many records to generate (1–100)")


class IdIn(BaseModel):
    id_number: str = Field(
        ..., description="18-character Chinese resident ID number. The last character may be a digit or `X`.",
        examples=["11010519491231002X"])


class PhoneIn(BaseModel):
    phone: str = Field(..., description="11-digit mainland China mobile number", examples=["13812345678"])


class BankIn(BaseModel):
    card_number: str = Field(..., description="Bank card number, 16–19 digits", examples=["4539148803436467"])


class UsccIn(BaseModel):
    code: str = Field(
        ..., description="18-character Unified Social Credit Code (统一社会信用代码) printed on Chinese "
                         "business licences", examples=["91350100M000100Y43"])


# ==========================================================================
# 工具函数
# ==========================================================================

def _luhn_ok(num: str) -> bool:
    """Luhn 算法，用于银行卡号校验"""
    if not num.isdigit():
        return False
    total, alt = 0, False
    for ch in reversed(num):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def _check_idcard(s: str, lang: str) -> dict:
    p = _L(lang)
    s = s.strip().upper()
    if len(s) != 18:
        return {"valid": False, "reason": p(f"Expected 18 characters, got {len(s)}",
                                            f"长度应为 18 位，当前 {len(s)} 位")}
    if not re.fullmatch(r"\d{17}[\dX]", s):
        return {"valid": False,
                "reason": p("Invalid format: the first 17 characters must be digits and the last must be "
                            "a digit or X",
                            "格式错误：前 17 位必须是数字，最后一位是数字或 X")}
    if s[:2] not in PROVINCE:
        return {"valid": False, "reason": p(f"Unknown province code {s[:2]}", f"省级代码 {s[:2]} 不存在")}
    try:
        birth = datetime.strptime(s[6:14], "%Y%m%d").date()
    except ValueError:
        return {"valid": False, "reason": p("Birth date is not a valid calendar date", "出生日期不合法")}
    if birth > date.today():
        return {"valid": False, "reason": p("Birth date is in the future", "出生日期晚于今天")}
    total = sum(int(s[i]) * ID_WEIGHTS[i] for i in range(17))
    if ID_CHECK[total % 11] != s[17]:
        return {"valid": False,
                "reason": p("Check digit mismatch — the number may have been altered",
                            "校验位错误（号码可能被改过）")}
    en_prov, cn_prov = PROVINCE[s[:2]]
    return {
        "valid": True,
        "reason": p("Check passed", "校验通过"),
        "birth_date": birth.isoformat(),
        "gender": p("male", "男") if int(s[16]) % 2 else p("female", "女"),
        "age": (date.today() - birth).days // 365,
        "province": p(en_prov, cn_prov),
        "masked": s[:6] + "*" * 8 + s[14:],
    }


def _check_uscc(code: str, lang: str) -> dict:
    p = _L(lang)
    code = code.strip().upper()
    if len(code) != 18:
        return {"valid": False, "reason": p(f"Expected 18 characters, got {len(code)}",
                                            f"长度应为 18 位，当前 {len(code)} 位")}
    for ch in code:
        if ch not in USCC_CHARSET:
            return {"valid": False,
                    "reason": p(f"Illegal character '{ch}' — this code never contains I, O, S, V or Z",
                                f"含非法字符「{ch}」（统一社会信用代码不含 I、O、S、V、Z）")}
    total = sum(USCC_CHARSET.index(code[i]) * USCC_WEIGHTS[i] for i in range(17))
    c = 31 - total % 31
    if c == 31:
        c = 0
    if USCC_CHARSET[c] != code[17]:
        return {"valid": False, "reason": p("Check digit mismatch", "校验位错误")}
    return {"valid": True, "reason": p("Check passed", "校验通过"),
            "registration_authority": code[0:2]}


def _mask_text(text: str, mask_char: str, keep_head: int, keep_tail: int, lang: str) -> dict:
    """自动识别 PII 并打码，返回脱敏结果和命中明细"""
    p = _L(lang)
    hits = []

    def _mk(name):
        def f(m):
            v = m.group(0)

            def rep(inner):
                if len(inner) <= keep_head + keep_tail:
                    return mask_char * len(inner)
                return inner[:keep_head] + mask_char * (len(inner) - keep_head - keep_tail) + inner[-keep_tail:]

            if name == "email":
                local, _, domain = v.partition("@")
                masked_local = rep(local)
                hits.append({"type": "email", "original": v, "masked": f"{masked_local}@{domain}"})
                return f"{masked_local}@{domain}"
            out = rep(v)
            hits.append({"type": name, "original": v, "masked": out})
            return out
        return f

    # 顺序有讲究：先长后短，避免身份证被手机号规则先切走
    patterns = [
        ("idcard", re.compile(r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")),
        ("bankcard", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
        ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
        ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ]
    out = text
    for name, pat in patterns:
        out = pat.sub(_mk(name), out)
    return {
        "masked_text": out,
        "hit_count": len(hits),
        "hits": hits,
        "note": p("The bankcard rule matches any run of 16–19 digits, so it can also match order numbers. "
                  "Submit only the field you need masked if you require precision.",
                  "银行卡规则为 16~19 位连续数字，可能误伤订单号；如需精确请只提交待脱敏字段"),
    }


def _count_text(text: str) -> dict:
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = len(re.findall(r"[A-Za-z]+", text))
    digits = len(re.findall(r"\d", text))
    punct = len(re.findall(r"[^\w\s\u4e00-\u9fff]", text))
    spaces = len(re.findall(r"\s", text))
    lines = text.count("\n") + 1 if text else 0
    return {
        "total_chars": len(text),
        "chinese_chars": chinese,
        "english_words": english_words,
        "digits": digits,
        "punctuation": punct,
        "whitespace": spaces,
        "lines": lines,
        "estimated_read_minutes": round((chinese / 400 + english_words / 200), 2) or 0.01,
    }


# ==========================================================================
# 接口
# ==========================================================================

@app.get("/", tags=["Meta"], summary="Service index",
         description="Returns the service name, version and the list of available endpoints. "
                     "Useful as a quick smoke test.")
def root():
    return {
        "name": "China Data Toolkit API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "POST /v1/mask", "POST /v1/count", "POST /v1/pinyin",
            "POST /v1/validate/idcard", "POST /v1/validate/phone",
            "POST /v1/validate/bankcard", "POST /v1/validate/uscc",
            "POST /v1/fake", "GET /health",
        ],
    }


@app.get("/health", tags=["Meta"], summary="Health check",
         description='Returns `{"status": "ok"}` while the service is up. Use this for uptime monitoring.')
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.post("/v1/mask", tags=["PII Masking"],
          summary="Mask phone numbers, ID cards, emails and bank cards",
          description="""Detects and masks **personally identifiable information** inside any text.

Built for three everyday jobs:

- **Log scrubbing** — strip real user data before it reaches your log pipeline
- **Support tooling** — let an agent read a ticket without seeing the customer's phone number
- **Test fixtures** — turn production records into safe sample data

### What it detects

| Type | Pattern |
|---|---|
| `idcard` | 18-character Chinese resident ID (with `X` check digit) |
| `phone` | 11-digit mainland China mobile number |
| `bankcard` | any run of 16–19 digits |
| `email` | standard email address |

Detection runs longest-pattern-first, so an ID number is never swallowed by the phone rule.

### Response

`masked_text` is the cleaned string. `hits` lists exactly what was found and how each value was
rewritten, so you can audit the result before trusting it.

### Example

**Request**

```json
{
  "text": "Customer Zhang Wei, phone 13812345678, ID 11010519491231002X, email zhang.wei@corp.com"
}
```

**Response**

```json
{
  "masked_text": "Customer Zhang Wei, phone 138****5678, ID 110***********002X, email zha**.wei@corp.com",
  "hit_count": 3,
  "hits": [
    { "type": "idcard", "original": "11010519491231002X", "masked": "110***********002X" },
    { "type": "phone",  "original": "13812345678",        "masked": "138****5678" },
    { "type": "email",  "original": "zhang.wei@corp.com", "masked": "zha**.wei@corp.com" }
  ]
}
```

### Notes

- The `bankcard` rule matches **any** run of 16–19 digits, so it may also catch order numbers. If you
  need precision, submit only the field you want masked.
- Nothing is stored or logged. The service is stateless by design — that is the whole point of a
  masking API.
""")
def mask(payload: MaskIn, lang: str = Query("en", description=LANG_DOC)):
    if not payload.text.strip():
        raise HTTPException(400, "text must not be empty")
    if len(payload.text) > 20000:
        raise HTTPException(413, "text is limited to 20,000 characters per request")
    return _mask_text(payload.text, payload.mask_char, payload.keep_head, payload.keep_tail, lang)


@app.post("/v1/validate/idcard", tags=["Validation"],
          summary="Validate a Chinese resident ID number",
          description="""Validates an 18-character Chinese resident ID (居民身份证号码) and returns the
information encoded inside it.

### Checks performed

1. Length is exactly 18 characters
2. The first 17 characters are digits; the last is a digit or `X`
3. The province code (first 2 digits) exists
4. The birth date is a real calendar date and not in the future
5. The **check digit** matches the weighted modulo-11 algorithm

### What you get back

Besides `valid`, a passing number returns the `birth_date`, `gender`, `age` and `province` encoded in
the number — no second lookup needed.

### Example

**Request**

```json
{ "id_number": "11010519491231002X" }
```

**Response**

```json
{
  "valid": true,
  "reason": "Check passed",
  "birth_date": "1949-12-31",
  "gender": "female",
  "age": 76,
  "province": "Beijing",
  "masked": "110105********002X"
}
```

**A rejected number**

```json
{ "valid": false, "reason": "Check digit mismatch — the number may have been altered" }
```

### Notes

- Lowercase `x` is accepted and normalised to uppercase.
- This validates the number's **structure only**. It does not confirm that the person exists, nor that
  the name matches the number.
""")
def validate_idcard(payload: IdIn, lang: str = Query("en", description=LANG_DOC)):
    return _check_idcard(payload.id_number, lang)


@app.post("/v1/validate/uscc", tags=["Validation"],
          summary="Validate a Unified Social Credit Code",
          description="""Validates the 18-character **Unified Social Credit Code** (统一社会信用代码) printed on
every Chinese business licence — the Chinese equivalent of a company registration number.

Implemented per **GB 32100-2015**, including the modulo-31 check digit.

### Example

**Request**

```json
{ "code": "91350100M000100Y43" }
```

**Response**

```json
{ "valid": true, "reason": "Check passed", "registration_authority": "91" }
```

### Notes

- The character set deliberately excludes the letters **I, O, S, V and Z** to avoid confusion with
  digits. A code containing any of them is rejected immediately.
- Input is case-insensitive.

### Typical use

Supplier and merchant onboarding forms, KYC flows, invoice reconciliation.
""")
def validate_uscc(payload: UsccIn, lang: str = Query("en", description=LANG_DOC)):
    return _check_uscc(payload.code, lang)


@app.post("/v1/validate/bankcard", tags=["Validation"],
          summary="Validate a bank card number (Luhn)",
          description="""Checks a bank card number with the **Luhn algorithm** (mod-10) and returns a masked copy.

### Example

**Request**

```json
{ "card_number": "4539148803436467" }
```

**Response**

```json
{ "valid": true, "reason": "Luhn check passed", "length": 16, "masked": "4539********6467" }
```

### Notes

- Accepts 12–19 digits; spaces are ignored.
- Luhn catches typos and transposed digits, but it is **not** proof that a card exists or is active.
  Roughly 1 in 10 random digit strings passes Luhn, so always combine this with your payment
  provider's own verification.
- No network lookup is performed and nothing is stored.
""")
def validate_bankcard(payload: BankIn, lang: str = Query("en", description=LANG_DOC)):
    p = _L(lang)
    n = re.sub(r"\s", "", payload.card_number)
    if not n.isdigit():
        return {"valid": False, "reason": p("Card number must contain digits only", "卡号必须全是数字")}
    if not 12 <= len(n) <= 19:
        return {"valid": False, "reason": p(f"Unexpected length ({len(n)} digits)", f"长度异常（{len(n)} 位）")}
    ok = _luhn_ok(n)
    return {
        "valid": ok,
        "reason": p("Luhn check passed", "Luhn 校验通过") if ok
                  else p("Luhn check failed — the number is probably mistyped", "Luhn 校验失败，卡号可能有误"),
        "length": len(n),
        "masked": n[:4] + "*" * (len(n) - 8) + n[-4:],
    }


@app.post("/v1/validate/phone", tags=["Validation"],
          summary="Validate a Chinese mobile number",
          description="""Validates an 11-digit mainland China mobile number and identifies the **carrier**
from the allocated number prefix.

### Example

**Request**

```json
{ "phone": "13812345678" }
```

**Response**

```json
{ "valid": true, "reason": "Check passed", "carrier": "China Mobile", "masked": "138****5678" }
```

Carrier values: `China Mobile`, `China Unicom`, `China Telecom`, `China Broadnet`, `MVNO`
(virtual operators), or `Unknown prefix`.

### Notes

- Spaces and hyphens are ignored.
- Prefix data follows the public MIIT allocation list. **Number portability means the carrier shown is
  the original allocation, not necessarily the current network** — treat it as a hint, not a fact.
""")
def validate_phone(payload: PhoneIn, lang: str = Query("en", description=LANG_DOC)):
    p = _L(lang)
    ph = re.sub(r"[\s-]", "", payload.phone)
    if not re.fullmatch(r"1[3-9]\d{9}", ph):
        return {"valid": False,
                "reason": p("Not a valid mainland China mobile number", "不是合法的中国大陆手机号")}
    entry = PHONE_PREFIX.get(ph[:3])
    return {
        "valid": True,
        "reason": p("Check passed", "校验通过"),
        "carrier": p(*entry) if entry else p("Unknown prefix", "未知号段"),
        "masked": ph[:3] + "****" + ph[7:],
    }


@app.post("/v1/count", tags=["Text Tools"],
          summary="Count Chinese and English text correctly",
          description="""Counts text the way Chinese and English actually work: **Chinese by character,
English by word**.

Most generic counters get this wrong — they either report a 3-character Chinese phrase as 3 "words",
or split Chinese text on whitespace and return 1.

### Example

**Request**

```json
{ "text": "你好world 123，测试。" }
```

**Response**

```json
{
  "total_chars": 15,
  "chinese_chars": 4,
  "english_words": 1,
  "digits": 3,
  "punctuation": 2,
  "whitespace": 1,
  "lines": 1,
  "estimated_read_minutes": 0.01
}
```

### Typical use

Pricing translation work, enforcing CMS character limits, estimating reading time, validating
user-submitted content.
""")
def count(payload: TextIn):
    return _count_text(payload.text)


@app.post("/v1/pinyin", tags=["Text Tools"],
          summary="Convert Chinese characters to pinyin",
          description="""Converts Chinese text to **pinyin** in one of three styles.

### Styles

| `style` | Output | Use for |
|---|---|---|
| `plain` | `zhong guo yin hang` | Display, URL slugs |
| `tone` | `zhong1 guo2 yin2 hang2` | Pronunciation, language learning |
| `first` | `z g y h` | Initials, sorting, search |

### Example

**Request**

```json
{ "text": "中国银行", "style": "plain" }
```

**Response**

```json
{
  "pinyin": "zhong guo yin hang",
  "syllables": ["zhong", "guo", "yin", "hang"],
  "count": 4
}
```

### Notes

- Non-Chinese characters (digits, punctuation, Latin letters) are passed through unchanged.
- Characters with multiple readings use the most common pronunciation. This is reliable for real
  words; isolated rare characters may occasionally be read differently than intended.
""")
def pinyin(payload: PinyinIn):
    try:
        from pypinyin import Style, lazy_pinyin
    except ImportError:
        raise HTTPException(500, "Server is missing the pypinyin dependency")

    style_map = {"plain": Style.NORMAL, "tone": Style.TONE3, "first": Style.FIRST_LETTER}
    if payload.style not in style_map:
        raise HTTPException(400, f"style must be one of {list(style_map)}")
    parts = lazy_pinyin(payload.text, style=style_map[payload.style], errors="default")
    return {"pinyin": payload.separator.join(parts), "syllables": parts, "count": len(parts)}


@app.post("/v1/fake", tags=["Text Tools"],
          summary="Generate realistic Chinese test data",
          description="""Generates **structurally valid Chinese test data** — names, mobile numbers, ID
numbers, company names and addresses.

### Why it is useful

The ID numbers returned here **pass the same checksum that the validation endpoints enforce**, so you
can seed a test database and immediately exercise your own validation logic. Addresses use real
city/district pairings rather than random combinations.

### Example

**Request**

```json
{ "kind": "all", "count": 1 }
```

**Response**

```json
{
  "kind": "all",
  "count": 1,
  "data": [
    {
      "name": "谭远",
      "phone": "13928475610",
      "idcard": "440305198703124417",
      "company": "Shenzhen Wei Technology Co., Ltd.",
      "address": "Shenzhen Nanshan Keji Rd 412"
    }
  ]
}
```

### Notes

- **This is synthetic data. It does not correspond to any real person.** Never use it to impersonate
  anyone or to bypass identity verification.
- `kind` accepts `name`, `phone`, `idcard`, `company`, `address`, or `all`.
- Maximum 100 records per request.
""")
def fake(payload: FakeIn):
    if payload.kind not in ("name", "phone", "idcard", "company", "address", "all"):
        raise HTTPException(400, "kind must be one of: name, phone, idcard, company, address, all")
    rnd = random.Random()
    out: List[dict] = []

    def one_name():
        return rnd.choice(SURNAMES) + "".join(rnd.choice(GIVEN_CHARS) for _ in range(rnd.choice([1, 1, 2])))

    def one_phone():
        return "1" + rnd.choice("35789") + "".join(rnd.choice(string.digits) for _ in range(9))

    def one_idcard():
        # 6 位地区码 + 8 位生日 + 3 位顺序码 = 17 位，再加 1 位校验位
        prov = rnd.choice([k for k in PROVINCE if k not in ("71", "81", "82", "91")])
        region = f"{prov}{rnd.randint(1, 99):02d}{rnd.randint(1, 99):02d}"
        y = rnd.randint(1960, 2005)
        m = rnd.randint(1, 12)
        d = rnd.randint(1, 28)
        seq = f"{rnd.randint(0, 999):03d}"
        body = f"{region}{y}{m:02d}{d:02d}{seq}"
        total = sum(int(body[i]) * ID_WEIGHTS[i] for i in range(17))
        return body + ID_CHECK[total % 11]

    def one_company():
        return rnd.choice(CITY) + one_name()[:2] + " " + rnd.choice(COMPANY_SUFFIX)

    def one_address():
        c = rnd.choice(CITY)
        return f"{c} {rnd.choice(CITY_DISTRICT[c])} {rnd.choice(ROAD)} {rnd.randint(1, 999)}"

    for _ in range(payload.count):
        if payload.kind == "all":
            out.append({
                "name": one_name(), "phone": one_phone(), "idcard": one_idcard(),
                "company": one_company(), "address": one_address(),
            })
        else:
            out.append({"value": {
                "name": one_name, "phone": one_phone, "idcard": one_idcard,
                "company": one_company, "address": one_address,
            }[payload.kind]()})
    return {"kind": payload.kind, "count": len(out), "data": out}


# ==========================================================================
# OpenAPI 3.0.2 降级转换
# --------------------------------------------------------------------------
# 为什么需要这个：
#   新版 FastAPI 默认输出 OpenAPI 3.1.0，但 RapidAPI 目前只接受到 3.0.2。
#   直接上传 3.1 规范会被拒绝。这里在服务端现转一份 3.0.2 出来。
# ==========================================================================

def to_openapi_30(spec: dict) -> dict:
    """把 OpenAPI 3.1 规范降级成 3.0.2（RapidAPI 可接受）"""
    s = copy.deepcopy(spec)
    s["openapi"] = "3.0.2"
    s.pop("webhooks", None)          # 3.1 专有
    s.pop("jsonSchemaDialect", None)  # 3.1 专有

    def walk(node):
        if isinstance(node, dict):
            # examples: [x] -> example: x   （3.0 用单数）
            if isinstance(node.get("examples"), list) and node["examples"]:
                node.setdefault("example", node["examples"][0])
                del node["examples"]

            # const -> enum
            if "const" in node:
                node.setdefault("enum", [node.pop("const")])

            # prefixItems -> items（3.0 不支持元组式数组）
            if "prefixItems" in node:
                node["items"] = node.pop("prefixItems")[0]

            # anyOf: [{type: X}, {type: "null"}] -> type: X, nullable: true
            if isinstance(node.get("anyOf"), list):
                subs = [x for x in node["anyOf"] if isinstance(x, dict)]
                nulls = [x for x in subs if x.get("type") == "null"]
                real = [x for x in subs if x.get("type") != "null"]
                if nulls and len(real) == 1 and len(subs) == len(node["anyOf"]):
                    merged = real[0]
                    rest = {k: v for k, v in node.items() if k != "anyOf"}
                    node.clear()
                    node.update(rest)
                    node.update(merged)
                    node["nullable"] = True
                elif nulls:
                    node["anyOf"] = real
                    node["nullable"] = True

            # type: ["string","null"] -> type: string, nullable: true  （3.1 写法）
            t = node.get("type")
            if isinstance(t, list):
                if "null" in t:
                    rest_t = [x for x in t if x != "null"]
                    node["type"] = rest_t[0] if len(rest_t) == 1 else rest_t
                    node["nullable"] = True
                else:
                    node["type"] = t[0] if len(t) == 1 else t

            for v in list(node.values()):
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(s)
    return s


def custom_openapi():
    """在规范里补上 servers 字段"""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title, version=app.version,
        description=app.description, routes=app.routes,
    )
    schema["servers"] = [{"url": BASE_URL, "description": "Production"}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.get("/openapi-3.0.json", include_in_schema=False)
def openapi_30_json():
    """给 RapidAPI 用的 OpenAPI 3.0.2 规范（直接下载这个文件上传）"""
    return JSONResponse(to_openapi_30(app.openapi()))


@app.get("/download/openapi-3.0.2.json", include_in_schema=False)
def download_openapi_30():
    """真·下载：点这个链接会直接下载文件，而不是在浏览器里显示"""
    spec = to_openapi_30(app.openapi())
    body = json.dumps(spec, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="openapi-3.0.2.json"'},
    )
