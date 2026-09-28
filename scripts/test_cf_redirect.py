"""Run with `uv run --with httpx python scripts/test_cf_redirect.py`. No credentials."""
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("cf_redirect", pathlib.Path(__file__).with_name("cf-redirect.py"))
cf_redirect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf_redirect)

WANT = cf_redirect.desired_rule("example.com")
OTHER = {"action": "redirect", "expression": '(http.request.uri.path eq "/old")', "description": "legacy /old"}


class Plan(unittest.TestCase):
    def test_empty_phase_installs_the_rule(self):
        self.assertEqual(cf_redirect.plan([], WANT), [WANT])

    def test_converged_rule_is_a_no_op(self):
        stored = {**WANT, "id": "abc", "version": "3", "last_updated": "now"}
        self.assertIsNone(cf_redirect.plan([stored, OTHER], WANT))

    def test_stale_copy_is_replaced_and_others_kept(self):
        stale = {**WANT, "action_parameters": {"from_value": {"status_code": 302}}}
        self.assertEqual(cf_redirect.plan([OTHER, stale], WANT), [WANT, OTHER])

    def test_rule_shape(self):
        self.assertEqual(WANT["expression"], '(http.host eq "www.example.com")')
        self.assertTrue(WANT["action_parameters"]["from_value"]["preserve_query_string"])
        self.assertEqual(WANT["action_parameters"]["from_value"]["status_code"], 301)


if __name__ == "__main__":
    unittest.main()
