import argparse
import json
import sys
from datetime import datetime
from operator import itemgetter
from os import getenv

from fio import get as fio_get
from fio import get_transactions as fio_get_transactions
from fio import test_connection as fio_test
from paperless import get as paperless_get
from paperless import patch as paperless_patch
from paperless import search as paperless_search
from paperless import test_connection as paperless_test

main_parser = argparse.ArgumentParser("Paperless FIO Connector", "Tags paid invoices in Paperless based on Fio Bank payments.")
sub_parser = main_parser.add_subparsers()

fio_parser = sub_parser.add_parser("fio", help="Fio API related commands.")
fio_sub_parser = fio_parser.add_subparsers()

fio_test_parser = fio_sub_parser.add_parser("test", help="Test connection to API and token.")
fio_test_parser.set_defaults(func=lambda _: print("Fio API connection OK." if fio_test() else "Fio API connection NOT OK."))

def fio_set_last(args):
    date_format = "%Y-%m-%d"
    date_start = datetime.strptime(args.date_start, date_format)
    date_start_formatted = date_start.strftime(date_format)
    date_end = datetime.strptime(args.date_end, date_format)
    date_end_formatted = date_end.strftime(date_format)

    transactions = fio_get_transactions(f"periods/<token>/{date_start_formatted}/{date_end_formatted}/transactions.json")
    if transactions is None or len(transactions[0]) == 0:
        print("Could not set last date(first step).")
        return
    
    transaction = transactions[0][-1]
    req = fio_get(f"set-last-id/<token>/{transaction.ID}/")
    if req.status_code < 400:
        print(f"Last date set to transaction ID {transaction.ID} from {transaction.get_date().strftime(date_format)}")
    else:
        print("Could not set last date(second step).")
    
    return 
    

fio_set_last_parser = fio_sub_parser.add_parser("set-last", help="Set last pull date")
fio_set_last_parser.add_argument("date_start", metavar="<YYYY-MM-DD>", type=str, help="Start date in YYYY-MM-DD format")
fio_set_last_parser.add_argument("date_end", metavar="<YYYY-MM-DD>", type=str, help="End date in YYYY-MM-DD format")
fio_set_last_parser.set_defaults(func= lambda args: fio_set_last(args))


paperless_parser = sub_parser.add_parser("paperless", help="Paperless API related commands.")
paperless_sub_parser = paperless_parser.add_subparsers()

paperless_test_parser = paperless_sub_parser.add_parser("test", help="Test connection to API and token.")
paperless_test_parser.set_defaults(func=lambda _: print("Paperless API connection OK." if paperless_test() else "Paperless API connection NOT OK."))

def paperless_get_tags():
    req = paperless_get("/tags/")
    if req is None or "results" not in req:
        print("Cannot load tags.")
        return
    print(json.dumps(req["results"],indent=2))

paperless_tags_parser = paperless_sub_parser.add_parser("tags", help="Get Paperless tags.")
paperless_tags_parser.set_defaults(func=lambda _: paperless_get_tags())

def paperless_get_types():
    req = paperless_get("/document_types/")
    if req is None or "results" not in req:
        print("Cannot load types.")
        return
    print(json.dumps(req["results"], indent=2))

paperless_types_parser = paperless_sub_parser.add_parser("types", help="Get Paperless document_types.")
paperless_types_parser.set_defaults(func=lambda _: paperless_get_types())

def paperless_search_query(args):
    query = args.query
    print(f"Searching for: \"{query}\"")
    count, results = itemgetter("count", "results")(paperless_search(query))
    print(f"Found {count} results.")

    if "count" not in args or args.count is not True:
        print(json.dumps(results, indent=2))

paperless_search_parser = paperless_sub_parser.add_parser("search", help="Custom Paperless search query.")
paperless_search_parser.add_argument("query", metavar="<query>", type=str, help="https://docs.paperless-ngx.com/usage/#basic-usage_searching")
paperless_search_parser.add_argument("-c", "--count", action="store_true", help="Show only count of found documents.")
paperless_search_parser.set_defaults(func=lambda args: paperless_search_query(args))

