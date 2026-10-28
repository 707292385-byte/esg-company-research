# 数据源与命令参考

按环境能力选择数据源，从上到下优先级递减。所有来源查到的数据都要登记来源编号，供报告正文上标引用。

## 一、结构化金融数据与权威评级栏目（环境已装 finance-data 类插件时优先用结构化源）

### westock CLI（中证/聚源 ESG 评级、风险事件、公告、新闻）

安装（仅首次）：

```bash
bash <westock-data技能目录>/scripts/setup.sh
# 装到 ~/.local/bin/westock，PATH 需包含该目录
```

常用命令：

```bash
# 名称转代码（必做第一步）
westock search 宁德时代

# ESG 评级：中证 + 聚源双源（仅 A 股，sh/sz/bj 前缀）
westock esg sz300750
westock esg sz300750,sz002594,sh601012   # 同业对标批量查询

# 风险事件（负面舆情章节）：8 类可选
# specialtrade(ST) pledge(质押) unlock(解禁) lawsuit(诉讼)
# seasonedissue(增发) leaderchange(高管变动) executivetransfer(高管增减持) bondrating(评级)
westock risk sz300750 --types lawsuit,specialtrade,pledge

# 公告与新闻
westock notice list sz300750 --limit 20
westock news list sz300750 --limit 20
```

要点：
- 代码必带市场前缀，禁止裸数字。
- `westock esg` 无行业排名字段——行业排名优先从新浪财经 ESG评价文章页取，无该信息时用同业可比公司评级对比表替代。
- 输出已是 Markdown 表格，直接读取，不要用脚本解析。

### neodata 自然语言金融搜索（评级交叉验证、ESG 资讯）

```bash
python3 <neodata-financial-search技能目录>/scripts/query.py --query "宁德时代ESG评级，各评级机构评级及行业排名"
```

要点：
- 覆盖恒生聚源 ESG（总评分 + E/S/G 分项 + 近期历史）等结构化数据，可作 westock 的交叉验证源。
- 默认不传 `--data-type`，同时召回结构化数据与资讯文章。
- 输出 `TOKEN_EXPIRED` / `TOKEN_MISSING` 时，按该技能文档取凭证后重试（最多重试 1 次）。
- 召回的 ESG 相关资讯可直接用于新闻与奖项章节。

### 新浪财经 ESG 评级中心（多机构评级主力源）

页面：`https://finance.sina.com.cn/esg/grade.shtml`。数据走 `global.finance.sina.com.cn` 的 EsgService 接口，须带 `Referer: https://finance.sina.com.cn/esg/grade.shtml`。

**个股全机构查询（首选）**：

```bash
curl "https://global.finance.sina.com.cn/api/openapi.php/EsgService.getEsgStockInfo?symbol=sz000050" \
  -H "Referer: https://finance.sina.com.cn/esg/grade.shtml"
```

- 一次返回 16 家机构最新评级：MSCI、标普 CSA、中证指数、国证指数、中国国新、中债、商道融绿、联合赤道、中诚信 ESG、秩鼎、华证、有机数、妙盈、中财绿金院、晨星 Sustainalytics、盟浪，含评级、日期、E/S/G 分项。
- **symbol 必须带小写市场前缀（sz/sh/hk + 6 位代码）**，裸代码返回全「-」。
- `detail` 字段是 E/S/G 分项评分，不是历史；接口无历史评级序列。

**各机构评级档位分布（行业相对位置参考）**：

```bash
curl "https://global.finance.sina.com.cn/api/openapi.php/EsgService.getEsgRatingDistribution?symbol=sz000050" -H "Referer: ..."
```

返回每家机构的评级档位分布（如 MSCI 全市场 CCC 共 7 家），可计算相对位置。

**列表分页端点**（无过滤参数，需翻页，个股查询优先用上面的接口）：
`getEsgStocks`（多机构聚合）、`getMsciEsgStocks`、`getSPEsgStocks`、`getCsindexEsgStocks`、`getHzEsgStocks`（华证）、`getZdEsgStocks`（秩鼎）、`getRftEsgStocks`（伦交所），参数 `p`（页码）`num`（每页）。

**近三年评级序列与行业排名**：接口不含历史，用新浪「ESG评价」栏目静态文章页补充：

- 地址形如 `https://finance.sina.com.cn/stock/aiassist/esgpj/<日期>/doc-<id>.shtml`，静态 HTML 可直接抓取。
- 每篇含：最新评级、近五年历史评级、同行业排名（注明 GICS 三级或申万三级口径、参评公司数、名次）、同行业排名表。
- 检索方式：搜索引擎搜「`公司简称 + 机构名 + ESG评级`」限定 `finance.sina.com.cn`；机构名逐家试，以实际检索到为准。
- 该栏目通常为年度发布，与评级中心的批次/日期可能不同——并列展示、各自注明日期，不互相覆盖。

### Wind 官网公开门户（免登录，已验证 2026-10-27）

Wind ESG 评级公开查询门户：`https://esg.wind.com.cn/WindESGRating/index.html`。

**免登录直达链接**：`https://esg.wind.com.cn/WindESGRating/index.html?lan=cn&windcode=<代码>#/public-esg`（如 `windcode=000050.SZ`），或首页搜索框选公司后自动跳转。页面无需登录即展示：

