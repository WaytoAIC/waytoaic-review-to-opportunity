## 🚀 Way to AIC | 通往 AI 电商之路
---
### 🌐 官网 Website
- https://waytoaic.com
- https://www.waytoaic.com
---

### 👥 社群招募 Community
`Way to AIC 社群招募 | WaytoAIC.com`

<p align="center">
  <img src="https://github.com/user-attachments/assets/d9f8bbf4-2056-4780-975d-86c885b52bab" width="70%">
</p>

---

### 📣 公众号 WeChat Official Account
`维正 WaytoAIC`

<p align="center">
  <img src="https://github.com/user-attachments/assets/71c71a5c-e68a-4f30-9afb-f2b056619991" width="300">
</p>

---

### 🧠 知识星球 Xiaozhixing
`AI电商之路 WaytoAIC`

<p align="center">
  <img src="https://github.com/user-attachments/assets/9eccef07-0e84-45a7-a415-affcb18c928d" width="200">
  <img src="https://github.com/user-attachments/assets/4e99fbc3-1981-4fee-b113-c9821141102d" width="400">
</p>

---

### 🧩 About Way to AIC

**AIC = AI Commerce**

在 AI 重塑商业的时代，我们希望和每一个拥抱 AI 的卖家：

- 找到场景
- 定义问题
- 积累能力
- 设计系统

共同通往 AI 电商之路。

> Way to AIC 不是教学，不是工具，
> 而是一条所有电商人共同走的进化之路。

### WaytoAIC 理念 | Principles

| 中文 | English |
|---|---|
| 场景先于方法 | Context before method |
| AI 的价值来自真实业务场景，而不是技术本身。 | AI creates value through real business contexts, not through technology alone. |
| 问题先于答案 | Problem before answer |
| 定义问题，比拥有工具更重要。 | Defining the problem matters more than collecting tools. |
| 系统胜过技巧 | System over tricks |
| 技巧是术，系统才是道，决定卖家的上限。 | Tricks are tactical; systems define long-term leverage and ceiling. |
| 共创优于独行 | Co-creation over solo progress |
| 我们相信，真正的进化发生在共同探索的过程中。 | Real evolution happens through shared exploration. |

---
# 评论到产品机会 · Review to Opportunity

作者 / Author: **waytoaic** · Version **1.1.0**

先判断评论置信度，再按「人群 → 场景 → 需求 → 解决方案」拆解，将证据连接到完整产品机会、产品迭代、Listing、广告搜索词及定投 ASIN。默认输出可搜索、可筛选、可切换决策卡的离线 HTML。

Evaluate review confidence first, then connect people, scenarios, needs and solutions to five product and operations decisions. Outputs include an interactive, offline HTML report.

## 安装 / Install

需要 Python 3.10+、Git、Bash。无 Python 第三方依赖。Requires Python 3.10+, Git and Bash. No third-party Python packages.

```bash
git clone https://github.com/WaytoAIC/waytoaic-review-to-opportunity.git
cd waytoaic-review-to-opportunity
bash install.sh --target codex
# Or: bash install.sh --target openclaw
```

支持 `--dest /path/to/skill`、`--repo owner/repo`、`--ref main`。目标已存在时停止，避免覆盖用户修改。Existing destinations are never overwritten.

## 调用 / Use

```text
使用 $waytoaic-review-to-opportunity，分析我提供的美国站评论。
先判断置信度，Vine 相对低优先级；核查图片、场景、边角/整体、使用时长与人数。
输出问题证据卡、五类决策卡和 HTML，区分事实、推断和待验证方案。
```

真实数据由用户提供，或使用当前已授权的数据工具获取。本 Skill 不自带账号、爬虫或广告执行权限。Provide your own authorized review data; no credentials, scraper or ad execution is included.

## 模拟示例 / Synthetic example

[查看 HTML 文件](examples/report.html)（下载后浏览器打开 / download and open locally）

```bash
python3 scripts/review_workbench.py prepare --input examples/reviews.jsonl --output runs/demo --asin DEMO --marketplace US
python3 scripts/review_workbench.py check --run runs/demo --analysis examples/analysis.json
python3 scripts/render_report.py --run runs/demo --analysis examples/analysis.json --output runs/report.html
python3 -m unittest discover -s tests -v
```

输入字段见 [数据合同](references/contracts.md)，分析卡片见 [卡片格式](references/cards.md)。`analysis.json` 由执行 Skill 的模型结合证据产出；渲染脚本不自动理解评论。The model produces evidence-grounded analysis; the renderer only validates and displays it.

## 已验证范围 / Validation boundaries

18 项测试通过，并经过真实数据准备及独立前向试跑。已验证的是结构检查、引用一致性、覆盖范围与 HTML 工作流；未证明评论真实性、市场需求或产品/广告效果。详见 [验证记录](references/validation.md)。

18 tests and a bounded real-data forward trial validate workflow and structural checks, not review authenticity, market demand, or business performance. Public examples are entirely synthetic.

## 来源与许可 / Attribution and license

MIT · Copyright (c) 2026 waytoaic. 借鉴 buluslan/review-analyzer-skill 的分批处理与可恢复工作方式；未复制其脚本或模板。[来源说明 / Provenance](references/provenance.md)。
