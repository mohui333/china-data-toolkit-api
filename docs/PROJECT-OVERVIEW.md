# China Data Toolkit · 项目总文档

> **给未来的你**：三个月后你可能忘了这一切。看这一份文档就能完整接手。
> 最后更新：2026-09-13

---

## 一、这是什么（大白话版）

我们在 **RapidAPI**（一个"API 的淘宝"）上开了一个**24 小时自动营业的小窗口**。

程序员做 App 时经常需要处理**中国数据**——验证身份证号真假、给手机号打码、拆解地址。自己写要花好几天，**用我们的，一个月 12 美元，5 分钟接上**。

**你不需要做任何技术操作。** 干活的是服务器，收钱的是你的账户，我负责所有技术活。

---

## 二、涉及的账号（最重要的一节）

整套系统一共涉及 **5 个账号**。下面是完整清单。

### ① GitHub —— 存放代码

| | |
|---|---|
| **网址** | https://github.com |
| **你的账号** | `mohui333` |
| **用途** | 存放 API 的全部源代码。Render 从这里拉代码去部署 |
| **仓库 1** | https://github.com/mohui333/china-data-toolkit-api （**Public**，API 源码） |
| **仓库 2** | `chinese-data-validation` （**待创建**，开源库） |
| **密码** | 你自己设的，我不知道 |

⚠️ **令牌（Token）说明**

你曾经创建过一个叫 `dsh-deploy` 的令牌给我用。它的配置是：

| 项目 | 值 |
|---|---|
| 类型 | Fine-grained personal access token |
| 权限 | Contents: Read and write（只有这一个） |
| 仓库范围 | 只授权 `china-data-toolkit-api` |
| 有效期 | **7 天后自动过期** |
| 管理地址 | https://github.com/settings/personal-access-tokens |

**这个令牌到期就自动失效，不用管。** 如果以后还要我推代码，需要重新建一个。

> 🔒 **重要**：GitHub 令牌等于"改代码的钥匙"。任何时候都要设**最小权限 + 短有效期**，就像你这次做的这样。

---

### ② Render —— 托管服务器

| | |
|---|---|
| **网址** | https://dashboard.render.com |
| **登录方式** | 用 GitHub 账号登录（`mohui333`） |
| **服务名** | `china-data-toolkit-api` |
| **服务 ID** | `srv-daj88sh594qs73b6m230` |
| **总览页** | https://dashboard.render.com/web/srv-daj88sh594qs73b6m230 |
| **套餐** | **Free（免费）** |
| **区域** | Singapore（新加坡，对亚洲快） |
| **用途** | 真正运行 API 的服务器，24 小时在线 |

⚠️ **这里有两个必须记住的点：**

**1. API 密钥已撤销（这是对的）**

你创建过一个 API Key 给我部署用，**任务完成后已经撤销，我验证过是 401 失效**。
管理地址：https://dashboard.render.com/u/settings

**2. 免费层会"睡觉"——这是正常的，不要试图阻止它**

| 现象 | 说明 |
|---|---|
| 15 分钟没人访问 | 服务自动休眠 |
| 下次有人访问 | 需要 **30~50 秒**冷启动 |

**为什么不能"保活"？** 我查过：Render 免费额度是 **750 实例小时/月**，而一个月是 **730~744 小时**。一个服务 24 小时不睡就吃掉几乎全部额度，**额度用完会把工作区里所有服务一起停掉**。

> **休眠不是 bug，是让免费方案能成立的机制。**

**等有付费客户后**，可以考虑升到 $7/月。在那之前，接受冷启动。

---

### ③ RapidAPI —— 上架卖东西的地方

| | |
|---|---|
| **网址** | https://rapidapi.com |
| **后台入口** | https://rapidapi.com/studio （**不是** `/provider`，那个已废弃） |
| **你的 listing** | https://rapidapi.com/mohui333/api/china-data-toolkit |
| **用途** | 全世界程序员在这上面找 API。我们在这里收钱 |
| **状态** | ✅ 已上线，可见性 PUBLIC |
| **抽成** | **20%**（定价 $12，你实收 $9.6） |

---

### ④ PayPal —— 收钱的通道（⚠️ 还没设置）

| | |
|---|---|
| **网址** | https://www.paypal.com |
| **用途** | **RapidAPI 只通过 PayPal 打款**（官方原文：*"we cannot accommodate other payout methods"*） |
| **状态** | ⚠️ **还没绑定** |

**⚠️ 一个必须避开的坑：**

| 提现方式 | 手续费 | 判断 |
|---|---|---|
| **PayPal 直接提到国内银行卡** | **每笔 $35** | ❌ **绝对不要用** |
| **走第三方（WindPayer / Payoneer）** | 约 **1%** | ✅ 用这个 |

