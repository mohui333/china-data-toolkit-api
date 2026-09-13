# -*- coding: utf-8 -*-
"""
China Data Toolkit API —— 中国数据校验与合规脱敏 API

设计原则（重要）：
    只用纯算法 + 极小内置字表，不抓取任何外部数据、不依赖任何在线服务。
    好处：不会因为上游改版而失效，维护成本接近 0。
    这是它能在 RapidAPI 上"挂上去就基本不用管"的根本原因。

启动本地调试：
    uvicorn main:app --reload --port 8000
然后打开 http://127.0.0.1:8000/docs 就能看到交互式文档。
"""

import copy
import json
import random
import re
import string
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

# ==========================================================================
# 常量与内置数据（都很小，且永不失效）
# ==========================================================================

# 身份证前 2 位的省级代码
PROVINCE = {
    "11": "北京市", "12": "天津市", "13": "河北省", "14": "山西省", "15": "内蒙古自治区",
    "21": "辽宁省", "22": "吉林省", "23": "黑龙江省",
    "31": "上海市", "32": "江苏省", "33": "浙江省", "34": "安徽省", "35": "福建省",
    "36": "江西省", "37": "山东省",
    "41": "河南省", "42": "湖北省", "43": "湖南省", "44": "广东省", "45": "广西壮族自治区",
    "46": "海南省",
    "50": "重庆市", "51": "四川省", "52": "贵州省", "53": "云南省", "54": "西藏自治区",
    "61": "陕西省", "62": "甘肃省", "63": "青海省", "64": "宁夏回族自治区", "65": "新疆维吾尔自治区",
    "71": "台湾省", "81": "香港特别行政区", "82": "澳门特别行政区",
    "91": "国外",
}

# 身份证校验位
ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
ID_CHECK = "10X98765432"

# 统一社会信用代码（GB 32100-2015）
USCC_CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"      # 31 个，去掉 I O S V Z
USCC_WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]

# 手机号段（工信部公开号段，前缀 3 位）
PHONE_PREFIX = {
    "134": "中国移动", "135": "中国移动", "136": "中国移动", "137": "中国移动",
    "138": "中国移动", "139": "中国移动", "147": "中国移动", "150": "中国移动",
    "151": "中国移动", "152": "中国移动", "157": "中国移动", "158": "中国移动",
    "159": "中国移动", "172": "中国移动", "178": "中国移动", "182": "中国移动",
    "183": "中国移动", "184": "中国移动", "187": "中国移动", "188": "中国移动",
    "198": "中国移动",
    "130": "中国联通", "131": "中国联通", "132": "中国联通", "145": "中国联通",
    "155": "中国联通", "156": "中国联通", "166": "中国联通", "171": "中国联通",
    "175": "中国联通", "176": "中国联通", "185": "中国联通", "186": "中国联通",
    "133": "中国电信", "149": "中国电信", "153": "中国电信", "173": "中国电信",
    "177": "中国电信", "180": "中国电信", "181": "中国电信", "189": "中国电信",
    "190": "中国电信", "191": "中国电信", "193": "中国电信", "199": "中国电信",
    "192": "中国广电", "197": "中国广电",
    "165": "虚拟运营商", "167": "虚拟运营商", "170": "虚拟运营商", "162": "虚拟运营商",
}

SURNAMES = ("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾"
            "肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤")
GIVEN_CHARS = "伟芳娜秀英敏静丽强磊军洋勇艳杰娟涛明超秀霞平刚桂英建华文博雨欣宇泽轩浩然思远嘉怡子墨紫萱晨曦"
COMPANY_SUFFIX = ["科技有限公司", "网络科技有限公司", "信息技术有限公司", "贸易有限公司",
                  "文化传媒有限公司", "实业有限公司", "电子商务有限公司", "供应链管理有限公司"]
CITY = ["北京市", "上海市", "广州市", "深圳市", "杭州市", "成都市", "武汉市", "南京市",
        "西安市", "重庆市", "苏州市", "天津市", "长沙市", "郑州市", "青岛市", "宁波市"]
