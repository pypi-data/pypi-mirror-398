import os
import random

from gatling.utility.io_fctns import save_jsonl, read_jsonl

K_proxy = 'proxy'
K_success = 'success'
K_failure = 'failure'
K_total = 'total'
K_srate = 'srate'


class ProxyManager:
    @staticmethod
    def proxy2info_to_proxyinfos(proxy2info):
        proxyinfos = []
        for proxy, info in proxy2info.items():
            success = info['success']
            failure = info['failure']
            total = failure + success
            srate = round(success / total, 4) if total > 0 else 0
            proxyinfo = {K_proxy: proxy, K_total: total, K_success: success, K_failure: failure, K_srate: srate}
            proxyinfos.append(proxyinfo)
        proxyinfos = sorted(proxyinfos, key=lambda x: x[K_success], reverse=True)
        return proxyinfos

    @staticmethod
    def proxyinfos_to_proxy2info(proxyinfos):
        proxy2info = {}
        for proxyinfo in proxyinfos:
            proxy = proxyinfo[K_proxy]
            success = proxyinfo[K_success]
            failure = proxyinfo[K_failure]
            proxy2info[proxy] = {K_success: success, K_failure: failure}
        return proxy2info

    def __init__(self, fpath_proxyinfos_jsonl):
        self.fpath_proxyinfo_jsonl = fpath_proxyinfos_jsonl
        if os.path.exists(self.fpath_proxyinfo_jsonl):
            proxyinfos = read_jsonl(self.fpath_proxyinfo_jsonl)
            self.proxy2info = ProxyManager.proxyinfos_to_proxy2info(proxyinfos)
        else:
            self.proxy2info = {}

    def initialize(self, proxies):
        proxyinfos = [{K_proxy: proxy, K_success: 0, K_failure: 0} for proxy in proxies]
        self.proxy2info = ProxyManager.proxyinfos_to_proxy2info(proxyinfos)
        print(f"initialized {len(self.proxy2info)} proxies")

    def inc_success(self, proxy):
        if proxy not in self.proxy2info:
            self.proxy2info[proxy] = {K_success: 0, K_failure: 0}
        self.proxy2info[proxy][K_success] += 1

    def inc_failure(self, proxy):
        if proxy not in self.proxy2info:
            self.proxy2info[proxy] = {K_success: 0, K_failure: 0}
        self.proxy2info[proxy][K_failure] += 1

    def save(self):
        proxyinfos = ProxyManager.proxy2info_to_proxyinfos(self.proxy2info)
        save_jsonl(proxyinfos, self.fpath_proxyinfo_jsonl)

    def rand_ts_proxy_for_aiohttp(self):
        # thompson sampling
        proxy_theta_s = [[proxy, random.betavariate(info[K_success] + 1, info[K_failure] + 1)] for proxy, info in self.proxy2info.items()]
        selected_proxy_theta = max(proxy_theta_s, key=lambda x: x[1])
        selected_proxy = selected_proxy_theta[0]
        return selected_proxy

    def rand_wt_proxy_for_aiohttp(self):
        # Weighted Random Sampling
        proxies = []
        weights = []
        for proxy, info in self.proxy2info.items():
            success = info[K_success] + 1
            failure = info[K_failure] + 1
            total = failure + success
            srate = success / total
            proxies.append(proxy)
            weights.append(srate)

        return random.choices(proxies, weights=weights)[0]


if __name__ == '__main__':
    pass
    """
    proxyinfos = read_json(os.path.join(preset.dpath_base_asset, 'data.http.json'))

    proxies = [pxinfo['proxy'] for pxinfo in proxyinfos]

    fpath_proxyinfo = os.path.join(preset.dpath_base_asset, 'proxyinfos.http.jsonl')
    pm = ProxyManager(fpath_proxyinfo)
    pm.initialize(proxies)
    pm.save()

    for i in range(100):
        print(pm.rand_ts_proxy_for_aiohttp())
    """