算给你看：如果只有一个 $12 的订阅，你实收 $9.6。用 PayPal 直提，手续费 $35 —— **你会倒亏 $25**。

**正确做法**：注册一个第三方收款（WindPayer 或 Payoneer），申请一个美元收款账户，绑到 PayPal 作为提现目标。

**什么时候做**：**等真的有客户订阅了再做**。RapidAPI 会先帮你把钱扣着，不急。

---

### ⑤ UptimeRobot —— 我们决定**不做**

我原本打算配一个定时 ping 防休眠，查完发现会烧掉 Render 免费额度，**所以放弃了**。这里记一笔，免得以后你又想起来。

---

## 三、系统是怎么连起来的

```
    程序员在 RapidAPI 搜索
            ↓
    找到我们的 listing
    rapidapi.com/mohui333/api/china-data-toolkit
            ↓
    他调用 API（比如 /v1/validate/idcard）
            ↓
    RapidAPI 转发请求（抽 20% 手续费）
            ↓
    我们的服务器（Render，新加坡）
    china-data-toolkit-api.onrender.com
            ↓
    返回结果（纯算法计算，<50ms）
            ↓
    ┌─────────────────┐
    │ 代码存在 GitHub  │ ← 改了代码要重新部署
    └─────────────────┘
```

**数据流的关键点：我们不存任何数据。** 请求进来、算完、返回、忘掉。没有数据库，没有日志留存。这是"脱敏 API"该有的样子。

---

## 四、钱是怎么到你手里的

```
程序员订阅 $12/月
        ↓
RapidAPI 收下，扣 20%
        ↓
$9.60 累积在你的 RapidAPI 账户
        ↓
满 $2 就会打款（但要先绑 PayPal）
        ↓
30 天后到账 PayPal
        ↓
通过 WindPayer/Payoneer 转回国内（约 1% 手续费）
        ↓
你的银行卡
```

**定价方案（已配置好）：**

| 档位 | 价格 | 每月次数 | 作用 |
|---|---|---|---|
| BASIC | **免费** | **200 次** | 试用装，故意卡得难受 |
| PRO | $12 | 5,000 次 | 主力 |
| ULTRA | $49 | 30,000 次 | 价格锚点 |
| MEGA | $199 | 200,000 次 | 价格锚点（基本没人买） |

**注意**：RapidAPI 默认会给一个"每月 100 万次免费"的 BASIC 计划。**我们已经改成 200 次**。如果哪次重新导入后发现变成 100 万，**立刻改回 200**，否则有人能白嫖。

---

## 五、你拥有什么（资产清单）

### 线上服务

| 资产 | 地址 |
|---|---|
| **RapidAPI listing** | https://rapidapi.com/mohui333/api/china-data-toolkit |
| **后端 API** | https://china-data-toolkit-api.onrender.com |
| **交互式文档** | https://china-data-toolkit-api.onrender.com/docs |
| **健康检查** | https://china-data-toolkit-api.onrender.com/health |
| **规范文件下载** | https://china-data-toolkit-api.onrender.com/download/openapi-3.0.2.json |
| **GitHub 仓库** | https://github.com/mohui333/china-data-toolkit-api |

### 10 个业务端点

| 端点 | 干什么 | 谁会需要 |
|---|---|---|
| `POST /v1/mask` | **脱敏**：手机/身份证/邮箱/银行卡自动打码 | 日志清洗、客服系统、测试数据 |
| `POST /v1/validate/idcard` | 身份证校验 + 生日/性别/年龄/省份 | 注册表单、实名流程 |
| `POST /v1/validate/uscc` | 统一社会信用代码校验 | 企业入驻、B 端表单 |
| `POST /v1/validate/bankcard` | 银行卡 Luhn 校验 | 支付、绑卡 |
| `POST /v1/validate/phone` | 手机号 + 运营商 | 注册、短信 |
| `POST /v1/validate/plate` | **车牌校验**（含新能源/挂车/教练车） | 停车、门禁、物流、保险 |
| `POST /v1/address/parse` | **中文地址拆解**成省/市/区 | 电商发货、CRM 清洗 |
| `POST /v1/count` | 中英文字数统计 | 内容平台、翻译报价 |
| `POST /v1/pinyin` | 汉字转拼音 | 搜索、排序、教学 |
| `POST /v1/fake` | 生成中文测试假数据 | 压测、演示 |

**额外**：所有端点都支持 `?lang=zh` 参数，加了就返回中文（默认英文，因为客户是全球开发者）。

### 本地文件

在 `mh_work/` 目录下：