# 市 → 该市真实的区（避免生成「苏州市江干区」这种地理错乱地址）
CITY_DISTRICT = {
    "北京市": ["朝阳区", "海淀区", "东城区", "西城区", "丰台区", "通州区"],
    "上海市": ["浦东新区", "徐汇区", "静安区", "黄浦区", "长宁区", "闵行区"],
    "广州市": ["天河区", "越秀区", "海珠区", "白云区", "番禺区", "荔湾区"],
    "深圳市": ["南山区", "福田区", "罗湖区", "宝安区", "龙岗区", "龙华区"],
    "杭州市": ["西湖区", "拱墅区", "上城区", "滨江区", "余杭区", "萧山区"],
    "成都市": ["武侯区", "锦江区", "青羊区", "金牛区", "成华区", "高新区"],
    "武汉市": ["武昌区", "洪山区", "江汉区", "硚口区", "汉阳区", "江岸区"],
    "南京市": ["鼓楼区", "玄武区", "秦淮区", "建邺区", "栖霞区", "江宁区"],
    "西安市": ["雁塔区", "碑林区", "莲湖区", "未央区", "新城区", "长安区"],
    "重庆市": ["渝中区", "江北区", "沙坪坝区", "南岸区", "九龙坡区", "渝北区"],
    "苏州市": ["姑苏区", "吴中区", "相城区", "虎丘区", "吴江区", "工业园区"],
    "天津市": ["和平区", "河西区", "南开区", "河东区", "河北区", "红桥区"],
    "长沙市": ["岳麓区", "芙蓉区", "天心区", "开福区", "雨花区", "望城区"],
    "郑州市": ["金水区", "中原区", "二七区", "管城区", "惠济区", "郑东新区"],
    "青岛市": ["市南区", "市北区", "李沧区", "崂山区", "城阳区", "黄岛区"],
    "宁波市": ["海曙区", "江北区", "鄞州区", "镇海区", "北仑区", "奉化区"],
}
ROAD = ["中山路", "人民路", "建设大道", "解放路", "科技路", "长江路", "黄河大道", "文化路"]

