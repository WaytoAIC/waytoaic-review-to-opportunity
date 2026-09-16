# 数据约定

脚本使用 Python 3 标准库，无网络调用。JSONL 每行一条对象。非本格式输入由 Agent 映射，保留未知，不猜测字段。

## 输入 reviews.jsonl

字段：`id`（可选，本地编号，不等于平台 ID）、`title`、`content`、`date`、`star`、`skus`（字符串列表）、`verified`、`vine`（布尔或 null）、`images`（URL 列表）。可以保留 `source_url`（来源页）、`source_review_id`（平台 ID），未知就省略。购买标记为字符串时先明确转换；脚本拒绝字符串 false 被误当 true。

脚本删除作者姓名等非分析必需信息。同一日期、标题、正文、变体作为重复候选；不宣称已完成独立身份去重。重复记录合并图片并保留 alias ID；不同内容使用同一 ID 则报错，要求先修正。

目标匹配支持 `Color:`、`Size:` 字段，统一英文大小写、空格、英尺引号和乘号；不做模糊颜色匹配。若没有同时给出目标颜色、尺寸则归属 unknown；其他变体为 other_or_unknown，不能由脚本判成同款。

## analysis.json

```json
{
  "author": "waytoaic",
  "completion": "partial",
  "reviewed_ids": ["R001"],
  "findings": [{
    "id": "P01",
    "problem": "具体可观察现象",
    "support_ids": ["R001"],
    "counter_ids": [],
    "quotes": [{"review_id": "R001", "text": "从该记录逐字摘取的片段"}],
    "applicability": "related",
    "status": "hypothesis",
    "people": "未知",
    "scene": "原文明确的场景或未知",
    "need": "推断时注明推断",
    "solution": "当前方案",
    "confidence_reason": "说明证据强弱及局限",
    "gaps": ["还缺什么"],
    "next_test": "最有区分力的验证动作"
  }],
  "actions": [{
    "type": "product_iteration",
    "finding_ids": ["P01"],
    "status": "hypothesis",
    "proposal": "候选调整或验证任务",
    "verification": "如何验证",
    "acceptance": "成功判据，未获业务确认须注明",
    "gaps": ["待补数据"]
  }]
}
```

- `completion`: partial / complete。complete 要求 reviewed_ids 覆盖每一条保留记录，包括缺正文条目的识别处理；不能只做关键词筛选就报全量分析。
- `applicability`: target / related / unknown。target 至少需要一条精确匹配记录；仍须人工评估跨款适用性。
- `status`（finding）: insufficient / hypothesis / business_confirmed。business_confirmed 要补 `human_confirmation` 记录真实确认依据；不能填“AI 推测用户会同意”。
- `status`（action）: blocked / hypothesis / test_plan。test_plan 仅表示已提出试验设计，不代表样品、预算或阈值已就绪；均不代表效果已验证。每项 action 必填 acceptance（成功判据），未确认的判据标“建议/待业务确认”。
- 引用只能指向 reviewed_ids 中的规范 ID，quotes 必须能在原记录标题或正文中逐字找到。
- check 只做结构、引用和部分边界检查。需求推断、图片内容、人数独立性、业务确认真实性与建议质量由 Agent/用户复核。
