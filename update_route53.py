#!/usr/bin/python3

import argparse
import boto3
import ipaddress
import socket
from contextlib import contextmanager
from urllib.request import urlopen, Request
from urllib.parse import urlparse


@contextmanager
def socketcontext(*args, **kw):
    """
    Wraps socket.socket in a context manager for auto-closing.
    Shamelessly stolen from https://stackoverflow.com/a/16772520
    """
    s = socket.socket(*args, **kw)
    try:
        yield s
    finally:
        s.close()

def get_localhost():
    """
    Obtains the localhost ip address.
    Note that opening the udp socket doesn't actually send a packet,
    so this is a fast and reasonable operation.
    Shamelessly stolen from https://stackoverflow.com/a/166589
    """
    with socketcontext(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        localhost = s.getsockname()[0]
        return localhost

def request_address():
    """
    Remotely requests ip address from ifconfig.co.
    User-Agent is required, or a 403 Forbidden is returned.
    Check out both https://ifconfig.co and https://github.com/mpolden/echoip
    """
    headers = { 'User-Agent' : 'update-route53/1.0' }
    url = 'https://ifconfig.co/ip'
    req = Request(url, headers=headers)
    response = urlopen(req)
    return response.read().decode('utf-8').strip()

def get_public_ip():
    """
    Detect the public IP of this machine via localhost or remote request.
    """
    localhost = get_localhost()
    if ipaddress.ip_address(localhost).is_private:
        return request_address()
    else:
        return localhost

def get_domain_from_fqdn(name):
    """
    Parses out the domain part that is necessary for getting the hosted zone.
    Accounts for the public suffixes supported by the route53 registrar
    (which is not the complete list. For that, see https://publicsuffix.org/)
    'foo.bar.co.uk.' -> 'bar.co.uk'
    """
    normalized_name = name[:-1] if name.endswith('.') else name
    double_tlds = [
        'com.au',
        'co.uk',
        'com.mx',
        'me.uk',
        'net.au',
        'net.nz',
        'org.nz',
        'org.uk'
    ]
    double_tld = any(map(lambda x: normalized_name.endswith(x), double_tlds))
    split_point = 3 if double_tld else 2
    domain = '.'.join(normalized_name.split('.')[-split_point:])
    return domain


class Route53Updater(object):
    """
    Route 53 Updater. The only state is the cached boto3 client.
    """
    def __init__(self):
        self.client = boto3.client('route53')

    def get_hosted_zone_id_for_domain(self, domain):
        """
        Looks up the zone_id for a given domain name (no trailing .)
        """
        response = self.client.list_hosted_zones_by_name(
            DNSName=domain,
            MaxItems='1'
        )
        zone = response['HostedZones'][0]
        if zone['Name'] == domain + '.':
            return zone['Id']
        return None

    def upsert_name_with_ip(self, zone_id, name, ip):
        """
        boto3 change_resource_record_sets call wrapper
        """
        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Comment': 'Update from update-route53 script',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': name,
                            'ResourceRecords': [
                                {'Value': ip}
                            ],
                            'Type': 'A',
                            'TTL': 300,
                        }
                    }
                ]
            }
        )
        return response

    def check_dns(self, name, ip):
        """
        Checks if ip is the only entry for name.
        """
        res = socket.getaddrinfo(name, 80, type=socket.SOCK_STREAM)
        if [ip] == list(set([ str(i[4][0]) for i in res ])):
            return True
        return False


def register_ip(name, ip, always):
    """
    Associates a name with an ip in Route53
    """
    domain = get_domain_from_fqdn(name)
    rup = Route53Updater()
    zone_id = rup.get_hosted_zone_id_for_domain(domain)
    if always or not rup.check_dns(name, ip):
        response = rup.upsert_name_with_ip(zone_id, name, ip)
        print(response)
    else:
        print("Not updating, no change detected.")

def main_func():
    parser = argparse.ArgumentParser(description='Sets a DNS A record to point to an ip')
    parser.add_argument('name', help='fully qualified domain name to set')
    parser.add_argument('--ip', help='ip address, default is localhost')
    parser.add_argument('--always', default=False, action='store_true', help='skips dns check to avoid unnecessary updates. Default is False.')
    args = parser.parse_args()
    ip = None
    if args.ip:
        ipaddress.ip_address(args.ip)
        ip = args.ip
    else:
        ip = get_public_ip()
    register_ip(args.name, ip, args.always)

if __name__ == '__main__':
    main_func()