app = FastAPI(
    title="China Data Toolkit API",
    version="1.0.0",
    description=(
        "中国数据校验与合规脱敏 API。\n\n"
        "- **PII 脱敏**：自动识别并打码手机号 / 身份证 / 邮箱 / 银行卡，用于日志、客服记录、测试环境\n"
        "- **证件校验**：身份证、统一社会信用代码、银行卡（Luhn）、手机号（含运营商）\n"
        "- **文本工具**：中英文字数统计、拼音转换、中文假数据生成\n\n"
        "全部为纯算法实现，不采集、不存储、不外传任何请求内容。"
    ),
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ==========================================================================
# 模型
# ==========================================================================

class TextIn(BaseModel):
    text: str = Field(..., description="待处理文本", examples=["联系我 13812345678 或 a@b.com"])


class MaskIn(BaseModel):
    text: str = Field(..., description="需要脱敏的文本")
    mask_char: str = Field("*", max_length=1, description="打码用的字符，默认 *")
    keep_head: int = Field(3, ge=0, le=10, description="保留前几位（手机/银行卡）")
    keep_tail: int = Field(4, ge=0, le=10, description="保留后几位")


class PinyinIn(BaseModel):
    text: str = Field(..., description="中文文本", examples=["中国银行"])
    style: str = Field("plain", description="plain=不带声调 / tone=带声调数字 / first=首字母")
    separator: str = Field(" ", description="拼音之间的分隔符")


class FakeIn(BaseModel):
    kind: str = Field("name", description="name / phone / idcard / company / address / all")
    count: int = Field(5, ge=1, le=100, description="生成数量，1~100")


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


def _check_idcard(s: str) -> dict:
    s = s.strip().upper()
    if len(s) != 18:
        return {"valid": False, "reason": f"长度应为 18 位，当前 {len(s)} 位"}
    if not re.fullmatch(r"\d{17}[\dX]", s):
        return {"valid": False, "reason": "格式错误：前 17 位必须是数字，最后一位是数字或 X"}
    if s[:2] not in PROVINCE:
        return {"valid": False, "reason": f"省级代码 {s[:2]} 不存在"}
    try:
        birth = datetime.strptime(s[6:14], "%Y%m%d").date()
    except ValueError:
        return {"valid": False, "reason": "出生日期不合法"}
    if birth > date.today():
        return {"valid": False, "reason": "出生日期晚于今天"}
    total = sum(int(s[i]) * ID_WEIGHTS[i] for i in range(17))
    if ID_CHECK[total % 11] != s[17]:
        return {"valid": False, "reason": "校验位错误（号码可能被改过）"}
    return {
        "valid": True,
        "reason": "校验通过",
        "birth_date": birth.isoformat(),
        "gender": "男" if int(s[16]) % 2 else "女",
        "age": (date.today() - birth).days // 365,
        "province": PROVINCE.get(s[:2], "未知"),
        "masked": s[:6] + "*" * 8 + s[14:],
    }


def _check_uscc(code: str) -> dict:
    code = code.strip().upper()
    if len(code) != 18:
        return {"valid": False, "reason": f"长度应为 18 位，当前 {len(code)} 位"}
    for ch in code:
        if ch not in USCC_CHARSET:
            return {"valid": False, "reason": f"含非法字符「{ch}」（统一社会信用代码不含 I、O、S、V、Z）"}
    total = sum(USCC_CHARSET.index(code[i]) * USCC_WEIGHTS[i] for i in range(17))
    c = 31 - total % 31
    if c == 31:
        c = 0
    if USCC_CHARSET[c] != code[17]:
        return {"valid": False, "reason": "校验位错误"}
    return {"valid": True, "reason": "校验通过", "registration_authority": code[0:2]}


def _mask_text(text: str, mask_char: str, keep_head: int, keep_tail: int) -> dict:
    """自动识别 PII 并打码，返回脱敏结果和命中明细"""
    hits = []

    def _mk(name):
        def f(m):
            v = m.group(0)

            def rep(inner):
                if len(inner) <= keep_head + keep_tail:
                    return mask_char * len(inner)
                return inner[:keep_head] + mask_char * (len(inner) - keep_head - keep_tail) + inner[-keep_tail:]
            # 邮箱按 @ 前部分整体处理，其余按整体处理
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
        "note": "银行卡规则为 16~19 位连续数字，可能误伤订单号；如需精确请只提交待脱敏字段",
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

@app.get("/", tags=["基础"])
def root():
    """服务自述"""
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


@app.get("/health", tags=["基础"])
def health():
    """健康检查（RapidAPI 会调用）"""
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.post("/v1/mask", tags=["脱敏"])
def mask(payload: MaskIn):
    """PII 自动脱敏：手机号、身份证、邮箱、银行卡自动打码"""
    if not payload.text.strip():
        raise HTTPException(400, "text 不能为空")
    if len(payload.text) > 20000:
        raise HTTPException(413, "单次最多 20000 字符")
    return _mask_text(payload.text, payload.mask_char, payload.keep_head, payload.keep_tail)


@app.post("/v1/count", tags=["文本"])
def count(payload: TextIn):
    """中英文字数统计（中文按字、英文按词）"""
    return _count_text(payload.text)


class IdIn(BaseModel):
    id_number: str = Field(..., description="18 位身份证号", examples=["11010519491231002X"])


class PhoneIn(BaseModel):
    phone: str = Field(..., description="11 位手机号", examples=["13812345678"])


class BankIn(BaseModel):
    card_number: str = Field(..., description="16~19 位银行卡号", examples=["6222020200112233445"])


class UsccIn(BaseModel):
    code: str = Field(..., description="18 位统一社会信用代码", examples=["91350100M000100Y43"])


@app.post("/v1/validate/idcard", tags=["校验"])
def validate_idcard(payload: IdIn):
    """身份证校验：合法性 + 出生日期 + 性别 + 年龄 + 归属省"""
    return _check_idcard(payload.id_number)


@app.post("/v1/validate/phone", tags=["校验"])
def validate_phone(payload: PhoneIn):
    """手机号校验 + 运营商归属"""
    p = re.sub(r"[\s-]", "", payload.phone)
    if not re.fullmatch(r"1[3-9]\d{9}", p):
        return {"valid": False, "reason": "不是合法的中国大陆手机号"}
    carrier = PHONE_PREFIX.get(p[:3])
    return {
        "valid": True,
        "reason": "校验通过",
        "carrier": carrier or "未知号段",
        "masked": p[:3] + "****" + p[7:],
    }


@app.post("/v1/validate/bankcard", tags=["校验"])
def validate_bankcard(payload: BankIn):
    """银行卡号 Luhn 校验"""
    n = re.sub(r"\s", "", payload.card_number)
    if not n.isdigit():
        return {"valid": False, "reason": "卡号必须全是数字"}
    if not 12 <= len(n) <= 19:
        return {"valid": False, "reason": f"长度异常（{len(n)} 位）"}
    ok = _luhn_ok(n)
    return {
        "valid": ok,
        "reason": "Luhn 校验通过" if ok else "Luhn 校验失败，卡号可能有误",
        "length": len(n),
        "masked": n[:4] + "*" * (len(n) - 8) + n[-4:],
    }


@app.post("/v1/validate/uscc", tags=["校验"])
def validate_uscc(payload: UsccIn):
    """统一社会信用代码校验（GB 32100-2015），营业执照上的 18 位代码"""
    return _check_uscc(payload.code)


@app.post("/v1/pinyin", tags=["文本"])
def pinyin(payload: PinyinIn):
    """汉字转拼音：支持不带声调 / 数字声调 / 首字母"""
    try:
        from pypinyin import Style, lazy_pinyin
    except ImportError:
        raise HTTPException(500, "服务端缺少 pypinyin 依赖")

    style_map = {"plain": Style.NORMAL, "tone": Style.TONE3, "first": Style.FIRST_LETTER}
    if payload.style not in style_map:
        raise HTTPException(400, f"style 只能是 {list(style_map)}")
    parts = lazy_pinyin(payload.text, style=style_map[payload.style], errors="default")
    return {
        "pinyin": payload.separator.join(parts),
        "syllables": parts,
        "count": len(parts),
    }


@app.post("/v1/fake", tags=["假数据"])
def fake(payload: FakeIn):
    """生成中文测试假数据（姓名/手机/身份证/公司/地址），用于压测和演示"""
    if payload.kind not in ("name", "phone", "idcard", "company", "address", "all"):
        raise HTTPException(400, "kind 取值：name/phone/idcard/company/address/all")
    rnd = random.Random()
    out: List[dict] = []

    def one_name():
        return rnd.choice(SURNAMES) + "".join(rnd.choice(GIVEN_CHARS) for _ in range(rnd.choice([1, 1, 2])))

    def one_phone():
        return "1" + rnd.choice("35789") + "".join(rnd.choice(string.digits) for _ in range(9))

    def one_idcard():
        # 6 位地区码 + 8 位生日 + 3 位顺序码 = 17 位，再加 1 位校验位
        prov = rnd.choice(list(PROVINCE.keys())[:31])
        region = f"{prov}{rnd.randint(1, 99):02d}{rnd.randint(1, 99):02d}"
        y = rnd.randint(1960, 2005)
        m = rnd.randint(1, 12)
        d = rnd.randint(1, 28)
        seq = f"{rnd.randint(0, 999):03d}"
        body = f"{region}{y}{m:02d}{d:02d}{seq}"
        total = sum(int(body[i]) * ID_WEIGHTS[i] for i in range(17))
        return body + ID_CHECK[total % 11]

    def one_company():
        return rnd.choice(CITY) + one_name()[:2] + rnd.choice(COMPANY_SUFFIX)

    def one_address():
        c = rnd.choice(CITY)
        return f"{c}{rnd.choice(CITY_DISTRICT[c])}{rnd.choice(ROAD)}{rnd.randint(1, 999)}号"

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
