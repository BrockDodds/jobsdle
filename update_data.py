"""Refresh the Jobsdle data array in index.html from the BLS public API.

Fetches the last 10 years of each series in one request (BLS API v1, no key),
recomputes every month it can, and rewrites the `const ALL = [...]` line.
Older months already in the file are kept as they are.

Set BLS_API_KEY to use API v2 (higher daily limits); it is optional.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
SERIES = ["CES0000000001", "LNS14000000", "CUSR0000SA0", "LNS11300000", "CES0500000008", "CES3000000001"]
LINE = re.compile(r"^const ALL = (\[.*\]);$", re.M)


def fetch(start, end):
    key = os.environ.get("BLS_API_KEY")
    body = {"seriesid": SERIES, "startyear": str(start), "endyear": str(end)}
    url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    if key:
        body["registrationkey"] = key
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    if res.get("status") != "REQUEST_SUCCEEDED":
        sys.exit(f"BLS request failed: {res.get('status')} {res.get('message')}")
    out = {}
    for s in res["Results"]["series"]:
        for p in s["data"]:
            if p["period"] == "M13" or p["value"] in ("-", ""):
                continue
            out.setdefault(s["seriesID"], {})[(int(p["year"]), int(p["period"][1:]))] = float(p["value"])
    missing = [s for s in SERIES if s not in out]
    if missing:
        sys.exit(f"BLS response is missing series {missing}")
    return out


def prev(k, n=1):
    y, m = k
    m -= n
    while m < 1:
        m += 12
        y -= 1
    return (y, m)


def rows_from(d):
    N, U, C, L, W, M = (d[s] for s in SERIES)

    def g(f):
        try:
            return f()
        except KeyError:
            return None

    rows = {}
    for k in sorted(N):
        if prev(k) not in N:
            continue
        rows[k] = [k[0], k[1], round(N[k] - N[prev(k)])] + [g(f) for f in (
            lambda: U[k],
            lambda: round((C[k] / C[prev(k, 12)] - 1) * 100, 1),
            lambda: round((C[k] / C[prev(k)] - 1) * 100, 1),
            lambda: L[k],
            lambda: round((W[k] / W[prev(k, 12)] - 1) * 100, 1),
            lambda: round(M[k] - M[prev(k)]),
            lambda: round(N[prev(k)] - N[prev(k, 2)]) if prev(k, 2) in N else None,
            lambda: round(U[k] - U[prev(k)], 1),
        )]
    return rows


def main():
    html = open(INDEX, encoding="utf-8").read()
    m = LINE.search(html)
    if not m:
        sys.exit("Could not find the `const ALL = [...]` line in index.html")
    existing = {(r[0], r[1]): r for r in json.loads(m.group(1))}

    year = datetime.now(timezone.utc).year
    fresh = rows_from(fetch(year - 9, year))
    # The first fetched year lacks the prior-year values its 12-month changes need,
    # so only replace months from the second year on.
    cutoff = (year - 8, 1)
    merged = dict(existing)
    for k, r in fresh.items():
        if k >= cutoff:
            merged[k] = r

    rows = [merged[k] for k in sorted(merged)]
    added = sorted(set(merged) - set(existing))
    changed = [k for k in existing if merged[k] != existing[k]]
    if not added and not changed:
        print("No new or revised data.")
        return

    new_line = "const ALL = " + json.dumps(rows, separators=(",", ":")) + ";"
    html = html[:m.start()] + new_line + html[m.end():]
    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"Added {len(added)} month(s): {[f'{y}-{mo:02d}' for y, mo in added]}")
    print(f"Revised {len(changed)} month(s).")


if __name__ == "__main__":
    main()
