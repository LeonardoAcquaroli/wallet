import datetime
import requests
import os
import time
import pandas as pd
from config.filters import SPESE, INCOME, RIMBORSI, INVESTIMENTI, BUONI_PASTO
from dotenv import load_dotenv
load_dotenv()
WALLET_API_TOKEN = os.getenv("WALLET_API_TOKEN")

def get_previous_month_range(reference_date_str: str):
    # Parse and validate
    try:
        reference_date = datetime.date.fromisoformat(reference_date_str)
    except ValueError:
        raise ValueError(f"Invalid date format: '{reference_date_str}'. Expected YYYY-MM-DD.")

    if reference_date > datetime.date.today():
        raise ValueError(f"Reference date {reference_date_str} is in the future.")

    # Get previous month range
    first_day_of_ref_month = reference_date.replace(day=1)
    last_day_of_prev_month = (first_day_of_ref_month - datetime.timedelta(days=1))
    first_day_of_prev_month = (last_day_of_prev_month.replace(day=1))

    return first_day_of_prev_month.isoformat(), last_day_of_prev_month.isoformat()

def call_wallet_api(endpoint: str, args: dict = None, base_url = "https://rest.budgetbakers.com/wallet"):
    headers = {"Authorization": f"Bearer {WALLET_API_TOKEN}"}
    request_url = f"{base_url}/{endpoint}"
    # send the request with a payload of params
    response = requests.get(request_url, headers=headers, params=args)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
    
def make_report(records_df: pd.DataFrame):
    # Spese
    spese_df = records_df[records_df['category_id'].isin(SPESE['categories'].keys()) &
            (records_df['amount'] < 0)]
    spese_amount = round(spese_df.amount.sum(), 2)
    # Income
    income_df = records_df[records_df['category_id'].isin(INCOME['categories'].keys()) &
               (records_df['amount'] > 0)]
    income_amount = round(income_df.amount.sum(), 2)
    # Rimborsi
    rimborsi_df = records_df[records_df['category_id'].isin(RIMBORSI['categories'].keys()) &
               (records_df['amount'] > 0)]
    rimborsi_amount = round(rimborsi_df.amount.sum(), 2)
    # Investimenti
    investimenti_df = records_df[records_df['category_id'].isin(INVESTIMENTI['categories'].keys()) &
               (records_df['amount'] > 0)]
    investimenti_amount = round(investimenti_df.amount.sum(), 2)
    # Buoni pasto
    buoni_pasto_df = records_df[records_df['category_id'].isin(BUONI_PASTO['categories'].keys()) &
               (records_df['amount'] > 0)]
    buoni_pasto_amount = round(buoni_pasto_df.amount.sum(), 2)

    cash_flow = round(income_amount + rimborsi_amount + spese_amount, 2)

    report = {
        "cash_flow_details": {
            "spese": spese_amount,
            "income": income_amount,
            "rimborsi": rimborsi_amount,
        },
        "buoni_pasto": buoni_pasto_amount,
        "cash_flow": cash_flow,
        "investimenti": investimenti_amount
    }

    return report

def save_report(db_connection, report: dict, reference_date_str: str):
    print(report)
    pass

def get_records(accounts: dict, reference_date_str: str):
    
    first_day_of_prev_month, last_day_of_prev_month = get_previous_month_range(reference_date_str)
    print(f"Fetching records from {first_day_of_prev_month} to {last_day_of_prev_month}")

    records_df = pd.DataFrame()
    i = 0

    for account_name, account_id in accounts.items():
        while True:    
            n_records_retrieved = i * 100

            args = {
                    "accountId": account_id,
                    "recordDate": f"lte.{last_day_of_prev_month}",
                    "limit": 100,
                    "offset": n_records_retrieved
                }
            time.sleep(1)
            print(f"Fetching records for account {account_name} with offset {n_records_retrieved}")
            records = call_wallet_api("v1/api/records", args=args)

            if len(records['records']) > 0:
                account_records = records['records']
                for record in account_records:
                    cat_id = record['category']['id']
                    cat_name = record['category']['name']
                    date = record['recordDate']
                    amount = record['amount']["value"]
                    label_ids = [label['id'] for label in record.get('labels', [])]
                    label_names = [label['name'] for label in record.get('labels', [])]

                    new_row = {
                        "account": account_name,
                        "amount": amount,
                        "date": date,
                        "category_id": cat_id,
                        "category_name": cat_name,
                        "label_ids": label_ids,
                        "label_names": label_names
                    }
                    records_df = pd.concat([records_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                i += 1
            else:
                i = 0
                break
    
    records_df = records_df[records_df['date'] >= first_day_of_prev_month]
    return records_df