#!/usr/bin/env python3
import ipaddress
import os
import requests
import socket
import sys
import tldextract


class Sysinfo:
    def __init__(self):
        self.inetaddr = {"ipv6": None, "ipv4": None}
        self.set_inetaddr(self.inetaddr)

        self.hostname = {"domain": None, "fqdn": None, "short": None}
        self.set_hostname()

    def set_inetaddr(self, inet_families):
        domain = "ip-addr.net"
        for i in [6, 4]:
            try:
                my_ip = requests.get("https://{0}.{1}".format(i, domain)).text.rstrip(
                    "\n"
                )

                if ipaddress.ip_address(my_ip).version == 6:
                    self.inetaddr["ipv6"] = ipaddress.IPv6Address(my_ip)
                elif ipaddress.ip_address(my_ip).version == 4:
                    self.inetaddr["ipv4"] = ipaddress.IPv4Address(my_ip)
            except Exception:
                continue

    def set_hostname(self):
        try:
            sys.stderr = open(os.devnull, "w")
            ext = tldextract.extract(socket.gethostname())
            sys.stderr = sys.__stderr__
            self.hostname["fqdn"] = ext.fqdn.lower()
            self.hostname["domain"] = ext.registered_domain.lower()
            self.hostname["short"] = ext.subdomain.lower() or ''
        except Exception as e:
            print("Error getting hostname: {}".format(e))


def main():
    sysinfo = Sysinfo()
    for key, value in sysinfo.hostname.items():
        print("{0}: {1}".format(key, value))
    for key, value in sysinfo.inetaddr.items():
        print("{0}: {1}".format(key, value))


if __name__ == "__main__":
    main()
