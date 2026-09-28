"""Run with `uv run --with httpx python scripts/test_cf_queues.py`. No credentials."""
import importlib.util
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("cf_queues", pathlib.Path(__file__).with_name("cf-queues.py"))
cf_queues = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf_queues)


def declared(jsonc: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonc", delete=False) as f:
        f.write(jsonc)
    return cf_queues.declared_queues(pathlib.Path(f.name))


class DeclaredQueues(unittest.TestCase):
    def test_producers_consumers_and_dead_letter_queues_in_declaration_order(self):
        cfg = """{
          // comments and trailing commas are legal in wrangler.jsonc
          "queues": {
            "producers": [{ "binding": "JOBS", "queue": "jobs" },],
            "consumers": [
              { "queue": "jobs", "dead_letter_queue": "jobs-dlq" },
              { "queue": "emails" },
            ],
          },
        }"""
        self.assertEqual(declared(cfg), ["jobs", "jobs-dlq", "emails"])

    def test_no_queues_declared(self):
        self.assertEqual(declared('{ "name": "site" }'), [])

    def test_wrangler_toml_is_read_too(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('[[queues.consumers]]\nqueue = "essay-extraction-queue"\ndead_letter_queue = "essay-extraction-dlq"\n')
        self.assertEqual(
            cf_queues.declared_queues(pathlib.Path(f.name)),
            ["essay-extraction-queue", "essay-extraction-dlq"],
        )


class Plan(unittest.TestCase):
    def test_only_missing_queues_are_created(self):
        self.assertEqual(cf_queues.missing(["jobs", "jobs-dlq", "emails"], {"jobs"}), ["jobs-dlq", "emails"])


if __name__ == "__main__":
    unittest.main()
