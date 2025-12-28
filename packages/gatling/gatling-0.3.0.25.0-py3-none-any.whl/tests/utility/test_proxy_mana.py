import unittest
import os
import tempfile
from gatling.utility.proxy_mana import ProxyManager
from gatling.utility.io_fctns import read_json, save_json


class TestProxyManager(unittest.TestCase):
    """Test the initialization, saving, and random proxy functionality of ProxyManager"""

    def setUp(self):
        # Create a temporary directory
        self.tempdir = tempfile.TemporaryDirectory()
        self.dpath_base_asset = self.tempdir.name

        # Create a mock data.http.json file
        self.http_json_path = os.path.join(self.dpath_base_asset, 'data.http.json')
        proxyinfos = [
            {'proxy': 'http://proxy1.example.com:8080'},
            {'proxy': 'http://proxy2.example.com:8080'}
        ]
        save_json(proxyinfos, self.http_json_path)  # Use your own save_json()

        # Mock a preset object
        class Preset:
            pass

        self.preset = Preset()
        self.preset.dpath_base_asset = self.dpath_base_asset

    def tearDown(self):
        # Automatically clean up the temporary directory
        self.tempdir.cleanup()

    def test_proxy_manager_workflow(self):
        """Test the full workflow of ProxyManager"""
        # Read data.http.json (use your own read_json)
        proxyinfos = read_json(self.http_json_path)
        proxies = [pxinfo['proxy'] for pxinfo in proxyinfos]

        # Initialize ProxyManager
        fpath_proxyinfo = os.path.join(self.preset.dpath_base_asset, 'proxyinfos.http.jsonl')
        pm = ProxyManager(fpath_proxyinfo)
        pm.initialize(proxies)
        pm.save()

        # Verify that the file was saved successfully
        self.assertTrue(os.path.exists(fpath_proxyinfo), "proxyinfos.http.jsonl file not created")

        # Verify that random proxies are valid
        for _ in range(10):
            proxy = pm.rand_ts_proxy_for_aiohttp()
            self.assertIn(proxy, proxies, f"Returned proxy {proxy} not in initialization list")

        print("\n ProxyManager test passed")


if __name__ == '__main__':
    unittest.main(verbosity=2)
