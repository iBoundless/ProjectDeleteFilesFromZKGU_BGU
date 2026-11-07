"""Integration check for the non-mutating namespace probe, not a 1C test."""
import pathlib
import subprocess
import unittest


class IsolationProbe(unittest.TestCase):
    def test_probe_confirms_no_network_or_host_database_paths(self):
        script = pathlib.Path(__file__).parent / 'isolation' / 'probe.sh'
        self.assertTrue(script.is_file(), 'missing isolation probe')
        result = subprocess.run(['bash', str(script)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('host_srv_absent=1', result.stdout)
        self.assertIn('non_loopback_routes=0', result.stdout)
        self.assertIn('host_socket_absent=1', result.stdout)

    def test_platform_creates_disposable_database_inside_isolation(self):
        script = pathlib.Path(__file__).parent / 'isolation' / 'platform_probe.sh'
        self.assertTrue(script.is_file(), 'missing isolated platform probe')
        result = subprocess.run(['bash', str(script)], capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('disposable_base_created=1', result.stdout)


if __name__ == '__main__':
    unittest.main()
