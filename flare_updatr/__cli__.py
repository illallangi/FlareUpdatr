#!/usr/bin/env python

import datetime
import os
import time

import CloudFlare

import kubernetes

import requests

DOMAIN_ANNOTATION = "flareupdatr.illallangi.enterprises/domain"
IPIFY_ANNOTATION = "flareupdatr.illallangi.enterprises/ipify"
EMAIL_ANNOTATION = "flareupdatr.illallangi.enterprises/email"
KEY_ANNOTATION = "flareupdatr.illallangi.enterprises/key"


def main():
    starttime = time.time()
    timeout = float(os.environ.get("UPDATE_INTERVAL", 300))
    while True:
        flareUpdate()
        sleep = max(0, timeout - ((time.time() - starttime) % timeout))
        if sleep > 1:
            print('{0}        Sleeping {1:00.0f} seconds'.format(datetime.datetime.now().isoformat(), sleep), flush=True)
            time.sleep(sleep)


def flareUpdate():
    try:
        if 'KUBERNETES_SERVICE_HOST' in os.environ:
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config()
    except kubernetes.config.ConfigException:
        exit("Cannot initialize kubernetes API, terminating.")

    ip_api_cache = {}
    v1 = kubernetes.client.CoreV1Api()
    services = v1.list_service_for_all_namespaces(watch=False)
    for svc in services.items:
        if svc is not None and svc.metadata is not None:
            if svc.metadata.annotations is not None and DOMAIN_ANNOTATION in svc.metadata.annotations:
                print("{0}        Processing service {2} in namespace {1}: ".format(datetime.datetime.now().isoformat(), svc.metadata.namespace, svc.metadata.name), flush=True)

                if svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org") in ip_api_cache:
                    print("{0}         - Using cached IP from {1}: ".format(
                        datetime.datetime.now().isoformat(),
                        svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org")), end='', flush=True)
                    ip = ip_api_cache[svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org")]
                else:
                    print("{0}         - Getting IP from {1}: ".format(
                        datetime.datetime.now().isoformat(),
                        svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org")), end='', flush=True)
                    ip = ip_api(
                        svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org"))
                    ip_api_cache[svc.metadata.annotations.get(IPIFY_ANNOTATION, "https://api.ipify.org")] = ip
                print("{0}".format(ip), flush=True)

                print("{0}         - Updating {1} with email {2} and key {3}: ".format(
                    datetime.datetime.now().isoformat(),
                    svc.metadata.annotations.get(DOMAIN_ANNOTATION),
                    svc.metadata.annotations.get(EMAIL_ANNOTATION, os.environ.get("CF_EMAIL")),
                    svc.metadata.annotations.get(KEY_ANNOTATION, os.environ.get("CF_KEY"))), end='', flush=True)
                cloudflare = cloudflare_api(
                    ip,
                    svc.metadata.annotations.get(DOMAIN_ANNOTATION),
                    svc.metadata.annotations.get(EMAIL_ANNOTATION, os.environ.get("CF_EMAIL")),
                    svc.metadata.annotations.get(KEY_ANNOTATION, os.environ.get("CF_KEY")))
                print("%s" % cloudflare, flush=True)


def ip_api(url):
    try:
        ip = requests.get(url).text
    except BaseException:
        exit('%s: failed' % (url))
    if ip == '':
        exit('%s: failed' % (url))
    return ip


def cloudflare_api(ip_address, domain, email, token):
    cf = CloudFlare.CloudFlare(email, token)

    zone_name = '.'.join(domain.split('.')[-2:])

    try:
        params = {'name': zone_name}
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        return ('/zones %d %s - api call failed' % (e, e))
    except Exception as e:
        return ('/zones.get - %s - api call failed' % (e))

    if len(zones) == 0:
        return ('/zones.get - %s - zone not found' % (zone_name))

    if len(zones) != 1:
        return ('/zones.get - %s - api call returned %d items' % (zone_name, len(zones)))

    zone = zones[0]

    zone_name = zone['name']
    zone_id = zone['id']

    try:
        params = {'name': domain, 'match': 'all', 'type': 'A'}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        return ('/zones/dns_records %s - %d %s - api call failed' % (domain, e, e))

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record['content']

        if ip_address == old_ip_address:
            return ('No Change')

        proxied_state = dns_record['proxied']
        dns_record_id = dns_record['id']
        dns_record = {
            'name': domain,
            'type': 'A',
            'content': ip_address,
            'proxied': proxied_state
        }
        try:
            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            return ('/zones.dns_records.put %s - %d %s - api call failed' % (domain, e, e))
        return ('Updated from %s' % old_ip_address)

    # no exsiting dns record to update - so create dns record
    dns_record = {
        'name': domain,
        'type': 'A',
        'content': ip_address
    }
    try:
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        return ('/zones.dns_records.post %s - %d %s - api call failed' % (domain, e, e))
    return ('Created')


if __name__ == "__main__":
    main()
