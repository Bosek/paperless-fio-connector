import argparse
import sys

from actions import *
from fio import test_connection as fio_test
from paperless import test_connection as paperless_test

main_parser = argparse.ArgumentParser("Paperless FIO Connector", "Tags paid invoices in Paperless based on Fio Bank payments.")
sub_parser = main_parser.add_subparsers()

fio_parser = sub_parser.add_parser("fio", help="Fio API related commands.")
fio_sub_parser = fio_parser.add_subparsers()

fio_test_parser = fio_sub_parser.add_parser("test", help="Test connection to API and token.")
fio_test_parser.set_defaults(func=lambda _: print("Fio API connection OK." if fio_test() else "Fio API connection NOT OK."))

fio_set_last_parser = fio_sub_parser.add_parser("set-last", help="Set last pull date")
fio_set_last_parser.add_argument("date_start", metavar="<YYYY-MM-DD>", type=str, help="Start date in YYYY-MM-DD format")
fio_set_last_parser.add_argument("date_end", metavar="<YYYY-MM-DD>", type=str, help="End date in YYYY-MM-DD format")
fio_set_last_parser.set_defaults(func= lambda args: fio_set_last(args))

paperless_parser = sub_parser.add_parser("paperless", help="Paperless API related commands.")
paperless_sub_parser = paperless_parser.add_subparsers()

paperless_test_parser = paperless_sub_parser.add_parser("test", help="Test connection to API and token.")
paperless_test_parser.set_defaults(func=lambda _: print("Paperless API connection OK." if paperless_test() else "Paperless API connection NOT OK."))

paperless_tags_parser = paperless_sub_parser.add_parser("tags", help="Get Paperless tags.")
paperless_tags_parser.set_defaults(func=lambda _: paperless_get_tags())

paperless_types_parser = paperless_sub_parser.add_parser("types", help="Get Paperless document_types.")
paperless_types_parser.set_defaults(func=lambda _: paperless_get_types())

paperless_search_parser = paperless_sub_parser.add_parser("search", help="Custom Paperless search query.")
paperless_search_parser.add_argument("query", metavar="<query>", type=str, help="https://docs.paperless-ngx.com/usage/#basic-usage_searching")
paperless_search_parser.add_argument("-c", "--count", action="store_true", help="Show only count of found documents.")
paperless_search_parser.set_defaults(func=lambda args: paperless_search_query(args))

link_parser = sub_parser.add_parser("link", help="Link transactions with documents.")
link_parser.add_argument("-p", "--perform", action="store_true", help="Perform update requests on Paperless.")
link_parser.set_defaults(func=lambda args: link(args))

if len(sys.argv) <= 1:
    main_parser.print_help()

args = main_parser.parse_args()
if "func" in args:
    args.func(args)
