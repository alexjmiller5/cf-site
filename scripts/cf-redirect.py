#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Idempotent www -> apex redirect (declarative-via-script).

Installs ONE Cloudflare Single Redirect in the zone: `www.<zone>` 301s to
`<zone>`, path and query preserved. Re-runs converge; other rules in the phase
are kept.

  scripts/cf-redirect.py --zone example.com

One public origin is load-bearing, not cosmetic. Anything that derives a URL
from the request origin - an OAuth `redirect_uri`, a canonical tag, an
analytics distinct-id cookie - silently forks when www is served as a second
site, and OAuth providers refuse the callback outright. The rule runs in the
dynamic-redirect phase, before the Worker, so www never reaches app code.

Auth: CLOUDFLARE_API_TOKEN env var if set (needs Zone > Single Redirect >
Edit + Zone > Zone > Read on the zone), else the AI Agent Cloudflare API key
from 1Password (by ID).
"""

import argparse
import os
import subprocess
import sys

import httpx

API = "https://api.cloudflare.com/client/v4"
OP_TOKEN_REF = "op://4eeyrkqibibn7k4j6rz2fbzvxm/mxxpo6neiz3grdyrjj7rv7nume/credential"
PHASE = "http_request_dynamic_redirect"


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


def desired_rule(zone: str) -> dict:
    return {
        "action": "redirect",
        "action_parameters": {
            "from_value": {
                "status_code": 301,
                "target_url": {"expression": f'concat("https://{zone}", http.request.uri.path)'},
                "preserve_query_string": True,
            }
        },
        "expression": f'(http.host eq "www.{zone}")',
        "description": "www -> apex (one canonical origin)",
        "enabled": True,
    }


def plan(existing: list[dict], want: dict) -> list[dict] | None:
    """Rules to PUT, or None when a rule already expressing `want` is present.

    A stale version of our rule (same description, different body) is replaced;
    every other rule in the phase is kept as-is.
    """
    if any(all(r.get(k) == v for k, v in want.items()) for r in existing):
        return None
    return [want, *(r for r in existing if r.get("description") != want["description"])]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zone", required=True, help="apex hostname, e.g. example.com")
    args = ap.parse_args()

    c = httpx.Client(headers={"Authorization": f"Bearer {api_token()}"}, timeout=30)
    zones = unwrap(c.get(f"{API}/zones", params={"name": args.zone}))
    if not zones:
        sys.exit(f"zone {args.zone} not visible to this token")
    url = f"{API}/zones/{zones[0]['id']}/rulesets/phases/{PHASE}/entrypoint"

    r = c.get(url)
    # 404 = nothing has ever been created in this phase; the entrypoint appears on first PUT.
    existing = [] if r.status_code == 404 else unwrap(r).get("rules", [])
    rules = plan(existing, desired_rule(args.zone))
    if rules is None:
        print(f"www.{args.zone} -> {args.zone} already converged")
        return
    unwrap(c.put(url, json={"rules": rules}))
    print(f"redirecting www.{args.zone} -> {args.zone} (301)")


if __name__ == "__main__":
    main()
