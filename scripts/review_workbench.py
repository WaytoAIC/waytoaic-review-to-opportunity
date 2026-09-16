#!/usr/bin/env python3
"""Local review preparation and evidence-reference checks. Author: waytoaic."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def normalize(value):
    value = str(value or '').lower().replace('×', 'x')
    value = value.translate(str.maketrans({'‘': "'", '’': "'", '′': "'", '＇': "'"}))
    return re.sub(r'\s+', '', value)


def variant(row):
    result = {}
    for item in row.get('skus') or []:
        key, sep, value = item.partition(':')
        if sep:
            result[key.strip().lower()] = normalize(value)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def prepare(source, output, asin, marketplace, color=None, size=None):
    source, output = Path(source), Path(output)
    raw = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
    require(raw, 'input is empty')
    normalized, aliases, ids = {}, {}, {}
    for index, item in enumerate(raw, 1):
        require(isinstance(item, dict), f'row {index}: expected object')
        for field in ('verified', 'vine'):
            require(item.get(field) is None or type(item[field]) is bool,
                    f'row {index}: {field} must be boolean or null')
        for field in ('title', 'content', 'date'):
            require(item.get(field) is None or isinstance(item[field], str),
                    f'row {index}: {field} must be text or null')
        for field in ('skus', 'images'):
            require(item.get(field) is None or (isinstance(item[field], list) and
                    all(isinstance(x, str) for x in item[field])), f'row {index}: invalid {field}')
        key = digest([item.get('date'), item.get('title'), item.get('content'), sorted(item.get('skus') or [])])
        rid = item.get('id') or 'R' + key[:16]
        require(isinstance(rid, str) and rid.strip(), f'row {index}: invalid id')
        require(rid not in ids or ids[rid] == key, f'conflicting id: {rid}')
        ids[rid] = key
        if key in normalized:
            prior = normalized[key]
            for field in ('verified', 'vine', 'star', 'source_review_id'):
                if item.get(field) is not None and prior.get(field) is not None:
                    require(item[field] == prior[field], f'duplicate conflicting {field}: {rid}')
                elif prior.get(field) is None and item.get(field) is not None:
                    prior[field] = item[field]
            prior['images'] = sorted(set(prior['images'] + (item.get('images') or [])))
            aliases[rid] = prior['id']
            continue
        row = {k: item.get(k) for k in ('title', 'content', 'date', 'star', 'verified', 'vine', 'source_url', 'source_review_id')}
        row.update(id=rid, skus=item.get('skus') or [], images=item.get('images') or [])
        attrs = variant(row)
        row['target_match'] = ('exact' if attrs.get('color') == normalize(color) and
                               attrs.get('size') == normalize(size) else 'other_or_unknown') if color and size else 'unknown'
        normalized[key] = row
    records = list(normalized.values())
    config = dict(asin=asin, marketplace=marketplace, color=color, size=size)
    fingerprint = digest(dict(raw=raw, config=config))
    manifest = output / 'coverage.json'
    if output.exists():
        require(manifest.exists(), 'output already exists without manifest; choose a fresh run directory')
        previous = json.loads(manifest.read_text())
        require(previous['input_fingerprint'] == fingerprint, 'different input/config: choose a new run directory')
        expected = previous.get('artifact_hashes', {})
        require(expected, 'missing artifact hashes')
        for name, sha in expected.items():
            f = output / name
            require(f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() == sha,
                    f'prepared artifact changed/missing: {name}; choose a new run directory')
        return previous
    output.mkdir(parents=True)
    (output / 'batches').mkdir()
    (output / 'reviews.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    artifacts = ['reviews.jsonl']
    for n, start in enumerate(range(0, len(records), 20), 1):
        name = f'batches/batch_{n:03d}.json'
        (output / name).write_text(json.dumps(records[start:start + 20], ensure_ascii=False, indent=2), encoding='utf-8')
        artifacts.append(name)
    coverage = dict(author='waytoaic', input_count=len(raw), record_count=len(records),
                    missing_body=sum(not (r['content'] or '').strip() for r in records),
                    exact_target=sum(r['target_match'] == 'exact' for r in records),
                    vine=sum(r['vine'] is True for r in records),
                    images_available=sum(bool(r['images']) for r in records),
                    independent_people=None, identity_dedup_verified=False,
                    config=config, aliases=aliases, input_fingerprint=fingerprint,
                    artifact_hashes={name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in artifacts})
    manifest.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding='utf-8')
    return coverage


def nonempty(obj, fields, label):
    for field in fields:
        require(isinstance(obj.get(field), str) and obj[field].strip(), f'{label}: missing {field}')


def list_field(obj, field):
    require(isinstance(obj.get(field), list), f'{field} must be a list')
    return obj[field]


def check(run, analysis):
    run = Path(run)
    coverage = json.loads((run / 'coverage.json').read_text())
    for name, sha in coverage['artifact_hashes'].items():
        f = run / name
        require(f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() == sha,
                f'prepared artifact changed/missing: {name}')
    records = {r['id']: r for r in map(json.loads, (run / 'reviews.jsonl').read_text().splitlines())}
    data = json.loads(Path(analysis).read_text(encoding='utf-8'))
    require(data.get('author') == 'waytoaic', 'author must be waytoaic')
    reviewed = list_field(data, 'reviewed_ids')
    require(all(isinstance(x, str) for x in reviewed), 'reviewed ids must be strings')
    require(len(reviewed) == len(set(reviewed)), 'duplicate reviewed id')
    require(set(reviewed) <= records.keys(), 'unknown reviewed id')
    require(data.get('completion') in ('partial', 'complete'), 'invalid completion')
    if data['completion'] == 'complete':
        require(set(reviewed) == records.keys(), 'complete requires every record reviewed')
    finding_ids = set()
    for finding in list_field(data, 'findings'):
        nonempty(finding, ('id', 'problem', 'people', 'scene', 'need', 'solution', 'confidence_reason', 'next_test'), 'finding')
        fid = finding['id']
        require(fid not in finding_ids, 'duplicate finding id')
        finding_ids.add(fid)
        support, counter = list_field(finding, 'support_ids'), list_field(finding, 'counter_ids')
        for values in (support, counter):
            require(all(isinstance(x, str) for x in values) and len(values) == len(set(values)), 'invalid/duplicate reference')
            require(set(values) <= set(reviewed), 'finding references an unreviewed or unknown id')
        # A nuanced review may support one claim and oppose another; overlap is permitted.
        require(support, 'finding needs support; put unsupported ideas in gaps')
        applicability = finding.get('applicability')
        require(applicability in ('target', 'related', 'unknown'), 'invalid applicability')
        if applicability == 'target':
            require(any(records[x]['target_match'] == 'exact' for x in support), 'target finding needs exact variant evidence')
        status = finding.get('status')
        require(status in ('insufficient', 'hypothesis', 'business_confirmed'), 'invalid finding status')
        if status == 'business_confirmed':
            nonempty(finding, ('human_confirmation',), 'business confirmation')
        for quote in list_field(finding, 'quotes'):
            rid, text = quote.get('review_id'), quote.get('text')
            require(rid in support + counter, 'quote must reference supporting/counter record')
            require(isinstance(text, str) and text.strip(), 'empty quote')
            row = records[rid]
            require(text in (row['content'] or '') or text in (row['title'] or ''), 'quote not found verbatim')
        list_field(finding, 'gaps')
    types = {'new_product', 'product_iteration', 'listing', 'search_terms', 'asin_targeting'}
    for action in list_field(data, 'actions'):
        require(action.get('type') in types, 'invalid action type')
        require(action.get('status') in ('blocked', 'hypothesis', 'test_plan'), 'invalid action status')
        refs = list_field(action, 'finding_ids')
        require(refs and all(isinstance(x, str) for x in refs) and set(refs) <= finding_ids, 'unknown/missing finding')
        nonempty(action, ('proposal', 'verification', 'acceptance'), 'action')
        list_field(action, 'gaps')
    return dict(author='waytoaic', structural_check='passed', reviewed=len(reviewed),
                total=len(records), completion=data['completion'], findings=len(finding_ids),
                actions=len(data['actions']), semantic_and_business_validation='not_performed_by_script')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for flag in ('input', 'output', 'asin', 'marketplace'):
        prep.add_argument('--' + flag, required=True)
    prep.add_argument('--color')
    prep.add_argument('--size')
    ck = sub.add_parser('check')
    ck.add_argument('--run', required=True)
    ck.add_argument('--analysis', required=True)
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        if command == 'prepare':
            args['source'] = args.pop('input')
            result = prepare(**args)
        else:
            result = check(**args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
