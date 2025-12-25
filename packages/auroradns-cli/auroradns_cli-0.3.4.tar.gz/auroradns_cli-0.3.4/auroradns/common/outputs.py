#!/usr/bin/env python3
import operator
import os
import sys
from libcloud.dns.base import Zone, Record


class Output:
    def log():
        pass

    def print(data=None, print_details=False, print_extras=False):
        """
            This function basically accepts all kinds of data but will in 90%
            of all cases receive a list with "dicts" (Zone/Record datatypes).
            If `data` is found to be of type list, some further investigation
            will be carried out, otherwise everything is just dumped to stdout.
        """
        if not data:
            print("Nothing to do.")

        elif isinstance(data, list):
            if isinstance(data[0], Zone):
                # https://libcloud.readthedocs.io/en/latest/dns/api.html#libcloud.dns.base.Zone
                if print_details:
                    keys = ["id", "type", "ttl", "domain"]
                    # extra = ["created", "servers", "account_id", "cluster_id"]
                    extra = ["created", "servers", "account_id", "cluster_id"]
                else:
                    keys = ["domain"]
                    extra = ["created", "servers"]

                sortby = keys.index("domain")
                fillwith = keys.index("domain")

            elif isinstance(data[0], Record):
                # https://libcloud.readthedocs.io/en/latest/dns/api.html#libcloud.dns.base.Record
                if print_details:
                    keys = ["id", "name", "type", "ttl", "data"]
                    # extra = ["created", "modified", "ttl", "disabled", "priority"]
                    extra = ["created", "modified", "disabled", "priority"]
                else:
                    keys = ["name", "type", "priority", "ttl", "data"]
                    extra = ["disabled", "priority"]

                sortby = keys.index("type")
                fillwith = keys.index("data")

            """
                If the keys variable is found in locals() the contents of `data`
                is either of type Zone or Record so it'll be printed in an
                orderly fashion, if not this just dumps everything to stdout.
            """
            if "keys" in locals():
                width = []
                for i in range(len(keys)):
                    width.append(10)

                entities = []
                for item in data:
                    values = []
                    for c, key in enumerate(keys):
                        if key == "priority":
                            if item.type in ["MX", "SRV"]:
                                value = item.extra["priority"]
                            else:
                                value = "-"
                        else:
                            value = getattr(item, key, "@")

                        values.append(value)

                        if width[c] < len(str(value)):
                            width[c] = len(str(value))
                    values.append(item.extra)
                    entities.append(values)

                """
                    Make sure the output width never exceeds the ttwidth by
                    subtracting the width of all columns from ttywidth except
                    for one (fillwith) which will be set to the remaining space.
                """
                ttywidth = int(os.popen("stty size", "r").read().split()[1])
                width_remaining = ttywidth
                for id, chars in enumerate(width):
                    if id == fillwith:
                        continue
                    width_remaining -= chars + 1
                width[fillwith] = width_remaining

                spacing = " ".join(
                    "{" + str(id) + ":<" + str(item) + "s}"
                    for id, item in enumerate(width)
                )

                print(spacing.format(*keys))
                print(spacing.format(*[i * ("-") for i in width]))
                for entity in sorted(entities, key=lambda i: i[sortby]):
                    print(spacing.format(*[str(i) for i in entity]))
                    if print_extras:
                        extras = (
                            " \033[0;34m > "
                            + ", ".join(
                                str(i) + ": " + str(j)
                                for i, j in entity[-1].items()
                                if i in extra
                            )
                            + "\033[0;0m"
                        )
                        print(extras)

            else:
                for item in data:
                    print(item)

        else:
            try:
                print(data)
            except Exception as e:
                sys.exit("Error: {}".format(e))
