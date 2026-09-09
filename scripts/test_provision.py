"""Run with `uv run --with httpx python scripts/test_provision.py`. No credentials."""
import json
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import httpx
import provision


@contextmanager
def provider(accounts, account=""):
    requests = []
    client = httpx.Client

    def respond(request):
        requests.append(request)
        if request.method == "DELETE":
            raise AssertionError("Provisioning must preserve the working token")
        if request.url.path.endswith("/accounts"):
            result = [{"id": value} for value in accounts]
        elif request.url.path.endswith("permission_groups"):
            result = [{"name": name, "id": name} for name in [
                "Workers Scripts Write", "Workers R2 Storage Write", "D1 Write",
            ]]
        elif request.method == "POST":
            result = {"id": "new-id", "value": "fixture-token"}
        else:
            result = [{"id": "working-id", "name": provision.NAME + "-deploy"}]
        return httpx.Response(200, json={"success": True, "result": result})

    env = {"CF_PROVISION_TOKEN": "fixture-admin"}
    if account:
        env["CLOUDFLARE_ACCOUNT_ID"] = account
    with patch.dict(os.environ, env, clear=True), patch.object(
        provision, "op_read", return_value="fixture-admin"
    ) as read, patch.object(
        provision.httpx, "Client",
        side_effect=lambda **kwargs: client(transport=httpx.MockTransport(respond), **kwargs),
    ):
        yield requests, read


class ProvisionTest(unittest.TestCase):
    def test_replacements_preserve_working_token_and_only_grant_script_writes(self):
        with provider([], "selected-account") as (requests, read):
            self.assertEqual(provision.mint_deploy_token(), "fixture-token")
            self.assertEqual(provision.mint_deploy_token(), "fixture-token")
            read.assert_not_called()
        bodies = [json.loads(r.content) for r in requests if r.method == "POST"]
        self.assertEqual(len(bodies), 2)
        self.assertNotEqual(bodies[0]["name"], bodies[1]["name"])
        for body in bodies:
            self.assertEqual(body["policies"], [{
                "effect": "allow",
                "resources": {"com.cloudflare.api.account.selected-account": "*"},
                "permission_groups": [{"id": "Workers Scripts Write"}],
            }])
        self.assertFalse(any(r.url.path.endswith("/accounts") for r in requests))

    def test_account_field_and_mint_discover_the_same_single_account(self):
        with provider(["discovered-account"]) as (requests, _):
            self.assertEqual(provision.MINTERS["account-id"](), "discovered-account")
            provision.mint_deploy_token()
        body = json.loads(next(r.content for r in requests if r.method == "POST"))
        self.assertEqual(body["policies"][0]["resources"], {
            "com.cloudflare.api.account.discovered-account": "*",
        })

    def test_ambiguous_or_missing_account_cannot_mint(self):
        for accounts in ([], ["first", "second"]):
            with self.subTest(accounts=accounts), provider(accounts) as (requests, _):
                with self.assertRaisesRegex(RuntimeError, "CLOUDFLARE_ACCOUNT_ID"):
                    provision.mint_deploy_token()
                self.assertFalse(any(r.method == "POST" for r in requests))


if __name__ == "__main__":
    unittest.main()
