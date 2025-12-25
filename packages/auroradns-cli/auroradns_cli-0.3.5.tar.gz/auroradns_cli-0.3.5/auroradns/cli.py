#!/usr/bin/env python3
import os
import sys

from auroradns.common.argparser import Argparser
from auroradns.common.dnsapi import (
    Driver,
    DriverException,
    Zone,
    ZoneException,
    Record,
    RecordException,
)
from auroradns.common.outputs import Output
from auroradns.common.sysinfo import Sysinfo


###
### Define helper functions.
###


def get_args():
    args = Argparser.parse_arguments()
    args.filtercount = sum(
        i is not None
        for i in [args.recordid, args.name, args.data, args.prio, args.ttl, args.type]
    )
    return args


def get_driver(args):
    try:
        driver = Driver.get(args.provider, args.apikey, args.secretkey)
        return driver
    except DriverException as e:
        sys.exit(e)


def create_record(zone, args):
    try:
        record = Record.create(
            zone, args.name, args.data, args.prio, args.ttl, args.type
        )

        print(
            "Record created: {0}.{1}. {2} IN {3} {4} ".format(
                record.name, record.zone.domain, record.ttl, record.type, record.data
            )
        )

        return record

    except RecordException as e:
        sys.exit(e)


def get_records(zone, args, for_update=False):
    if for_update:
        data = None
        ttl = None
    else:
        data = args.data
        ttl = args.ttl

    try:
        records = Record.get(
            zone, args.recordid, args.name, data, args.prio, ttl, args.type
        )
        return records
    except RecordException as e:
        sys.exit(e)


def update_record(driver, records, args):
    if len(records) > 1:
        sys.exit("Too many matches, cannot update.")
    else:
        try:
            record = Record.update(
                driver, records[0], args.name, args.data, args.prio, args.ttl, args.type
            )

            print(
                "Record updated: {0}.{1}. {2} IN {3} {4} ".format(
                    record.name,
                    record.zone.domain,
                    record.ttl,
                    record.type,
                    record.data,
                )
            )

        except RecordException as e:
            sys.exit(e)


def get_zone(driver, args):
    try:
        zone = Zone.get(driver, args.zone)
        return zone
    except ZoneException as e:
        sys.exit(e)


###
### Main.
###


def main():
    sysinfo = Sysinfo()
    args = get_args()
    driver = get_driver(args)

    ###
    ### Zone related actions.
    ###

    ### LIST ZONES ###
    if args.action == "list-zones":
        try:
            zones = driver.list_zones()
            Output.print(zones, args.details, args.extras)
        except ZoneException as e:
            sys.exit(e)

    ### CREATE ZONE ###
    elif args.action == "create-zone":
        try:
            zone = Zone.create(driver, args.zone)
        except ZoneException as e:
            sys.exit(e)

    ### DELETE ZONE ###
    elif args.action == "delete-zone":
        zone = get_zone(driver, args)

        confirm = None
        if not args.force:
            confirm = input(
                "Warning, you are about to delete the zone [ {} ], this cannot be undone.\nType _uppercase_ yes to confirm: ".format(
                    zone.domain
                )
            )

        if confirm == "YES" or args.force:
            try:
                Zone.delete(driver, zone)
            except ZoneException as e:
                sys.exit(e)
        else:
            sys.exit("Cancelled.")

    ###
    ### Record related actions.
    ###

    ### GET RECORD ###
    elif args.action == "get-record":
        zone = get_zone(driver, args)
        records = get_records(zone, args)
        Output.print(records, args.details, args.extras)

    ### CREATE RECORD ###
    elif args.action == "create-record":
        zone = get_zone(driver, args)
        record = create_record(zone, args)

    ### DELETE RECORD ###
    elif args.action == "delete-record":
        if args.filtercount == 0:
            sys.exit(
                "This would delete ALL records in this zone, please specify at least one filter."
            )

        zone = get_zone(driver, args)
        records = get_records(zone, args)

        confirm = None
        if not args.force:
            Output.print(records, args.details, args.extras)
            confirm = input(
                "\nWarning, you are about to delete the records shown above, this cannot be undone.\nType _uppercase_ yes to confirm: "
            )

        if confirm == "YES" or args.force:
            try:
                print()
                Record.delete(driver, records)
            except RecordException as e:
                sys.exit(e)
        else:
            sys.exit("Cancelled.")

    ### UPDATE RECORD ###
    elif args.action == "update-record":
        for_update = True
        zone = get_zone(driver, args)
        records = get_records(zone, args, for_update)

        record = update_record(driver, records, args)

    ### SET HOSTNAME ###
    elif args.action == "set-hostname":
        if not args.zone:
            args.zone = sysinfo.hostname["domain"]
        args.name = sysinfo.hostname["short"]

        zone = get_zone(driver, args)

        for type in ["ipv6", "ipv4"]:
            if sysinfo.inetaddr[type]:
                if type == "ipv6":
                    args.type = "AAAA"
                elif type == "ipv4":
                    args.type = "A"

                records = get_records(zone, args)

                args.data = sysinfo.inetaddr[type].compressed
                if len(records) == 0:
                    record = create_record(zone, args)
                elif records[0].data != sysinfo.inetaddr[type].compressed:
                    record = update_record(driver, records, args)
                else:
                    print(
                        "IPv{0} address ({1}) matches DNS record, OK!".format(
                            sysinfo.inetaddr[type].version, args.data
                        )
                    )

                args.data = None


name = "auroradns-cli"
if __name__ == "__main__":
    main()
