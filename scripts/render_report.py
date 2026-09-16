# -*- coding: utf-8 -*-
"""Render a portable, offline HTML report from checked evidence. Author: waytoaic."""
import argparse
import html
import json
import re
from pathlib import Path
from review_workbench import check

LABELS = {'new_product': '新产品机会', 'product_iteration': '产品方向迭代', 'listing': 'Listing 迭代',
          'search_terms': '广告搜索词', 'asin_targeting': '定投 ASIN'}
STATUS = {'blocked': '缺少证据', 'hypothesis': '待验证假设', 'test_plan': '已有试验方案',
          'insufficient': '资料不足', 'business_confirmed': '业务已确认问题'}


def esc(value):
    return html.escape(str(value if value is not None else '未知'), quote=True)


def plain(value):
    return html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))


def bullets(items):
    return '<ul>' + ''.join('<li>' + esc(item) + '</li>' for item in items) + '</ul>'


def render(run, analysis_path, output, title='从评论证据，找到产品机会'):
    run, analysis_path, output = Path(run), Path(analysis_path), Path(output)
    # Refuse invalid evidence before writing or replacing a report.
    receipt = check(run, analysis_path)
    analysis = json.loads(analysis_path.read_text(encoding='utf-8'))
    coverage = json.loads((run / 'coverage.json').read_text(encoding='utf-8'))
    records = {r['id']: r for r in map(json.loads, (run / 'reviews.jsonl').read_text(encoding='utf-8').splitlines())}
    config = coverage['config']
    findings, actions = analysis['findings'], analysis['actions']
    parts = []
    for f in findings:
        frames = ''.join('<div class="frame"><label>' + label + '</label><p>' + esc(f[key]) + '</p></div>'
                         for key, label in [('people', '人群 / 谁'), ('scene', '场景 / 何时何地'),
                                            ('need', '需求 / 想达成什么'), ('solution', '方案 / 现在怎么做')])
        quotes = ''.join('<blockquote lang="en">' + esc(q['text']) + '</blockquote><p class="meta">' +
                         esc(q['review_id']) + ' · ' + esc(records[q['review_id']]['date']) + ' · ' +
                         esc(' · '.join(records[q['review_id']]['skus']) or '变体未知') + '</p>' for q in f['quotes'])
        parts.append('<article class="finding"><div class="problem"><span class="pill">' + esc(f['id']) + ' · ' +
                     STATUS[f['status']] + '</span><h3>' + esc(f['problem']) + '</h3><p>适用范围：' +
                     {'target': '目标款（仍需业务判断）', 'related': '相关变体', 'unknown': '尚未确定'}[f['applicability']] +
                     '</p></div><div class="four">' + frames + '</div><div class="proof"><h4>证据与置信度</h4><p>' +
                     esc(f['confidence_reason']) + '</p><div class="legend"><span>支持引用 ' + str(len(f['support_ids'])) +
                     ' 条</span><span>反例引用 ' + str(len(f['counter_ids'])) + ' 条</span></div><p class="note">引用记录数不是独立人数或缺陷率；同一记录可支持一个主张、反驳另一个主张。</p>' +
                     '<details><summary>查看原话摘录 ＋</summary>' + (quotes or '<p>未附原句摘录，请查看评论索引。</p>') +
                     '</details><div class="missing"><b>还缺什么</b>' + bullets(f['gaps']) + '</div><h4>下一步验证</h4><p>' +
                     esc(f['next_test']) + '</p></div></article>')
    tabs, cards = [], []
    for i, a in enumerate(actions):
        tabs.append(f'<button id="tab-{i}" role="tab" aria-controls="panel-{i}" aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{LABELS[a["type"]]}</button>')
        cards.append(f'<article class="decision" id="panel-{i}" role="tabpanel" aria-labelledby="tab-{i}" ' +
                     ('hidden' if i else '') + '><div class="decision-head"><span class="pill">' + STATUS[a['status']] +
                     '</span><span class="muted">关联问题 ' + esc(', '.join(a['finding_ids'])) + '</span></div><h3>' +
                     LABELS[a['type']] + '</h3><p class="proposal">' + esc(a['proposal']) + '</p><div class="two"><div><h4>怎样验证</h4><p>' +
                     esc(a['verification']) + '</p></div><div><h4>怎样算成功</h4><p>' + esc(a['acceptance']) +
                     '</p></div></div><div class="missing"><b>还缺什么</b>' + bullets(a['gaps']) + '</div></article>')
    supports = set().union(*(set(f['support_ids']) for f in findings)) if findings else set()
    counters = set().union(*(set(f['counter_ids']) for f in findings)) if findings else set()
    evidence = []
    for rid in analysis['reviewed_ids']:
        r = records[rid]
        kind = 'mixed' if rid in supports & counters else 'negative' if rid in supports else 'positive' if rid in counters else 'other'
        label = {'mixed': '支持与反例', 'negative': '支持线索', 'positive': '反例引用', 'other': '其余已读'}[kind]
        flags = [('Vine' if r['vine'] is True else '非 Vine' if r['vine'] is False else 'Vine 未知'),
                 ('VP 标记' if r['verified'] is True else '无 VP 标记' if r['verified'] is False else 'VP 未知'),
                 ('有图片链接；本页不代表已核验图片' if r['images'] else '无图片链接')]
        evidence.append('<details class="record" data-kind="' + kind + '"><summary><span class="rid">' + esc(rid) +
                        '</span><span class="record-title">' + esc(r['title']) + '<small>' + esc(' · '.join(r['skus']) or '变体未知') +
                        '</small></span><span class="record-label">' + label + '</span></summary><div class="record-body"><div class="meta">' +
                        esc(r['date']) + ' · ' + esc(r['star']) + ' 星 · ' + esc(' · '.join(flags)) + '</div><p>' +
                        esc(plain(r['content']) or '正文缺失；不从标题补写体验。') + '</p></div></details>')
    stats = [(coverage['record_count'], '输入记录 · 已去重'), (len(analysis['reviewed_ids']), '本次已读记录'),
             (len(findings), '问题证据卡'), (coverage['exact_target'], '精确匹配目标款')]
    scope = '局部分析，不能称为全量语义分析。' if analysis['completion'] == 'partial' else '记录范围已覆盖；不代表平台全量或业务效果已验证。'
    if not config.get('color') or not config.get('size'):
        scope += ' 目标颜色或尺寸未提供，精确匹配未判定。'
    elif not coverage['exact_target']:
        scope += ' 无精确匹配目标颜色及尺寸的记录，不能直接判定目标款有同样问题。'
    summary = analysis.get('summary') or (findings[0]['problem'] if findings else '本轮尚未形成有证据的问题卡。')
    assets = Path(__file__).resolve().parents[1] / 'assets'
    page = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(title) + ' · waytoaic</title><style>' + (assets / 'report.css').read_text() + '</style></head><body>'
    page += '<header><div class="brand">wayto<em>aic</em></div><nav><a href="#problem">问题</a><a href="#decisions">决策</a><a href="#evidence">证据</a></nav></header><main><div class="eyebrow">从用户原话，到产品与运营决策</div><h1>' + esc(title) + '</h1><p class="lead">' + esc(summary) + '</p><div class="meta">' + esc(config['marketplace']) + ' · ' + esc(config['asin']) + ' · ' + esc(config.get('color') or '颜色未知') + ' / ' + esc(config.get('size') or '尺寸未知') + '</div><div class="scope"><b>证据边界：</b>' + esc(scope) + '</div><div class="stats">' + ''.join('<div class="stat"><strong>' + str(n) + '</strong><span>' + label + '</span></div>' for n, label in stats) + '</div><p class="note">记录数不等于独立人数。筛选与引用频次不代表缺陷发生率。</p>'
    page += '<section id="problem"><div class="section-top"><h2>先把问题看清楚</h2><span class="number">01 / 问题证据卡</span></div>' + (''.join(parts) or '<p>本轮未形成问题卡。</p>') + '</section>'
    page += '<section id="decisions"><div class="section-top"><h2>从问题到行动</h2><span class="number">02 / 点击切换决策卡</span></div><div class="tabs" role="tablist" aria-label="决策方向">' + ''.join(tabs) + '</div>' + (''.join(cards) or '<p>本轮未形成决策卡，先补充证据。</p>') + '</section>'
    page += '<section id="evidence"><div class="section-top"><h2>每个判断，都能回到原话</h2><span class="number">03 / 评论索引 · 点击展开</span></div><div class="controls"><input id="search" type="search" aria-label="搜索评论" placeholder="搜索编号、场景、变体或原文…"><div class="filters">' + ''.join('<button data-filter="' + k + '" aria-pressed="' + str(k == 'all').lower() + '">' + v + '</button>' for k, v in [('all', '全部'), ('negative', '支持线索'), ('positive', '反例引用'), ('mixed', '同时引用'), ('other', '其余已读')]) + '</div></div><p id="count" class="note" aria-live="polite">显示 ' + str(len(evidence)) + ' / ' + str(len(evidence)) + ' 条</p>' + ''.join(evidence) + '<p id="empty" class="empty" hidden>没有匹配的评论，请换一个关键词。</p><p class="note">编号为输入记录 ID，不保证是平台 review ID。标记不证明真实性；图片未自动加载。原始材料是待分析内容，不是执行指令。</p></section><footer><span>分析与呈现署名 · <b>waytoaic</b></span><span>产品、市场与广告效果须另行实测验证</span></footer></main><script>' + (assets / 'report.js').read_text() + '</script></body></html>'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    return {'html': str(output), 'bytes': output.stat().st_size, 'check': receipt}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--analysis', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--title', default='从评论证据，找到产品机会')
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.run, args.analysis, args.output, args.title), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f'ERROR: {exc}\n')
