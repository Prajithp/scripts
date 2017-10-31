#!/usr/bin/python

import dns.resolver
import json
import boto3
import subprocess

def getArecordofDomain(domain):
    answers = dns.resolver.query(domain, 'A')

    resolved_ips = []
    for server in answers:
       resolved_ips.append(str(server))    
    return resolved_ips

def compareIPAddress(resolved_ips):
    is_diff = False
    try:
        with open('/tmp/dns_check_data.json', 'r') as file:
            servers = json.load(file)
            for ipaddres in resolved_ips:
                if servers[ipaddres] != 1:
                    is_diff = True
                    break
                return is_diff
    except Exception:
        return True

def writeDNSdataFIle(servers):
    with open('/tmp/dns_check_data.json', 'w') as file:
        servers = {server:1 for server in servers}
        file.write(json.dumps(servers))

def sendNotification(servers):
        template ={'IPchanged': 'yes', 'IPaddresses': servers}

        cloudwatch_events = boto3.client('events')
        response = cloudwatch_events.put_events(Entries=[
                {
                    'Detail': json.dumps(template),
                    'DetailType': 'dns-check',
                    'Resources': [
                        'xxxxxxxxxxxxxxxxxx',
                    ],
                    'Source': 'com.xxxx.DNS.Change'
                }
            ]
        )
        return response['Entries']

reloadCmd = ["sudo", "/etc/init.d/nginx", "reload"]

servers = getArecordofDomain("xxxxxxxxxxxxxxxxx.tld")
if compareIPAddress(servers) == True:
    try:
        sendNotification(servers)
        subprocess.call(reloadCmd)
        writeDNSdataFIle(servers)
    except Exception:
        pass
else:
    print "IP addrsses are same: %s" %(",".join(servers))

