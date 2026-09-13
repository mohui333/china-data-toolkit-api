#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China Data Toolkit API 的自动化测试
运行：python3 test_api.py
所有断言失败会以非 0 退出码结束。
"""

import sys
import warnings

warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient   # noqa: E402

import main                                  # noqa: E402

c = TestClient(main.app)
passed, failed = 0, []


def check(name, cond, detail=""):
    global passed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed.append(name)
        print(f"  ✗ {name}  {detail}")


print("【身份证校验 — 英文默认】")
r = c.post("/v1/validate/idcard", json={"id_number": "11010519491231002X"}).json()
check("标准测试号判为合法", r["valid"] is True)
check("解析出生日期", r["birth_date"] == "1949-12-31")
check("解析性别为英文", r["gender"] == "female", r["gender"])
check("解析省份为英文", r["province"] == "Beijing", r["province"])
r = c.post("/v1/validate/idcard", json={"id_number": "110105194912310021"}).json()
check("校验位错误被拒", r["valid"] is False and "Check digit" in r["reason"], r["reason"])
r = c.post("/v1/validate/idcard", json={"id_number": "110105209912310021"}).json()
check("未来生日被拒", r["valid"] is False and "future" in r["reason"], r["reason"])
check("小写 x 也接受", c.post("/v1/validate/idcard", json={"id_number": "11010519491231002x"}).json()["valid"])
check("长度不足被拒", c.post("/v1/validate/idcard", json={"id_number": "1101051949123100"}).json()["valid"] is False)

print("【身份证校验 — lang=zh 切回中文】")
r = c.post("/v1/validate/idcard?lang=zh", json={"id_number": "11010519491231002X"}).json()
check("性别中文", r["gender"] == "女", r["gender"])
check("省份中文", r["province"] == "北京市", r["province"])
check("reason 中文", r["reason"] == "校验通过", r["reason"])
r = c.post("/v1/validate/idcard?lang=zh", json={"id_number": "110105194912310021"}).json()
check("拒绝理由中文", "校验位" in r["reason"], r["reason"])

print("【统一社会信用代码】")
check("标准样例判为合法", c.post("/v1/validate/uscc", json={"code": "91350100M000100Y43"}).json()["valid"])
check("改一位后被拒", c.post("/v1/validate/uscc", json={"code": "91350100M000100Y44"}).json()["valid"] is False)
check("含非法字符 I 被拒", c.post("/v1/validate/uscc", json={"code": "91350100M000100Y4I"}).json()["valid"] is False)

print("【Luhn 银行卡校验 — 标准测试向量】")
check("4539148803436467 合法", c.post("/v1/validate/bankcard", json={"card_number": "4539148803436467"}).json()["valid"])
check("4539148803436468 非法", c.post("/v1/validate/bankcard", json={"card_number": "4539148803436468"}).json()["valid"] is False)
check("含字母被拒", c.post("/v1/validate/bankcard", json={"card_number": "453914880343646a"}).json()["valid"] is False)

print("【手机号】")
r = c.post("/v1/validate/phone", json={"phone": "13812345678"}).json()
check("合法号 + 英文运营商", r["valid"] is True and r["carrier"] == "China Mobile", r.get("carrier"))
check("10 位被拒", c.post("/v1/validate/phone", json={"phone": "1381234567"}).json()["valid"] is False)
check("首位非 1 被拒", c.post("/v1/validate/phone", json={"phone": "23812345678"}).json()["valid"] is False)
r = c.post("/v1/validate/phone?lang=zh", json={"phone": "13812345678"}).json()
check("lang=zh 运营商中文", r["carrier"] == "中国移动", r.get("carrier"))

print("【PII 脱敏】")
t = "手机 13812345678，身份证 11010519491231002X，邮箱 zhang.wei@corp.com，卡号 6222020200112233445"
r = c.post("/v1/mask", json={"text": t}).json()
m = r["masked_text"]
check("手机号已打码", "13812345678" not in m and "138****5678" in m)
check("身份证已打码", "11010519491231002X" not in m)
check("邮箱本地部分已打码", "zhang.wei@" not in m and "@corp.com" in m)
check("银行卡已打码", "6222020200112233445" not in m)
check("命中数=4", r["hit_count"] == 4, f"实际 {r['hit_count']}")
check("note 为英文", "bankcard rule" in r["note"], r["note"][:40])
r = c.post("/v1/mask?lang=zh", json={"text": t}).json()
check("lang=zh 的 note 为中文", "银行卡规则" in r["note"], r["note"][:40])
r = c.post("/v1/mask", json={"text": "订单号 12345，金额 99.9 元，日期 2026-09-13"}).json()
check("普通数字不误伤", r["hit_count"] == 0 and "12345" in r["masked_text"])
check("空文本返回 400", c.post("/v1/mask", json={"text": "   "}).status_code == 400)
check("超长文本返回 413", c.post("/v1/mask", json={"text": "a" * 20001}).status_code == 413)

print("【字数统计】")
r = c.post("/v1/count", json={"text": "你好world 123，测试。"}).json()
check("总字符=15", r["total_chars"] == 15, str(r["total_chars"]))
check("中文=4", r["chinese_chars"] == 4)
check("英文词=1", r["english_words"] == 1)
check("数字=3", r["digits"] == 3)

print("【拼音】")
check("不带声调", c.post("/v1/pinyin", json={"text": "中国银行", "style": "plain"}).json()["pinyin"] == "zhong guo yin hang")
check("首字母", c.post("/v1/pinyin", json={"text": "中国银行", "style": "first"}).json()["pinyin"] == "z g y h")
check("非法 style 返回 400", c.post("/v1/pinyin", json={"text": "中", "style": "zzz"}).status_code == 400)

print("【假数据】")
rows = c.post("/v1/fake", json={"kind": "all", "count": 5}).json()["data"]
check("生成 5 条", len(rows) == 5)
all_ok = True
for row in rows:
    if not c.post("/v1/validate/idcard", json={"id_number": row["idcard"]}).json()["valid"]:
        all_ok = False
check("生成的身份证全部自校验通过", all_ok)
geo_ok = all(
    any(row["address"].startswith(city) and dist in row["address"]
        for city, ds in main.CITY_DISTRICT.items() for dist in ds)
    for row in rows
)
check("地址市/区地理一致", geo_ok)
check("count=0 返回 422", c.post("/v1/fake", json={"kind": "name", "count": 0}).status_code == 422)
check("count=101 返回 422", c.post("/v1/fake", json={"kind": "name", "count": 101}).status_code == 422)

print("【基础】")
check("健康检查", c.get("/health").json()["status"] == "ok")
check("根路径可访问", c.get("/").status_code == 200)
check("OpenAPI 文档可生成", c.get("/openapi.json").status_code == 200)

print(f"\n{'=' * 46}")
print(f"通过 {passed} 项，失败 {len(failed)} 项")
if failed:
    print("失败项：" + "、".join(failed))
    sys.exit(1)
print("全部通过 ✓")
