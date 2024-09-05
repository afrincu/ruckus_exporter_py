import RuckusVirtualSmartZoneAPIClient

class Exporter(object):

    # Class variables
    vszClient = None
    vszHostname = "localhost"
    vszPort = 8443

    # Function
    def __init__(self, hostname: str="localhost", port: int=8443):
        self.vszClient = RuckusVirtualSmartZoneAPIClient.Client(verify=False,api_version='v9_1')
        self.vszHostname = hostname
        self.vszPort = port

    def login(self, username: str, password: str):
        self.vszClient.connect(url=f"https://{self.vszHostname}:{self.vszPort}", username=username, password=password)
        return self.vszClient.service_ticket != None

    def logout(self):
        self.vszClient.disconnect()
        return True

    def getAPs(self):
        maxNumberAPs = 0
        for c in self.vszClient.get(method='/system').json().get('apNumberLimitSettingsOfDomain',[]):
            maxNumberAPs = c.get('numberLimit',0) + maxNumberAPs
        maxNumberAPs = maxNumberAPs if maxNumberAPs > 0 else 1000
        result = self.vszClient.post(method='/query/ap',data={"attributes":["*"], "limit":maxNumberAPs})
        if result.status_code != 200:
            return False
        aps = result.json()['list']
        return aps

    def getSSIDs(self):
        result = self.vszClient.post(method='/query/wlan',data={"attributes":["*"], "limit": 100})
        if result.status_code != 200:
            return False
        ssids = {}
        for wlan in result.json().get('list',[]):
            ssids[wlan['ssid']] = wlan['clients'] + ssids.get(wlan['ssid'],0)
        return ssids

    def getControllerInfo(self):
        result = self.vszClient.get(method='/controller')
        if result.status_code != 200:
            return False
        controllers = []
        for node in result.json().get('list',[]):
            node_stats = self.vszClient.get(method=f'/controller/{node["id"]}/statistics?size=1').json()
            controllers.append({
                'hostname':node['hostName'],
                'uptime':node['uptimeInSec'],
                'cpu':node_stats[0]['cpu']['percent'],
                'disk':node_stats[0]['disk']['free'],
                'memory':node_stats[0]['memory']['percent'],
            })
        return controllers


