import argparse
import json
import datetime
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.utils import (
    call_wallet_api,
    get_records,
    make_report,
    save_report,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a monthly wallet report.")
    parser.add_argument(
        "--accounts",
        type=json.loads,
        default=None,
        help="Dictionary of accounts as a JSON string, e.g. '{\"account_name\": \"account_id\"}'",
    )
    parser.add_argument(
        "--reference-date",
        type=str,
        default=datetime.date.today(),
        help="Reference date for the report in YYYY-MM-DD format. Defaults to the previous month.",
    )
    return parser.parse_args()

def monthly_report(accounts=None, reference_date_str=None):
    if accounts is None and reference_date_str is None:
        args = parse_args()
        accounts = args.accounts
        reference_date_str = str(args.reference_date)

    if not accounts:
        accounts_response = call_wallet_api("v1/api/accounts")
        accounts = {account["name"]: account["id"] for account in accounts_response["accounts"]}

    monthly_records = get_records(accounts, reference_date_str=reference_date_str)
    report = make_report(monthly_records)
    save_report(report=report, reference_date_str=reference_date_str)

if __name__ == "__main__":
    monthly_report()