# auroradns-cli

A command line api client for PCextreme's AuroraDNS service based on Apache
Libcloud.

## Usage

```bash
usage: auroradns-cli.py [action] [arguments] (--help for more information)

AuroraDNS Command Line Interface

positional arguments:
  {list-zones,get-record,create-record,delete-record,update-record,create-zone,delete-zone,set-hostname}
                        Specify the action to perform.

optional arguments:
  -h, --help            show this help message and exit
  --details             print details
  --extras              print extras
  --force               do not prompt

authentication:
  --apikey APIKEY, -a APIKEY
                        dns api key
  --secretkey SECRETKEY, -s SECRETKEY
                        dns secret key

record arguments:
  -n NAME, --name NAME  dns name field, defaults to apex
  -d DATA, --data DATA  dns data/content field
  -p PRIO, --prio PRIO  dns record PRIO, mandatory for MX and SRV record types
  -t TYPE, --type TYPE  dns record type, defaults to A/AAAA based on DATA, mandatory otherwise
  --ttl TTL             dns record TTL
  --recordid RECORDID   dns record ID

zone arguments:
  -z ZONE, --zone ZONE  dns ZONE name
  --zoneid ZONEID       dns zone ID
```

### Examples

List all records in a zone:

```bash
./auroradns-cli.py get-record --zone=mydomain.net
name              type       priority   ttl        data
----------------- ---------- ---------- ---------- ----------------------------------------------------------------------
@                 A                     900        203.0.113.20
*                 A                     900        203.0.113.20
@                 AAAA                  900        2001:db8:1337::5054:efff:fe0c:c675
*                 AAAA                  900        2001:db8:1337::5054:efff:fe0c:c675
@                 MX         10         900        primary.mail.pcextreme.nl
@                 MX         20         900        fallback.mail.pcextreme.nl
@                 NS                    3600       ns081.auroradns.eu
@                 NS                    3600       ns082.auroradns.nl
@                 NS                    3600       ns083.auroradns.info
@                 SOA                   4800       ns081.auroradns.eu admin.auroradns.eu 2019011401 86400 7200 604800 300
```

Filter on specific record types and ttl:

```bash
./auroradns-cli.py get-record --zone=mydomain.net --type=AAAA --ttl=900
name          type       priority   ttl        data
------------- ---------- ---------- ---------- ----------------------------------
@             AAAA                  900        2001:db8:1337::5054:efff:fe0c:c675
*             AAAA                  900        2001:db8:1337::5054:efff:fe0c:c675
```

Create a new dns-record, IPv6 and IPv4 records are validated and record type is
automatically set to AAAA or A if not specified. TTL defaults to zone default:

```bash
./auroradns-cli.py create-record --zone=mydomain.net --name=test123 --data=2001:db8:1337:dbfd:5054:3eff:feba:c1f3
Record created: test123.mydomain.net. 3600 IN AAAA 2001:db8:1337:dbfd:5054:3eff:feba:c1f3
```

Delete a record, multiple records can be removed if the filters
return multiple results:

```bash
./auroradns-cli.py delete-record --zone=mydomain.net --name=mysubdomain --type=A
name                 type       priority   ttl        data
-------------------- ---------- ---------- ---------- ----------------------------
mysubdomain          AAAA                  3600       2001:db8:1337::5054:15ff:feb8:6a0e

Warning, you are about to delete the records shown above, this cannot be undone.
Type _uppercase_ yes to confirm: YES

Deleted record id 9f020b67-5b77-46e8-832c-0792280e3260: mysubdomain.mydomain.net. 3600 IN A 203.0.113.10
```

Automatically create or update AAAA-/A-records for the host

```bash
./auroradns-cli.py set-hostname
Record created: mysubdomain.mydomain.net. 3600 IN AAAA 2001:db8:1337::5054:15ff:feb8:6a0e
Record updated: mysubdomain.mydomain.net. 3600 IN A 203.0.113.10
```

## Authentication

You can either pass the `--apikey APIKEY` and `--secretkey SECRETKEY` command
line argumenrs or set the `DNS_API_KEY` and `DNS_SECRET_KEY` environment
variables:

```bash
export DNS_API_KEY=MYAPIKEY; export DNS_SECRET_KEY=MYSECRETKEY
```

## Setup

```bash
pip3 install auroradns-cli
```

### Requirements

#### Ubuntu 16+

```bash
apt install python3 python3-pip python3-dev
```

#### CentOS 7

```bash
yum install python3 python3-pip python3-devel
```

## License

* MIT License

This is my first python project ever so there's probably a lot of code in here
that doesn't even come close to being pythonic and some design choices that
may seem very strange but they seemed logical to me at the time. So no
guarantees on this whatsoever, use at your own risk. If this works for you,
great, enjoy! If not, send me a message and I'll try to fix the issue.