```
rapidapi-api/                  ← API 完整源码
    ├── main.py                ← 全部代码（含 10 个端点的英文描述）
    ├── test_api.py            ← 76 项自动化测试
    ├── openapi-3.0.2.json     ← 给 RapidAPI 用的规范文件
    ├── README.md              ← 技术说明
    ├── RapidAPI上架资料.md     ← 上架用的文案
    ├── 生成logo.py            ← logo 生成脚本
    ├── logo/                  ← logo 图片（512/256/64）
    ├── Dockerfile / render.yaml / Procfile / requirements.txt
    └── 本文件

chinese-data-validation/       ← 开源库（待发布）
xianyu-digital-goods/          ← 早期的闲鱼方案（已放弃，留着存档）
```

---

## 六、日常操作（每周 2 分钟）

### 每周看一次：有没有人在用

**位置一：看调用量**

```
rapidapi.com/studio → 你的 API → 左侧栏 【Analytics】
```

> **关键判断**：如果看到 **"Log Collection Methods"** 这个标题，
> 说明**一次调用都还没有**。这是正常的，不是故障。

**位置二：看谁订阅了**

```
rapidapi.com/studio → 你的 API → Hub Listing → 【Community】标签
```

点 **Free Users**（官方提醒：免费用户最容易漏看）和 **Paid Users**。每行显示订阅日期、**最近 60 天调用次数**、最后活跃时间。

### 需要改代码时

1. 告诉我改什么（我写代码 + 测试）
2. 我推到 GitHub
3. **你去 Render 点一次手动部署**
   ```
   https://dashboard.render.com/web/srv-daj88sh594qs73b6m230
   → 右上角 [Manual Deploy] → [Deploy latest commit]
   ```
   （公开仓库连不了 webhook，所以**不能自动部署**，必须手点）
4. 如果改了 API 的端点或描述，还要**重新导入规范**：
   ```
   下载 https://china-data-toolkit-api.onrender.com/download/openapi-3.0.2.json
   → rapidapi.com/studio → 你的 API
       → Hub Listing → Definitions → CI/CD
           → [Import OpenAPI] → [Upload File]
   ```
5. **重新导入后必须检查**：Monetize → BASIC 是不是还是 **200**（怕被重置回 100 万）

---

## 七、还没做的事

| 待办 | 谁做 | 说明 |
|---|---|---|
| **上传 logo** | 你 | 我生成了 `logo-512.png`，传到 General 标签。现在还是 RapidAPI 的默认图 |
| **建开源库仓库** | 你 | 建一个空的 public 仓库 `chinese-data-validation`，并把它加进 GitHub 令牌授权 |
| **绑定 PayPal 收款** | 你 | **等真有订阅再做**，用 WindPayer/Payoneer 避免 $35 手续费 |
| **加 Spotlight** | 你 | listing 的 About 标签 → `+ Add Spotlight`，把 README 挂上去 |
| **加使用计数器端点** | 我 | 可选。加了之后我能随时帮你查调用量 |

---

## 八、风险与红线

### 🔴 绝对不能做

| 事项 | 后果 |
|---|---|
| 把任何密钥写进代码或提交到 GitHub | 仓库是**公开**的，密钥会立刻泄露 |
| 在公开仓库放真实邮箱、手机号 | 同上 |
| 用 PayPal 直提国内银行 | 每笔 $35，小额必亏 |
| 配置定时 ping 保活 Render | 烧光免费额度，**所有服务被停** |
| 把 BASIC 计划改成大额度 | 有人能白嫖 |
| 用 AI 批量生成内容去各大社区发 | 封号，而且没用 |

### 🟡 需要注意

| 事项 | 说明 |
|---|---|
| **GitHub 令牌会过期** | 7 天后自动失效，属正常 |
| **Render 免费层会休眠** | 首次访问等 30~50 秒，正常 |
| **数据不准确的风险** | 手机号段、车牌规则每年会更新，我的数据是快照 |
| **我们不做身份验证** | API 只验号码**结构**，不能证明人存在。listing 里已写明 |

### ✅ 已经做对的安全措施

- 现有公开仓库扫描过：**0 处密钥、0 个真实邮箱**
- Render API Key：**已撤销**（验证过是 401）
- GitHub 令牌：**最小权限 + 7 天过期**
- API 设计：**不存储任何请求数据**

---

## 九、出问题怎么办

| 症状 | 可能原因 | 怎么办 |
|---|---|---|
| 打开 API 地址很慢（30~50 秒） | Render 免费层休眠 | 正常，等一下就好 |
| `/health` 返回 200，但 listing 上端点报错 | 规范没重新导入 | 走第六节的"重新导入"流程 |
| BASIC 计划变成 100 万次 | 重新导入把配置冲了 | 立刻改回 200 |
| 服务完全打不开 | Render 服务被停 | 去 dashboard 看状态，看邮箱有没有 Render 的邮件 |
| 想改端点描述 | — | 告诉我，我改代码 + 推 + 你部署 + 重新导入 |

