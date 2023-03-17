import json
from datetime import datetime
from operator import itemgetter
from os import getenv

from fio import get as fio_get
from fio import get_transactions as fio_get_transactions
from paperless import get as paperless_get
from paperless import patch as paperless_patch
from paperless import post as paperless_post
from paperless import search as paperless_search


def fio_set_last(args):
    date_format = "%Y-%m-%d"
    date_start = datetime.strptime(args.date_start, date_format)
    date_start_formatted = date_start.strftime(date_format)
    date_end = datetime.strptime(args.date_end, date_format)
    date_end_formatted = date_end.strftime(date_format)

    transactions, _ = fio_get_transactions(f"periods/<token>/{date_start_formatted}/{date_end_formatted}/transactions.json")
    if transactions is None or len(transactions) == 0:
        print("Could not set last date(first step).")
        return
    
    transaction = transactions[-1]
    req = fio_get(f"set-last-id/<token>/{transaction.ID}/")
    if req.status_code < 400:
        print(f"Last date set to transaction ID {transaction.ID} from {transaction.get_date().strftime(date_format)}")
    else:
        print("Could not set last date(second step).")
    
    return

def paperless_get_tags():
    req = paperless_get("/tags/")
    if req is None or "results" not in req:
        print("Cannot load tags.")
        return
    print(json.dumps(req["results"],indent=2))

def paperless_get_types():
    req = paperless_get("/document_types/")
    if req is None or "results" not in req:
        print("Cannot load types.")
        return
    print(json.dumps(req["results"], indent=2))

def paperless_search_query(args):
    query = args.query
    print(f"Searching for: \"{query}\"")
    count, results = itemgetter("count", "results")(paperless_search(query))
    print(f"Found {count} results.")

    if "count" not in args or args.count is not True:
        print(json.dumps(results, indent=2))

def link(args):
    if (DOCUMENTS_FILTER := getenv("DOCUMENTS_FILER")) is None:
        raise EnvironmentError("No DOCUMENTS_FILTER")
    if (TARGET_TAG_ID := getenv("TARGET_TAG_ID")) is None:
        raise EnvironmentError("No TARGET_TAG_ID")
    if (FINAL_TAG_ID := getenv("FINAL_TAG_ID")) is None:
        raise EnvironmentError("No FINAL_TAG_ID")
    
    TARGET_TAG_ID = int(TARGET_TAG_ID)
    FINAL_TAG_ID = int(FINAL_TAG_ID)
    
    print("Linking Fio payments with Paperless documents...")
    transactions, last_id = fio_get_transactions()
    if transactions is None or len(transactions) == 0:
        print("No payment found.")
        return
    for transaction in transactions:
        string = f"Payment {transaction.ID} from {transaction.get_date().strftime('%x %X')}"
        comment = f"{transaction.get_date().strftime('%x %X')}, {transaction.ID}, {transaction.Account}"

        string = string + f", {transaction.Amount}{transaction.Currency}"
        comment = comment + f", {transaction.Account}{transaction.Currency}"

        foreign_amount = transaction.get_foreign_amount()
        if foreign_amount is not None:
            string = string + f"| ({foreign_amount.amount_text}{foreign_amount.currency})"
            comment = comment + f"| ({foreign_amount.amount_text}{foreign_amount.currency})"
        
        if transaction.Message:
            string = string + f", {transaction.Message}"
            comment = comment + f", {transaction.Message}"
        
        if transaction.VS:
            string = string + f", {transaction.VS}"
            comment = comment + f", {transaction.VS}"
        print(string)

        query = f"{DOCUMENTS_FILTER.strip()} <param>"
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
                    patch = paperless_patch(f"/documents/{result['id']}/", { "tags": tags })

                    if patch:
                        comment = paperless_post(f"/documents/{result['id']}/comments/", { "comment": comment })
                        print(f"Document ID {result['id']} updated.")
                        print("Comment was added." if comment else "Comment was NOT added.")
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

    if last_id is not None and ("perform" not in args or args.perform is False):
        print("--perform not set, resetting last ID.")
        print(f"Setting last ID to {last_id}")
        req = fio_get(f"set-last-id/<token>/{last_id}/")
        if req.status_code < 400:
            print(f"Last ID set.")
        else:
            print("Could not set last ID.")