def link(args):
    if (TARGET_TYPE_SLUG := getenv("TARGET_TYPE_SLUG")) is None:
        raise EnvironmentError("No TARGET_TYPE_SLUG")
    if (TARGET_TAG_SLUG := getenv("TARGET_TAG_SLUG")) is None:
        raise EnvironmentError("No TARGET_TAG_SLUG")
    if (TARGET_TAG_ID := getenv("TARGET_TAG_ID")) is None:
        raise EnvironmentError("No TARGET_TAG_ID")
    if (FINAL_TAG_ID := getenv("FINAL_TAG_ID")) is None:
        raise EnvironmentError("No FINAL_TAG_ID")
    
    TARGET_TAG_ID = int(TARGET_TAG_ID)
    FINAL_TAG_ID = int(FINAL_TAG_ID)
    
    print("Linking Fio payments with Paperless documents...")
    transactions = fio_get_transactions()
    if transactions is None:
        print("No payment found.")
        return
    for transaction in transactions[0]:
        string = f"Payment {transaction.ID} from {transaction.get_date().strftime('%x %X')}"
        string = string + f", {transaction.Amount}{transaction.Currency}"

        foreign_amount = transaction.get_foreign_amount()
        if foreign_amount is not None:
            string = string + f" ({foreign_amount.amount_text}{foreign_amount.currency})"
        
        if transaction.Message:
            string = string + f", {transaction.Message}"
        
        if transaction.VS:
            string = string + f", {transaction.VS}"
        print(string)

        query = f"type:{TARGET_TYPE_SLUG} tag:{TARGET_TAG_SLUG} <param>"
        params = []
        if transaction.Message is not None and " " not in transaction.Message:
            params.append(f"'{transaction.Message}'")
        if transaction.VS is not None:
            params.append(f"'{transaction.VS}'")

        if len(params) == 0:
            print("Nothing to search for. Skipping...")

        while len(params) > 0:
            param = params.pop(0)
            print(f"Searching for: \"{query.replace('<param>', param)}\"")
            count, results = itemgetter("count", "results")(paperless_search(query.replace("<param>", param)))
            print(f"Found {count} result(s).")
            if count == 1:
                result = results[0]
                tags = result["tags"]

                print(f"Match ID: {result['id']}")
                print(f"Match tags before update: {tags}")
                if TARGET_TAG_ID in tags:
                    tags.remove(TARGET_TAG_ID)
                if FINAL_TAG_ID not in tags:
                    tags.append(FINAL_TAG_ID)
                print(f"Match tags after update: {tags}")

                if "perform" in args and args.perform is True:
                    breakpoint()
                    patch = paperless_patch(f"/documents/{result['id']}/", { "tags": tags })
                    if patch:
                        print(f"Document ID {result['id']} updated.")
                    else:
                        print(f"Document ID {result['id']} NOT updated.")
                else:
                    print("--perform not set, not updating.")
                break
            elif count > 1:
                if foreign_amount is not None and foreign_amount.amount_text is not None:
                    params.append(f"{param} ('{foreign_amount.amount_text.replace(',', '.')} {foreign_amount.currency}' OR '{foreign_amount.amount_text.replace('.', ',')} {foreign_amount.currency}')")
                else:
                    print("Too many results. Skipping...")
            else:
                print("Too few results. Skipping...")

        print("")

    if transactions[1] is not None and ("perform" not in args or args.perform is False):
        print(f"Setting last ID to {transactions[1]}")
        req = fio_get(f"set-last-id/<token>/{transactions[1]}/")
        if req.status_code < 400:
            print(f"Last ID set.")
        else:
            print("Could not set last ID.")

link_parser = sub_parser.add_parser("link", help="Link transactions with documents.")
link_parser.add_argument("-p", "--perform", action="store_true", help="Perform update requests on Paperless.")
link_parser.set_defaults(func=lambda args: link(args))

if len(sys.argv) <= 1:
    main_parser.print_help()

args = main_parser.parse_args()
if "func" in args:
    args.func(args)
