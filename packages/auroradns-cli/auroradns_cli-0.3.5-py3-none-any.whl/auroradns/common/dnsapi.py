#!/usr/bin/env python3
import ipaddress
import os
import sys
from libcloud.dns.providers import get_driver
from libcloud.dns.types import (
    Provider,
    ZoneError,
    ZoneDoesNotExistError,
    ZoneAlreadyExistsError,
    RecordError,
    RecordDoesNotExistError,
    RecordAlreadyExistsError,
)


class DriverException(Exception):
    pass


class ZoneException(Exception):
    pass


class RecordException(Exception):
    pass


class Driver:
    def get(provider, apikey, secretkey):
        if not provider:
            provider = "AURORADNS"

        if not apikey:
            try:
                apikey = os.environ["DNS_API_KEY"]
            except KeyError:
                raise DriverException("APIKEY not set.")

        if not secretkey:
            try:
                secretkey = os.environ["DNS_SECRET_KEY"]
            except KeyError:
                raise DriverException("SECRETKEY not set.")

        try:
            provider = getattr(Provider, provider)
            cls = get_driver(provider)
            driver = cls(apikey, secretkey)

            return driver
        except Exception as e:
            raise DriverException("Error loading driver: {}".format(e))


class Zone:
    def create(driver=None, name=None):
        try:
            zone = driver.create_zone(name, "master", 3600)
            print("Zone {} has been created.".format(zone.domain))

            return zone

        except (ZoneError, ZoneAlreadyExistsError):
            raise ZoneException("Zone already exists.")
        except Exception as e:
            sys.exit("Error: {}".format(e))

    def get(driver=None, name=None):
        try:
            zone = driver.get_zone(name)

            return zone

        except (ZoneError, ZoneDoesNotExistError):
            raise ZoneException("Zone does not exist.")
        except Exception as e:
            sys.exit("Error: {}".format(e))

    def delete(driver=None, zone=None):
        try:
            driver.delete_zone(zone)

            print("Zone {} has been deleted.".format(zone.domain))

        except (ZoneError, ZoneDoesNotExistError):
            raise ZoneException("Zone does not exist.")
        except Exception as e:
            sys.exit("Error: {}".format(e))


class Record:
    def create(zone, name=None, data=None, prio=None, ttl=None, type=None):
        if not data:
            sys.exit("Record data not specified, use --data=DATA")

        if not ttl:
            ttl = zone.ttl
        elif not isinstance(ttl, int):
            sys.exit("TTL is not numerical.")

        if not prio:
            prio = 0
        elif not isinstance(prio, int):
            sys.exit("Prio is not numerical.")

        if not type:
            if ipaddress.ip_address(data).version == 6:
                type = "AAAA"
            elif ipaddress.ip_address(data).version == 4:
                type = "A"
            else:
                sys.exit("Record type not specified, use --type=TYPE")

        if not prio and (type == "MX" or type == "SRV"):
            sys.exit("MX and SRV record types require prio (int), use --prio=PRIO")

        try:
            record = zone.create_record(
                name=name, type=type, data=data, extra={"priority": prio, "ttl": ttl}
            )

            return record

        except (ZoneAlreadyExistsError, RecordAlreadyExistsError):
            raise RecordException("Record already exists.")
        except (ZoneError, RecordError):
            raise RecordException("Error: {}".format(e))
        except Exception as e:
            sys.exit("Error: {}".format(e))

    def get(zone, recordid=None, name=None, data=None, prio=None, ttl=None, type=None):
        records = []
        try:
            all_records = zone.list_records()
            for record in all_records:
                # Filter on name, data, prio, ttl, type
                if (
                    (not recordid or recordid == record.id)
                    and (
                        not name
                        or name == record.name
                        or (not record.name and (name == "@" or name == "None"))
                    )
                    and (not data or record.data == data)
                    and (not prio or record.extra["priority"] == prio)
                    and (not ttl or record.ttl == ttl)
                    and (not type or type == record.type)
                ):
                    if not record.name:
                        record.name = "@"

                    records.append(record)

            return records

        except RecordDoesNotExistError:
            raise RecordException("No records found.")
        except RecordError as e:
            raise RecordException("Error: {}".format(e))
        except Exception as e:
            sys.exit("Error: {}".format(e))

    def update(driver, record, name=None, data=None, prio=None, ttl=None, type=None):
        if not name or name == "@":
            name == ""

        if not data:
            data = record.data

        if not prio:
            prio = record.extra["priority"]

        if not ttl:
            ttl = record.extra["ttl"]

        if not type:
            type = record.type

        try:
            record = driver.update_record(
                record,
                name=name,
                type=type,
                data=data,
                extra={"priority": prio, "ttl": ttl},
            )

            return record

        except (ZoneDoesNotExistError, RecordDoesNotExistError):
            raise RecordException("Record does not exist.")
        except (ZoneError, RecordError) as e:
            raise RecordException("Error: {}".format(e))
        except Exception as e:
            sys.exit("Error: {}".format(e))

    def delete(driver, records):
        for record in records:
            try:
                driver.delete_record(record)

                print(
                    "Deleted record id {0}: {1}.{2}. {3} IN {4} {5} ".format(
                        record.id,
                        record.name,
                        record.zone.domain,
                        record.ttl,
                        record.type,
                        record.data,
                    )
                )

            except RecordDoesNotExistError:
                raise RecordException(
                    "The record you are trying to delete does not exist."
                )
            except RecordError as e:
                raise RecordException("Error: {}".format(e))
            except Exception as e:
                sys.exit("Error: {}".format(e))
