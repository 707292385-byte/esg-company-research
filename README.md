# esg-company-research

公司 ESG 资料调研技能：给定公司名称或代码，自动采集 ESG 报告披露、评级与同业对比、治理架构、制度体系、新闻奖项、负面舆情、关键绩效、承诺目标等信息，生成一份逐条可溯源的客户 ESG 调研报告（HTML），并把近三年 ESG 报告 PDF 一并下载到输出包。

## 使用方法

在 WorkBuddy 中安装本技能后，直接说：

- 「帮我整理宁德时代 ESG 相关资料」
- 「调研一下 XX 公司的 ESG 情况」
- 「做一份 XX 的客户 ESG 调研报告，不带负面舆情」

报告默认保存在当前工作区 `客户ESG调研/` 目录，近三年 ESG 报告 PDF 存在同目录 `<公司简称>-资料/` 子文件夹。

## 安装方式

方式一：在 WorkBuddy 中粘贴以下一键安装链接：

```
workbuddy://codebuddy-ide/skill/install?skillname=esg-company-research&channelType=link&downloadurl=https%3A%2F%2Fcodeload.github.com%2F707292385-byte%2Fesg-company-research%2Fzip%2Frefs%2Fheads%2Fmain
```

方式二：手动安装——下载本仓库 ZIP，解压后把文件夹改名为 `esg-company-research`（必须与 `SKILL.md` 顶部的 `name` 一致），放到 `~/.workbuddy/skills/` 下，重启会话即可。

## 数据来源与覆盖范围

| 数据项 | 来源 |
| --- | --- |
| 中证 / 恒生聚源 ESG 评级（A 股） | 结构化金融数据插件（westock / neodata），自动查询并交叉验证 |
| 秩鼎 / 中证 / 伦交所 / MSCI / 华证 / 商道融绿 / 联合赤道等评级 + 同行业排名 | 新浪财经「ESG评价」栏目（静态文章页，含同行业排名表） |
| Wind ESG 评级 | Wind 官网公开评级门户（esg.wind.com.cn），动态页面用无头浏览器查询 |
| 报告披露、制度公告 | 巨潮资讯网、交易所披露平台、公司官网 |
| 工商信息 | 企业信用信息公示等官方渠道 |

环境里没有结构化金融数据插件时，技能自动降级为纯公开网络检索，并在报告中标注数据边界。

## 硬性规则

- 所有数据逐条溯源：正文上标编号 + 附录来源清单（含 URL 与查询日期）。
- 严禁臆造：查不到就写「未查到 / 未披露 / 待人工补充」。
- 不同机构评级不可跨体系比较。
- 报告样式需用户确认后固定复用：首次生成先出样式样张，确认后不再重复确认。
- 非上市公司自动裁剪不适用的章节并标注数据边界。

## 文件结构

```
esg-company-research/
├── SKILL.md                      # 技能主文件（触发、流程、规则）
├── scripts/cninfo_searcher.py    # 巨潮公告检索与 PDF 下载脚本（报告披露/制度公告采集）
├── references/data-sources.md    # 数据源清单、命令用法、降级策略
├── references/report-spec.md     # 报告结构、章节要求、撰写与样式规范
└── assets/report-template.html   # HTML 报告模板骨架
```

脚本依赖 Python3 + requests，无需其他第三方库。
