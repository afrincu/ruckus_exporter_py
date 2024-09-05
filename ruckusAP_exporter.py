#!/usr/bin/python
"""
Service to export data from Ruckus Wifi controller
"""

import time
import os
import sys

from prometheus_client import start_http_server
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, REGISTRY
from RuckusVirtualSmartZoneExporter import Exporter

if 'VSZ_USERNAME' not in os.environ or 'VSZ_PASSWORD' not in os.environ:
    print("Envionment variables VSZ_USERNAME or VSZ_PASSWORD are not defined")
    sys.exit(1)
vszHostname = os.environ['VSZ_HOSTNAME'] if 'VSZ_HOSTNAME' in os.environ else 'localhost'
vszUsername = os.environ['VSZ_USERNAME']
vszPassword = os.environ['VSZ_PASSWORD']

class RuckusCollector(object):
    """
    Object Class to collect Ruckus data
    """
    def __init__(self):
        self.controllers = [
            {"hostname": "controller1.example.com", "username": "user1", "password": "pass1"},
            {"hostname": "controller2.example.com", "username": "user2", "password": "pass2"},
            # Add more controller configurations as needed
        ]

    def collect(self):
        """Service that collect the data
        """
        for controller in self.controllers:
            vszExporter = Exporter(hostname=controller["hostname"])
            if not vszExporter.login(username=controller["username"], password=controller["password"]):
                continue  # Skip to the next controller if login fails

            # Retrieve datas
            aps = vszExporter.getAPs()
            ssids = vszExporter.getSSIDs()
            controller_info = vszExporter.getControllerInfo()

            vszExporter.logout()

            ap_metrics = {
                'tx': GaugeMetricFamily(name="ap_tx", documentation="AP Transmit", labels=["ap","apMac","apGroup","apZone"]),
                'rx': GaugeMetricFamily(name="ap_rx", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'numClients5G': GaugeMetricFamily(name="ap_num_clients_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'numClients24G': GaugeMetricFamily(name="ap_num_clients_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'noise5G': GaugeMetricFamily(name="ap_noise_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'noise24G': GaugeMetricFamily(name="ap_noise_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'airtime5G': GaugeMetricFamily(name="ap_airtime_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'airtime24G': GaugeMetricFamily(name="ap_airtime_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'latency50G': GaugeMetricFamily(name="ap_latency_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'latency24G': GaugeMetricFamily(name="ap_latency_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'retry5G': GaugeMetricFamily(name="ap_retries_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'retry24G': GaugeMetricFamily(name="ap_retries_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'capacity50G': GaugeMetricFamily(name="ap_capacity_5G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'capacity24G': GaugeMetricFamily(name="ap_capacity_2G", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
                'status': GaugeMetricFamily(name="ap_status", documentation="AP Received", labels=["ap","apMac","apGroup","apZone"]),
            }

            controller_metrics = {
                'uptime': CounterMetricFamily(name="node_uptime_seconds", documentation="Controller uptime", labels=["node"]),
                'cpu': GaugeMetricFamily(name="node_cpu_percent", documentation="Controller CPU used", labels=["node"]),
                'disk': GaugeMetricFamily(name="node_disk", documentation="Controller disk free", labels=["node"]),
                'memory': GaugeMetricFamily(name="node_memory_percent", documentation="Controller Memory_used", labels=["node"]),
            }

            ssid_metrics = {
                'client': GaugeMetricFamily(name="client_count", documentation="Number of users per SSID", labels=["ssid"]),
            }

            if aps:
                for ap in aps:
                    ap['deviceName'] = ap['deviceName'] or 'unknown'
                    ap['apMac'] = ap['apMac'] or '00:00:00:00:00:00'
                    for k,m in ap_metrics.items():
                        if k == "status":
                            state = 0 if not bool(ap['status']) or ap['status'] == 'Offline' else 1
                            m.add_metric([ap['deviceName'],ap['apMac'],str(ap['apGroupName']),str(ap["zoneName"])], float(state))
                        else:
                            m.add_metric([ap['deviceName'],ap['apMac'],str(ap['apGroupName']),str(ap["zoneName"])], float(ap[k] if k in ap and ap[k] is not None else 'NaN'))

                for m in ap_metrics.values():
                    yield m

            if controller_info:
                for node in controller_info:
                    for k,m in controller_metrics.items():
                        m.add_metric([node['hostname']], float(node[k] if k in node and node[k] is not None else 'NaN'))

                for m in controller_metrics.values():
                    yield m

            if ssids:
                for ssid,clients in ssids.items():
                    for k,m in ssid_metrics.items():
                        m.add_metric([ssid],float(clients))

                for m in ssid_metrics.values():
                    yield m

            return True

if __name__ == "__main__":
    REGISTRY.register(RuckusCollector())
    start_http_server(9118)
    while True:
        time.sleep(1)
