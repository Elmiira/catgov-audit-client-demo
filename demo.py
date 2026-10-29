#!/usr/bin/env python3
"""
data-catalog-governance-service audit API demo client.

Usage:
    python demo.py \
        --host https://catalog-governance.prd-dev.data.unity3d.com \
        --table unity-data-prd.attribution.secondary_conversion_session_v1 \
        --partition 2026-10-28 \
        --token <bearer-token>
"""

import argparse
import json
import sys
import time

import requests

DEFAULT_HOST = "https://catalog-governance.prd-dev.data.unity3d.com"
POLL_INTERVAL_S = 10
MAX_WAIT_S = 3600


def build_session(token: str | None) -> requests.Session:
    s = requests.Session()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Content-Type"] = "application/json"
    return s


def submit_audit(session, host, table_fqn, partition_date):
    url = f"{host}/audit/table"
    payload = {"tableFqn": table_fqn, "partitionDate": partition_date}
    print(f"POST {url}")
    print(f"  payload: {json.dumps(payload)}")
    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    job_id = resp.json()["jobId"]
    print(f"  → 202 Accepted  jobId={job_id}\n")
    return job_id


def poll_until_done(session, host, job_id):
    url = f"{host}/audit/{job_id}"
    deadline = time.monotonic() + MAX_WAIT_S
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        status = body.get("status", "UNKNOWN")
        print(f"  [{attempt:>3}] {url}  →  status={status}")
        if status == "DONE":
            print()
            return body
        if status not in ("RUNNING", "PENDING"):
            print(f"\nUnexpected status: {status}", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_S)
    print(f"Timed out after {MAX_WAIT_S}s", file=sys.stderr)
    sys.exit(1)


def print_results(result):
    r = result.get("results", {})
    print("=" * 60)
    print("Audit complete")
    print("=" * 60)
    print(f"  Table      : {result.get('tableFqn', 'n/a')}")
    print(f"  Partition  : {result.get('partitionDate', 'n/a')}")
    print(f"  Score      : {r.get('score', 'n/a')}  Grade: {r.get('grade', 'n/a')}")
    print(f"  Readiness  : {r.get('readiness', 'n/a')}")
    print(f"  Checks     : {r.get('pass', 0)} pass / {r.get('warn', 0)} warn / {r.get('fail', 0)} fail")
    print(f"  Issues     : P0={r.get('p0', 0)}  P1={r.get('p1', 0)}  P2={r.get('p2', 0)}")
    print()
    for label, key in [
        ("Summary ", "summaryReportUrl"),
        ("Glossary", "glossaryReportUrl"),
        ("DQ      ", "dqReportUrl"),
        ("Issue   ", "issueUrl"),
    ]:
        url = result.get(key)
        if url:
            print(f"  {label}: {url}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Demo client for the catalog governance audit API.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--table", default="unity-data-prd.attribution.secondary_conversion_session_v1")
    parser.add_argument("--partition", default=time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)))
    parser.add_argument("--token", default=None, help="Bearer token (omit when using mTLS)")
    args = parser.parse_args()

    session = build_session(args.token)
    job_id = submit_audit(session, args.host, args.table, args.partition)
    print(f"Polling every {POLL_INTERVAL_S}s …")
    result = poll_until_done(session, args.host, job_id)
    print_results(result)


if __name__ == "__main__":
    main()