- 当前评级（大徽章，如 A）与公司简介；
- 「ESG综合得分行业排名：x / 行业家数（行业名）」；
- 行业评级分布（AAA–CCC 各档占比）；
- 评级趋势（近 5 期，约年度更新，每期带年月）；
- ESG 得分构成：综合得分、管理实践得分、争议事件得分（各带更新日期）。

**抓取方式**：页面为 React SPA，curl 只能拿到空壳，用无头浏览器（`--headless=new --dump-dom`）或浏览器自动化技能读取；SPA 内文本可用 accessibility snapshot 逐段提取。评级趋势数据在 SVG 图表旁的 StaticText 里（先日期序列后评级序列，按顺序配对）。

**为什么不能直接 curl API**：`/Wind.ESG.Web/Service/{模块}/{方法}` 与 `WindSecureApi.aspx` 均校验 SessionId（JS 内置兜底 sessionid 已过期，返回 E_950003/10011）；公开数据实际走 `https://wx.wind.com.cn/WindESGPublicWeb/Service/{page}?windcode=<代码>`，POST 表单 `Content={"Invokes":[{"Name":"...","Parameters":{...}}]}`，但 invoke 名在懒加载 chunk 中、未完全逆向——浏览器流程最稳，不必再试 API。

**交叉验证**：公司 ESG 报告「附录·ESG 评级」常自述「万得 ESG 评级 X 级（名次/家数），截至 X 年 X 月」，可与门户数据互相印证（门户数据更新，以门户为准并注明查询日期）。

## 二、公开网络渠道（评级之外的补充检索）

### 巨潮资讯网（随 skill 附带脚本 scripts/cninfo_searcher.py）

报告披露与制度公告采集优先用脚本，不用手工翻页：

```bash
# 检索历年 ESG 报告（自动尝试 ESG/可持续发展/环境、社会/社会责任 关键词变体并合并去重）
python3 scripts/cninfo_searcher.py 宁德时代
python3 cninfo_searcher.py 300750 --download --out ./downloads   # 连 PDF 一起下载

# 制度公告：指定关键词变体
python3 cninfo_searcher.py 宁德时代 --kws "ESG管理制度" "信息披露管理制度" "ESG管理办法"
```

实测要点（踩坑记录，勿重蹈）：
- 全文检索接口的 `stock` 过滤参数已失效（传了反而 0 结果），只能用「公司简称/代码 + 关键词」标题检索。
- 接口依赖首次响应种下的 Cookie，必须用 `requests.Session()` 全局会话；散装 requests.post 会随机漏结果。
- 连续请求会被限频返回 0：脚本已内置关键词间隔与空结果重试，但不要并发轰炸。
- 报告标题措辞不统一（ESG报告 / 可持续发展报告 / 环境社会与公司治理报告），单关键词必漏，多变体合并才是全的。
- 沪深 A 股代码↔简称映射来自官方 szse_stock.json；港股无映射时直接用输入词检索。
- 下载地址为 static.cninfo.com.cn/finalpage/...，脚本输出已是可直引的公告链接与发布日期。

### 其他渠道

| 渠道 | 用途 | 注意 |
| --- | --- | --- |
| 交易所官网/披露平台 | 沪深北交易所、港交所披露易 | 问询函、监管函件也在这里查 |
| 公司官网 | 报告下载、ESG 专栏、治理架构介绍、新闻与奖项、ESG 评级荣誉页 | 官网信息注明「公司官网」；公司 ESG 报告中的「主流评级表现」表可作评级补充来源 |
| 搜索引擎（新闻/奖项/负面） | 各机构评级报道、奖项、环保处罚、诉讼 | 处罚信息优先用地方生态环境部门、信用中国等官方来源 |

网络检索时只认官方与权威来源（监管机构、交易所、公司官网、主流财经媒体），自媒体聚合内容不作为事实依据。

## 三、覆盖范围与取数口径

| 数据项 | 渠道 | 查不到时的处理 |
| --- | --- | --- |
| 16 家机构最新评级（MSCI/标普/中证/国证/商道融绿/联合赤道/中诚信/秩鼎/华证/晨星等） | 新浪 ESG 评级中心个股接口 | 留占位 |
| 中证/聚源 ESG 评级（A 股，月度） | westock + neodata，双源交叉验证 | 留占位 |
| 近三年评级序列 + 行业排名 | 新浪「ESG评价」栏目静态文章页（GICS 三级或申万三级口径） | 检索不到则留占位 |
| Wind ESG 评级 | 官网公开门户免登录查询（无头浏览器/浏览器自动化，windcode 直达链接） | 留「待人工补充（Wind）」占位 |
| 港股/美股评级 | 新浪个股接口同样支持（hk 前缀） | 留占位 |
| 非上市公司评级/报告 | 不适用 | 报告开头标注数据边界 |

## 四、结构化数据不可用时的整体降级

环境没有 finance-data 类插件时，全部数据走公开网络渠道：工商信息用企业信用信息公示类官方渠道，报告与制度用交易所披露平台与公司官网，评级靠网络检索（能核实多少算多少，其余留占位），并在报告概览页注明「本次采用公开网络渠道，评级覆盖以可核实来源为限」。
