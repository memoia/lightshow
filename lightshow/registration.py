import socket
import urllib
from urlparse import urlparse
from time import sleep
from beautifulhue.api import Portal, Bridge

DEFAULT_USER = 'immlightshow'
DEFAULT_DEVICE = 'python'


def discover_upnp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(True)
    sock.settimeout(1.0)

    message = """M-SEARCH * HTTP/1.1
    HOST: 239.255.255.250:1900
    MAN: ssdp:discover
    MX: 10
    ST: ssdp:all"""

    hue_ip = None

    def base_station_ip(upnp_response):
        location = lambda x: x.startswith('LOCATION: ')
        url = filter(location, upnp_response.split("\n"))[0][10:].strip()
        data = urllib.urlopen(url).read()
        if 'Philips hue' in data:
            return urlparse(url).netloc.split(':')[0]
        return None

    if sock.sendto(message, ("239.255.255.250", 1900)) == 101:
        while True:
            try:
                hue_ip = base_station_ip(sock.recv(256))
                if hue_ip:
                    break
            except IndexError:
                continue
            except socket.timeout:
                break

    return hue_ip


def discover_nupnp(station=0):
    res = Portal().get()
    return res.get('resource')[station].get('internalipaddress')


def discover():
    return discover_upnp() or discover_nupnp()


def is_registered(ip, username=DEFAULT_USER):
    bridge = Bridge(device={'ip': ip}, user={'name': username})
    resource = {'which': 'bridge'}
    response = bridge.config.get(resource)
    return bool(response.get('resource').get('whitelist', {}))


def register(ip, username=DEFAULT_USER, devicetype=DEFAULT_DEVICE):
    if not is_registered(ip, username):
        bridge = Bridge(device={'ip': ip},
                        user={'name': username})
        resource = {'user': {'devicetype': devicetype,
                             'name': username}}
        rsp = bridge.config.create(resource.copy())  # create() modifies it
        if rsp.get('resource')[0].get('error', {}).get('type', None) == 101:
            print "Press button on bridge now."
            sleep(10)
            rsp = bridge.config.create(resource)
    return (ip, username)
