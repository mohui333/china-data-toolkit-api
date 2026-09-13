# RapidAPI 上架资料（全部复制粘贴即用）

> 这是给 RapidAPI 后台填的。你只需要：部署 → 注册 Provider → 把这个文件里的内容粘进去。

---

## 0. 一个省 2 小时的技巧（先看）

RapidAPI 支持**直接导入 OpenAPI 规范**。你的服务部署好之后，会自带一个：

```
https://你的域名/openapi.json
```

在 RapidAPI 后台选 **Import from OpenAPI**，把上面这个地址填进去，**所有端点、参数、示例会自动生成**，你不用手敲 9 个端点。

---

## 1. 基础信息

| 字段 | 填这个 |
|---|---|
| **API Name** | China Data Toolkit |
| **Category** | Data |
| **Base URL** | `https://你的域名` （部署后拿到） |
| **Short Description**（≤80 字符） | Validate Chinese ID cards, phones & business codes. Mask PII in text. |

## 2. Long Description（Markdown，整段粘贴）

```markdown
## What is this?

A pure-algorithm toolkit for **Chinese data validation and PII masking**.

No scraping, no external data sources, no third-party calls. Every endpoint is deterministic
and returns in milliseconds.

## Why it exists

If you handle Chinese user data, you have two boring problems:

1. **You need to validate it** — is this a real ID number? A real business code?
2. **You need to hide it** — logs, support tickets, screenshots and test databases should never
   contain real phone numbers or ID cards.

Both are easy to get wrong and tedious to implement. This API does both in one call.

## Endpoints

### PII Masking
- **`POST /v1/mask`** — Detects and masks phone numbers, ID cards, emails and bank cards in any
  text. Returns both the masked text and a per-hit breakdown of what was found. Built for log
  scrubbing, support tools and test fixtures.

### Validation
- **`POST /v1/validate/idcard`** — Chinese resident ID: checksum, birth date, gender, age, province
- **`POST /v1/validate/uscc`** — Unified Social Credit Code (the 18-char code on every Chinese
  business licence), per GB 32100-2015
- **`POST /v1/validate/bankcard`** — Luhn checksum + length validation
- **`POST /v1/validate/phone`** — Chinese mobile numbers with carrier detection

### Text Utilities
- **`POST /v1/count`** — Character counting that treats Chinese (per character) and English
  (per word) correctly. Most counters get this wrong.
- **`POST /v1/pinyin`** — Hanzi to pinyin: plain, numbered tones, or initials
- **`POST /v1/fake`** — Generate realistic Chinese test data (names, phones, ID cards, companies,
  addresses) for load testing and demos

## Privacy

**Nothing is stored.** No request bodies are persisted, no logs of user data, no third-party
calls. The service is stateless by design — that is the whole point of a masking API.

## Latency

Pure computation. Typical response under 50 ms, no cold-start dependency on external services.
```

---

## 3. 端点清单（导入 OpenAPI 后会自动填，这里留档核对）

| Method | Path | 说明 |
|---|---|---|
| POST | `/v1/mask` | PII 脱敏 |
| POST | `/v1/count` | 中英文字数统计 |
| POST | `/v1/pinyin` | 汉字转拼音 |
| POST | `/v1/validate/idcard` | 身份证校验 |
| POST | `/v1/validate/phone` | 手机号校验 + 运营商 |
| POST | `/v1/validate/bankcard` | 银行卡 Luhn 校验 |
| POST | `/v1/validate/uscc` | 统一社会信用代码校验 |
| POST | `/v1/fake` | 中文假数据生成 |
| GET | `/health` | 健康检查（RapidAPI 会用） |

## 4. 示例请求 / 响应（写进 endpoint 描述里，提高转化）

**POST /v1/mask**

```json
{ "text": "客户手机 13812345678，身份证 11010519491231002X" }
```

```json
{
  "masked_text": "客户手机 138****5678，身份证 110***********002X",
  "hit_count": 2,
  "hits": [
    { "type": "idcard", "original": "11010519491231002X", "masked": "110***********002X" },
    { "type": "phone",  "original": "13812345678",        "masked": "138****5678" }
  ]
}
```

**POST /v1/validate/idcard**

```json
{ "id_number": "11010519491231002X" }
```

```json
{
  "valid": true,
  "reason": "校验通过",
  "birth_date": "1949-12-31",
  "gender": "女",
  "age": 76,
  "province": "北京市"
}
```

**POST /v1/validate/uscc**

```json
{ "code": "91350100M000100Y43" }
```

```json
{ "valid": true, "reason": "校验通过", "registration_authority": "91" }
```

---

## 5. 定价方案（后台 Plans & Pricing 里建）

> 策略说明（来自一个真实运营 API 组合的复盘）：
> **把完整阶梯都挂出来**，哪怕没人买最贵的。$12 / $49 / $199 摆在一起，
> 中间那档看起来最合理——**用最贵的那档去卖中间那档**。
> 另外：**免费额度要"卡得有点难受"**，如果免费档能舒服地跑生产，永远不会有人升级。
> 所有额度必须是**硬上限**，否则一个重度用户一晚上能把你的成本打穿。

| Plan | 价格 | 调用额度 | 说明 |
|---|---|---|---|
| **Basic** | 免费 | 200 次/月 | 不用绑卡。刚好够评估，不够上生产 |
| **Pro** | $12 / 月 | 5,000 次/月 | 主力档 |
| **Ultra** | $49 / 月 | 30,000 次/月 | 对比锚点 |
| **Enterprise** | $199 / 月 | 200,000 次/月 | 锚点，几乎不会有人买 |

**超量计费**：$0.003 / 次

---

## 6. 上架后要做的事（别跳过）

**"发布"不等于"会卖"。** 原文说得很直白：

> *"Published means findable by someone who already knows the exact name.
> The catalog has tens of thousands of APIs. **Discovery is the real job, and it starts
> after you publish.**"*

所以上架后必须做的事：

1. **填满 endpoint 描述和示例** —— 开发者是看示例决定要不要试的
2. **OpenAPI 导入后逐个检查** —— 自动生成的描述往往很烂，改成人话
3. **官网/文档页**：在 RapidAPI 的 "Optimize Your Website" 里填真实说明
4. **去开发者社区回答相关问题**（Stack Overflow、Reddit r/webdev、V2EX），顺带提一句你的 API
5. **每月看一次 Analytics**：哪些端点被调得多，就往那个方向加功能

---

## 7. 必须知道的两个硬事实

| 事实 | 影响 |
|---|---|
| **RapidAPI 只通过 PayPal 打款** | 官方原文：*"we cannot accommodate other payout methods."* 中国大陆的 PayPal 收款/提现有限制，**这一条你必须先确认能不能收到钱，再去部署** |
| **抽成 20%** | 定价 $12 → 你实收 $9.6 |
| **打款延迟 30 天** | 1 月 1 日订阅 → 2 月初才到账；低于 $2 会合并发放 |

---

## 8. 官方参考

- [Payouts and Finance（打款规则）](https://docs.rapidapi.com/v1.0/docs/payouts-and-finance)
- [Adding Base URLs（必须自己部署）](https://docs.rapidapi.com/v1.0/docs/base-urls)
- [Plans & Pricing](https://docs.rapidapi.com/v1.0/docs/plans-pricing)
- [Marketing Your API（发布后怎么做）](https://docs.rapidapi.com/v1.0/docs/ive-added-my-api-to-rapidapi-now-what)
