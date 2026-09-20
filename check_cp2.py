import csv
import re
from pathlib import Path

for folder_name in ['data/exchange_policy', 'data/ecommerce', 'exchange_policy']:
    D = Path(folder_name)
    if not D.exists():
        continue
    print(f"=== CHECKING {folder_name} ===")
    REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience']
    mds = sorted(D.glob('*.md'))
    rows = list(csv.DictReader(open(D / 'sources.csv', encoding='utf-8')))
    ids = []
    auds = {}
    for p in mds:
        content = p.read_text(encoding='utf-8')
        parts = content.split('---')
        if len(parts) >= 3:
            fm = dict(re.findall(r'^(\w+):\s*(.+)$', parts[1], re.M))
            fm = {k: v.strip().strip('"\'') for k, v in fm.items()}
        else:
            fm = {}
        ids.append(fm.get('doc_id'))
        aud = fm.get('audience')
        auds[aud] = auds.get(aud, 0) + 1
        is_ok = all(k in fm for k in REQ) and fm.get('doc_id') == p.stem
        status = "OK" if is_ok else "THIEU METADATA"
        print(f"{p.name:45} {status}")

    print("so file :", len(mds), "(can 5-10)")
    csv_match = "khop" if sorted(r['doc_id'] for r in rows) == sorted(ids) else "LECH"
    print("csv     :", csv_match)
    print("audience:", auds, "(can ca buyer va seller)")
    print()
