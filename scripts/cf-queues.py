#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Idempotent Cloudflare Queues provisioner (declarative-via-script).

The wrangler config is the declaration: this script reads every queue named
under `queues.producers`, `queues.consumers` and their `dead_letter_queue`s
and creates any that don't exist yet. Re-running converges; it never deletes.

`wrangler deploy` does NOT create queues - it fails with "Queue X does not
exist" - so a deleted queue breaks the next deploy until this is re-run.

  scripts/cf-queues.py                 ensure every declared queue exists
  scripts/cf-queues.py --dry-run       print the plan, change nothing
  scripts/cf-queues.py --parse-only    just print the queue names found in config

Reads wrangler.jsonc by default; a `.toml` path works too.

Auth: CLOUDFLARE_API_TOKEN env var if set (needs Account > Workers Queues:
Edit), else the AI Agent Cloudflare API key from 1Password (by ID).
Account: CLOUDFLARE_ACCOUNT_ID env var, else the token's sole visible account.
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tomllib

import httpx

API = "https://api.cloudflare.com/client/v4"
OP_TOKEN_REF = "op://4eeyrkqibibn7k4j6rz2fbzvxm/mxxpo6neiz3grdyrjj7rv7nume/credential"


def api_token() -> str:
    if tok := os.environ.get("CLOUDFLARE_API_TOKEN"):
        return tok
    return subprocess.run(
        ["op", "read", OP_TOKEN_REF], capture_output=True, text=True, check=True
    ).stdout.strip()


def unwrap(r: httpx.Response) -> dict | list:
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        sys.exit(f"Cloudflare API error: {body.get('errors')}")
    return body["result"]


def strip_jsonc(text: str) -> str:
    """JSONC -> JSON: drop // and /* */ comments (string-safe) + trailing commas."""
    out, i, n = [], 0, len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
            out.append(ch)
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i = text.find("*/", i + 2)
            if i == -1:
                break
            i += 2
            continue
        else:
            out.append(ch)
        i += 1
    cleaned, j = [], 0
    s = "".join(out)
    while j < len(s):
        if s[j] == ",":
            k = j + 1
            while k < len(s) and s[k] in " \t\r\n":
                k += 1
            if k < len(s) and s[k] in "}]":
                j += 1
                continue
        cleaned.append(s[j])
        j += 1
    return "".join(cleaned)


def declared_queues(config: pathlib.Path) -> list[str]:
    if config.suffix == ".toml":
        cfg = tomllib.loads(config.read_text())
    else:
        cfg = json.loads(strip_jsonc(config.read_text()))
    queues = cfg.get("queues", {})
    names: list[str] = []
    for entry in [*queues.get("producers", []), *queues.get("consumers", [])]:
        for key in ("queue", "dead_letter_queue"):
            if (name := entry.get(key)) and name not in names:
                names.append(name)
    return names


def missing(wanted: list[str], existing: set[str]) -> list[str]:
    return [q for q in wanted if q not in existing]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "wrangler.jsonc",
    )
    ap.add_argument("--parse-only", action="store_true", help="print declared queue names, no API")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    args = ap.parse_args()

    wanted = declared_queues(args.config)
    if args.parse_only:
        print("\n".join(wanted) or "(no queues declared)")
        return
    if not wanted:
        print(f"no queues declared in {args.config} - nothing to do")
        return

    c = httpx.Client(headers={"Authorization": f"Bearer {api_token()}"}, timeout=30)

    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account:
        accounts = unwrap(c.get(f"{API}/accounts"))
        if len(accounts) != 1:
            sys.exit("Multiple accounts visible - set CLOUDFLARE_ACCOUNT_ID")
        account = accounts[0]["id"]

    existing = {q["queue_name"] for q in unwrap(c.get(f"{API}/accounts/{account}/queues"))}
    for name in wanted:
        if name in existing:
            print(f"'{name}' already converged")
    for name in missing(wanted, existing):
        if args.dry_run:
            print(f"WOULD CREATE queue '{name}'")
        else:
            unwrap(c.post(f"{API}/accounts/{account}/queues", json={"queue_name": name}))
            print(f"created queue '{name}'")


if __name__ == "__main__":
    main()
