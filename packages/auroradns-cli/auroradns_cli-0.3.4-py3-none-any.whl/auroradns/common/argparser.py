#!/usr/bin/env python3
import argparse
import sys


class Argparser:
    def parse_arguments():
        parser = argparse.ArgumentParser(
            add_help=True,
            description="AuroraDNS Command Line Interface",
            formatter_class=argparse.RawTextHelpFormatter,
            usage="%(prog)s [action] [arguments] (--help for more information)",
        )

        """
            Define 'action/task' arguments, these are positional and are
            mutually exclusive, this produces the following variables:
                - action
        """

        parser.add_argument(
            "action",
            choices=(
                "list-zones",
                "get-record",
                "create-record",
                "delete-record",
                "update-record",
                "create-zone",
                "delete-zone",
                "set-hostname",
            ),
            help="Specify the action to perform.",
            nargs="?",
        )

        parser.add_argument(
            "--details", default=False, help="print details", action="store_true"
        )
        parser.add_argument(
            "--extras", default=False, help="print extras", action="store_true"
        )
        parser.add_argument(
            "--force", default=False, help="do not prompt", action="store_true"
        )

        """
            Add argument group for authentication related values
        """

        auth = parser.add_argument_group("authentication")
        auth.add_argument("--apikey", "-a", default=None, help="dns api key")
        auth.add_argument("--secretkey", "-s", default=None, help="dns secret key")
        auth.add_argument("--provider", default=None, help=argparse.SUPPRESS)

        """
            Add argument group for record related arguments,
            this produces the following variables:
                - data
                - name
                - prio
                - recordid
                - ttl
                - type
        """

        record_arguments = parser.add_argument_group("record arguments")
        record_arguments.add_argument(
            "-n", "--name", help="dns name field, defaults to apex"
        )
        record_arguments.add_argument("-d", "--data", help="dns data/content field")
        record_arguments.add_argument(
            "-p",
            "--prio",
            type=int,
            help="dns record PRIO, mandatory for MX and SRV record types",
        )
        record_arguments.add_argument(
            "-t",
            "--type",
            help="dns record type, defaults to A/AAAA based on DATA, mandatory otherwise",
        )
        record_arguments.add_argument("--ttl", type=int, help="dns record TTL")
        record_arguments.add_argument("--recordid", help="dns record ID")

        """
            Add argument group for zone related values,
            this produces the following variables:
                - zone
                - zoneid
        """

        zone_arguments = parser.add_argument_group("zone arguments")
        zone_arguments.add_argument("-z", "--zone", help="dns ZONE name")
        zone_arguments.add_argument("--zoneid", help="dns zone ID\n\n")

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        return parser.parse_args()