---

## 十、诚实预期（这一节最重要）

### 真实数据（我查证过的）

| 指标 | 数字 | 来源 |
|---|---|---|
| 多数 listing 的收入 | **$0**（这是基准率，不是失败） | 真实 API 组合运营者复盘 |
| 上线 1~3 个月 | $0 ~ $150/月 | 同上 |
| 6~12 个月成熟 listing | $300 ~ $1,200/月 | 同上 |
| **第一个付费客户** | **4~8 周** | 同上 |
| 每周维护 | 2~4 小时（"无聊的中间期"） | 同上 |
| 平台抽成 | 20% | RapidAPI 官方文档 |
| 打款延迟 | 30 天 | RapidAPI 官方文档 |

官方文档里最该记住的一句：

> **"Publishing is not selling."**
> 发布不等于会卖。它只意味着"知道确切名字的人能搜到"。
> 目录里有几万个 API，**被发现才是真正的工作，而且它是从你发布之后才开始的。**

### 达到"每天 10 元"需要多少客户

每天 10 元 ≈ 每月 ¥300 ≈ $42。RapidAPI 抽 20%，所以毛收入要 $52：

| 客户买哪档 | 需要几个人 |
|---|---|
| PRO $12 | **5 个** |
| ULTRA $49 | **2 个** |
| MEGA $199 | **1 个** |

**只要 5 个付 $12 的人。** 问题不是"量"，是"从 0 到 5"。

### 所以

**前 1~3 个月大概率是 $0。这不是失败，这是这个生意的正常样子。**

---

## 十一、完整历程（我们做了什么）

| 阶段 | 做了什么 |
|---|---|
| 1 | 你问"100 元怎么每天赚 10 元"。我算了复利：1.1³⁶⁵ ≈ 1280 万亿，**数学上不存在** |
| 2 | 试了**闲鱼卖数字商品**：做了 8 个 Excel 模板、10 个 Python 脚本、30 张主图、10 个 SKU 文案。查证后发现：无公开 API、登录墙、虚拟商品限流、新号第一月 0~100 元。**放弃** |
| 3 | 评估了素材站（平台正收紧 AI 内容，分成 0.5 元/次）、Whop（13 天 0 单）、插件市场。**都不合适** |
| 4 | **选定 RapidAPI**：唯一同时满足"平台自带搜索流量 + 我能全自动生产 + 不需要你值守"的形态 |
| 5 | 写了 **China Data Toolkit API**：8 个端点起步，零外部依赖，40 项测试 |
| 6 | 推 GitHub → 部署 Render → 上架 RapidAPI（你点） |
| 7 | 发现 FastAPI 输出 OpenAPI **3.1.0**，RapidAPI 只收 **3.0.2**，写了自动降级转换器 |
| 8 | 发现响应值是**中文的**（`"reason":"校验通过"`），对英文市场不专业 → **全面英文化**，加 `?lang=zh`。测试 40 → 47 项 |
| 9 | 把端点描述**写进代码**，重新导入即自动填充。测试 47 → 72 项 |
| 10 | 新增**车牌校验**和**地址解析**，端点 8 → 10。修了车牌挂车判定 bug |
| 11 | 拦住一个坑：**保活会烧光 Render 免费额度**，不做 |
| 12 | 写开源库 `chinese-data-validation`，**测试时抓到一个真漏洞**：`keep_tail=0` 时脱敏会泄露原文。库和线上 API 两处都修了。测试 72 → 76 项 |
| 13 | 生成 logo、写这份文档 |

### 花了多少钱

**¥0。** 全程免费层：GitHub 免费、Render 免费、RapidAPI 免费。

---

## 十二、快速索引

| 我想…… | 去哪里 |
|---|---|
| 看有没有人用 | rapidapi.com/studio → Analytics + Community |
| 改 API 功能 | 告诉我，我改 |
| 重新部署 | dashboard.render.com/web/srv-daj88sh594qs73b6m230 → Manual Deploy |
| 改 listing 描述 | rapidapi.com/studio → Hub Listing |
| 看钱 | rapidapi.com/studio → Monetize → Transactions |
| 管 GitHub 令牌 | github.com/settings/personal-access-tokens |
| 管 Render 密钥 | dashboard.render.com/u/settings |
| 测 API 能不能用 | 打开 https://china-data-toolkit-api.onrender.com/docs |

---

*本文档由 AI 生成并维护。有任何不清楚的地方，直接问，我改文档。*
