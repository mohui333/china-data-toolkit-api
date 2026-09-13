# China Data Toolkit API —— 可上架 RapidAPI 的成品

一句话：**中文数据校验 + PII 合规脱敏 API。已写好、已测试、已部署上线。**

## 🟢 已上线

| | |
|---|---|
| **RapidAPI listing** | https://rapidapi.com/mohui333/api/china-data-toolkit |
| **线上地址** | https://china-data-toolkit-api.onrender.com |
| **交互式文档** | https://china-data-toolkit-api.onrender.com/docs |
| **OpenAPI 规范**（RapidAPI 导入用） | https://china-data-toolkit-api.onrender.com/openapi-3.0.json |
| **一键下载规范文件** | https://china-data-toolkit-api.onrender.com/download/openapi-3.0.2.json |
| **健康检查** | https://china-data-toolkit-api.onrender.com/health |
| **GitHub 仓库** | https://github.com/mohui333/china-data-toolkit-api |
| **托管平台** | Render（新加坡节点，免费层） |

**上线状态（已核验）**：可见性 `PUBLIC`，**9 个端点**全部挂载，
4 档计划 **BASIC 免费 / PRO $12 / ULTRA $49 / MEGA $199**。

上线后已逐个验证 8 个业务端点，全部返回 200 且数据正确。

---

## 一、为什么选这个题目（不是随便挑的）

我查了 RapidAPI 官方文档和一个真实运营 API 组合的复盘，发现失败的主因不是技术，是这两条：

> *"Most of your listings will earn nothing. That's not failure, it's the base rate."*
> *"Sessions rot."* —— 上游改版、数据源挂掉，你辛苦搭的 API 悄悄变成空壳。

所以这个 API 的设计原则是**刻意对抗这两件事**：

| 设计选择 | 解决什么 |
|---|---|
| **纯算法，零外部数据源** | 不会因为上游改版而失效 → **维护成本接近 0** |
| **不抓取、不存储、不转存** | 无版权风险、无隐私风险、不会被投诉下架 |
| **无状态** | 不需要数据库、不需要定时任务、不需要运维 |
| **依赖只有 3 个包** | 换任何平台都能跑，不会烂在部署上 |

**它不是"能赚钱"的保证，它是"最不容易烂掉"的形态。**

---

## 二、它到底能干什么

| 端点 | 用途 | 谁会用 |
|---|---|---|
| `POST /v1/mask` | **自动识别并打码**手机号/身份证/邮箱/银行卡 | 做日志、客服系统、测试数据的人 |
| `POST /v1/validate/idcard` | 身份证校验 + 生日/性别/年龄/省份 | 表单校验、实名流程 |
| `POST /v1/validate/uscc` | 统一社会信用代码校验（GB 32100） | 企业入驻、B 端表单 |
| `POST /v1/validate/bankcard` | 银行卡 Luhn 校验 | 支付、绑卡 |
| `POST /v1/validate/phone` | 手机号校验 + 运营商 | 注册、短信 |
| `POST /v1/count` | 中文按字/英文按词的字数统计 | 内容平台、翻译报价 |
| `POST /v1/pinyin` | 汉字转拼音（带声调/首字母） | 搜索、排序、教学 |
| `POST /v1/fake` | 生成中文假数据 | 压测、演示 |

**最值钱的是第一个。** 脱敏是合规刚需（个人信息保护法），自己做容易漏，买 API 是最省事的解法。

---

## 三、它已经过验证（40 项测试，全部通过）

```
python3 test_api.py     →  通过 40 项，失败 0 项
```

关键验证点（都是**用标准测试向量**验的，不是自己跟自己比）：

| 验证项 | 证据 |
|---|---|
| 身份证算法 | `11010519491231002X` 判合法；改校验位 → 判非法；未来生日 → 判非法 |
| 统一社会信用代码 | `91350100M000100Y43` 判合法；改一位 → 判非法；含非法字符 I → 判非法 |
| **Luhn 算法** | 标准测试向量对：`4539148803436467` 合法 / `...468` 非法 |
| 脱敏正确性 | 4 类 PII 全部正确打码，且**普通数字不误伤**（订单号 12345 保持原样） |
| 假数据自洽 | 生成的身份证**全部能通过自己的校验**，地址市/区地理一致 |
| 边界处理 | 空文本 400、超长 413、非法参数 400/422 全部正确 |

