import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent / "smoke"

class SmokeSafety(unittest.TestCase):
    def test_runner_never_kills_unrelated_enterprise_processes(self):
        script = (ROOT / "run_smoke.sh").read_text()
        self.assertNotIn('pkill -f "1cv8 ENTERPRISE"', script)

    def test_fixture_does_not_delete_existing_catalog_records(self):
        source = (ROOT / "autotest.bsl").read_text()
        self.assertNotIn('ОбъектУдаления.Удалить()', source)

    def test_runner_fails_on_build_or_test_error(self):
        script = (ROOT / "run_smoke.sh").read_text()
        self.assertIn('set -euo pipefail', script)
        self.assertIn('grep -q "АВТОТЕСТ ЗАВЕРШЕН"', script)
        self.assertIn('grep -q "ОШИБКА АВТОТЕСТА"', script)

if __name__ == "__main__":
    unittest.main()
