from email.policy import default
import json
import re
from os import getenv
from typing import Any, List, TextIO

import requests
from requests import Response

from .transaction import Transaction

IBAN_REGEX = r"^([A-Z]{2}[ \-]?[0-9]{2})(?=(?:[ \-]?[A-Z0-9]){9,30}$)((?:[ \-]?[A-Z0-9]{3,5}){2,7})([ \-]?[A-Z0-9]{1,3})?$"
KEY_MAPPING = {
    "Date": "column0",
    "Amount": "column1",
    "Account": "column2",
    "BankCode": "column3",
    "KS": "column4",
    "VS": "column5",
    "SS": "column6",
    "Identifier": "column7",
    "Type": "column8",
    "Author": "column9",
    "AccountName": "column10",
    "BankName": "column12",
    "Currency": "column14",
    "Message": "column16",
    "TaskID": "column17",
    "Specification": "column18",
    "ID": "column22",
    "Comment": "column25",
    "BIC": "column26",
    "Reference": "column27",
}

def get_transaction_value(transaction: dict, column_name: str) -> Any:
    if transaction[KEY_MAPPING[column_name]] is not None:
        return transaction[KEY_MAPPING[column_name]]["value"]
    else:
        return None

def get(endpoint: str, params: dict | None = None) -> Response:
    if (FIO_TOKEN := getenv("FIO_TOKEN")) is None:
        raise EnvironmentError("No FIO_TOKEN")

    endpoint = endpoint.replace("<token>", FIO_TOKEN)
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    req = requests.get(f"https://www.fio.cz/ib_api/rest{endpoint}", params=params)
    if getenv("DEBUG") is not None:
        print(f"{req.request.method} {req.url}")
    return req

def test_connection() -> bool:
    req = get("/lastStatement/<token>/statement")
    return req.status_code == 200
    
def get_transactions(endpoint: str | None = None) -> tuple[List[Transaction] | None, int | None]:
    transactions = []
    default_endpoint = endpoint is None
    if endpoint is None:
        endpoint = "/last/<token>/transactions.json"
    req = get(endpoint)

    if req.status_code >= 400:
        return None, None
    
    req_body = req.json()
    req_transactions = req_body["accountStatement"]["transactionList"]["transaction"]
    req_last_id = req_body["accountStatement"]["info"]["idLastDownload"]
    for req_transaction in req_transactions:
        if default_endpoint and get_transaction_value(req_transaction, "Amount") > 0:
            continue
        if default_endpoint and get_transaction_value(req_transaction, "Type") == "Platba kartou":
            continue
        
        transactions.append(Transaction(
                get_transaction_value(req_transaction, "ID"),
                get_transaction_value(req_transaction, "Date"),
                get_transaction_value(req_transaction, "Amount"),
                get_transaction_value(req_transaction, "Currency"),
                account := str(get_transaction_value(req_transaction, "Account")),
                re.search(IBAN_REGEX, account) is not None,
                get_transaction_value(req_transaction, "Message"),
                get_transaction_value(req_transaction, "VS"),
                get_transaction_value(req_transaction, "Specification"),
            ))
    return transactions, req_last_id
        
def load_transactions(f: TextIO) -> List[Transaction]:
    return [Transaction(*transaction) for transaction in json.load(f)]

def loads_transactions(js: str) -> List[Transaction]:
    return [Transaction(*transaction) for transaction in json.loads(js)]

def dump_transactions(transactions: List[Transaction], f: TextIO):
    f.truncate(0)
    json.dump(transactions, f, indent=2)