过程中我修了 2 个真 bug：
- 假数据生成的身份证地区码只有 2 位（应为 6 位），导致长度错误直接崩溃
- 地址随机拼接出现「苏州市江干区」这种地理错乱（江干区在杭州），已改成市→区关联

---

## 四、你要做的三件事

### 第 1 步：本地跑起来看看（可选，5 分钟）

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

然后打开 `http://127.0.0.1:8000/docs`，**你会看到一个可交互的 API 文档页**，能直接点着测。

### 第 2 步：部署（必须，因为 RapidAPI 不帮你托管）

**RapidAPI 官方文档说得很清楚：你要自己提供 Base URL。它只做代理、计费和密钥管理，不托管你的代码。**

三个免费选项：

| 平台 | 难度 | 注意 |
|---|---|---|
| **Render** | 最简单，连 GitHub 自动部署 | 免费层**会休眠**，冷启动约 30 秒（对 API 是硬伤） |
| **Railway** | 简单 | 有免费额度，用完要付费 |
| **Cloudflare Workers / Vercel** | 稍复杂 | 无休眠，更适合 API |

仓库里已经放好 `render.yaml`、`Dockerfile`、`Procfile`，**Render 和 Railway 都能直接读**。

部署完你会得到一个 `https://xxx.onrender.com` 这样的地址，**这就是你的 Base URL**。

### 第 3 步：上架 RapidAPI

1. 去 `rapidapi.com/provider` 注册 Provider 账号
2. 绑定 **PayPal**（⚠️ 见下方警告）
3. 新建 API，Base URL 填第 2 步拿到的地址
4. **用 `https://你的域名/openapi.json` 一键导入**，9 个端点自动生成，省 2 小时
5. 把 `RapidAPI上架资料.md` 里的描述、示例、定价方案粘进去
6. 提交审核

---

## 五、诚实的预期（我不编数字）

### 已经查证的真实数据

| 指标 | 数字 | 来源 |
|---|---|---|
| **多数 listing 的收入** | **$0**（这是基准率，不是失败） | 真实 API 组合运营者复盘 |
| 上线 1~3 个月 | $0 ~ $150 / 月 | 同上 |
| 6~12 个月成熟 listing | $300 ~ $1,200 / 月 | 同上 |
| 第一个付费客户 | **4~8 周** | 同上 |
| 每周维护时间 | **2~4 小时**（"boring middle"） | 同上 |
| 平台抽成 | **20%** | RapidAPI 官方文档 |
| 打款延迟 | **30 天** | RapidAPI 官方文档 |

**"挂 20 个 API，大多数是 0 用户，一两个撑起全部"** —— 这是原文的原话。

### 换算到你的目标

$0~150/月 ≈ **¥0~1080/月 ≈ ¥0~36/天**。

**"每天 10 元"落在这个区间的下半段。也就是说：如果它成了，能覆盖；但大概率它是 0。**

---

## 六、⚠️ 一个必须先确认的硬问题

**RapidAPI 只用 PayPal 打款。** 官方原文：

> *"RapidAPI currently only pays out API providers via PayPal. Unfortunately, we cannot accommodate other payout methods."*

对准中国用户意味着：**你得先确认你的 PayPal 能正常收款并提现。** 中国大陆的 PayPal 提现到境内银行有额度和渠道限制。

**所以正确顺序是：先去确认 PayPal 能不能收到钱 → 再花时间部署。**
如果收不到，这条路在第一步就断了，别浪费时间。

---

## 七、如果你决定做，接下来最该干的事

按优先级：

1. **确认 PayPal 收款**（10 分钟，决定生死）
2. 部署拿到 Base URL（30 分钟）
3. 导入 OpenAPI + 粘上架资料（30 分钟）
4. **把 endpoint 描述改成人话**（自动生成的描述很差，这一步直接影响转化）
5. 提交审核
6. 之后每个月：看一次 Analytics，往被调用最多的端点加功能

---

## 八、文件清单

```
rapidapi-api/
├── main.py                  ← API 全部代码（已测试）
├── test_api.py              ← 40 项测试，跑一遍就知道好不好
├── requirements.txt         ← 只有 3 个依赖
├── Dockerfile               ← 任何平台都能部署
├── render.yaml              ← Render 一键部署配置
├── Procfile                 ← Railway / Heroku 用
├── RapidAPI上架资料.md       ← 后台要填的内容，复制粘贴即用
└── README.md                ← 你正在看
```
