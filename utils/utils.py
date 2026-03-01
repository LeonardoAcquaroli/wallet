import datetime
import requests
import os
import time
import json
import pandas as pd
from config.filters import SPESE, INCOME, RIMBORSI, INVESTIMENTI, BUONI_PASTO
from config.queries import INSERT_MONTHLY_FINANCIAL_UPDATE, SELECT_FUNDS, GET_PREVIOUS_SALDO, INSERT_SALDO
from dotenv import load_dotenv
from utils.db_utils import DBUtils
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

    svincolati = round(income_amount + rimborsi_amount + spese_amount, 2)

    report = {
        "svincolati_details": {
            "spese": spese_amount,
            "income": income_amount,
            "rimborsi": rimborsi_amount,
        },
        "buoni_pasto": buoni_pasto_amount,
        "svincolati": svincolati,
        "investimenti": investimenti_amount
    }

    return report

def save_report(report: dict, reference_date_str: str):
    DBUtils.initialize_pool()

    first_day_prev, _ = get_previous_month_range(reference_date_str)
    # first_day_prev is already in YYYY-MM-01 format from get_previous_month_range
    ref_month = first_day_prev[:10]
    
    # Get fund mappings from the database
    try:
        funds_data = DBUtils.execute_query(SELECT_FUNDS)
        # Create a mapping dictionary. e.g. {'svincolati': '0001', 'investimenti': '0002'}
        funds_map = {row[1]: row[0] for row in funds_data}
    except Exception as e:
        print(f"Error fetching funds: {e}")
        funds_map = {}

    svincolati_details = {
        "text": "",
        "components": {
            "spese": float(report.get("svincolati_details", {}).get("spese", 0.0)),
            "income": float(report.get("svincolati_details", {}).get("income", 0.0)),
            "rimborsi": float(report.get("svincolati_details", {}).get("rimborsi", 0.0))
        }
    }
    
    # Use the mapping to get the correct fund_id, fallback to hardcoded if not found
    records = [
        (ref_month, funds_map.get("svincolati", "0001"), float(report.get("svincolati", 0.0)), json.dumps(svincolati_details)),
        (ref_month, funds_map.get("investimenti", "0002"), float(report.get("investimenti", 0.0)), None),
        (ref_month, funds_map.get("buoni_pasto", "0003"), float(report.get("buoni_pasto", 0.0)), None)
    ]
    
    for row in records:
        print(f"Saving fund {row[1]} for month {row[0]}: {row[2]}")
        DBUtils.execute_update(INSERT_MONTHLY_FINANCIAL_UPDATE, row)
        
    save_saldo(ref_month, float(report.get("svincolati", 0.0)) + float(report.get("investimenti", 0.0)) + float(report.get("buoni_pasto", 0.0)))

    DBUtils.close_pool()

def save_saldo(ref_month: str, monthly_sum: float):
    # Fetch the previous month's saldo
    previous_saldo = 0.0
    try:
        result = DBUtils.execute_query(GET_PREVIOUS_SALDO, (ref_month,))
        if result and len(result) > 0 and result[0][0] is not None:
            previous_saldo = float(result[0][0])
    except Exception as e:
        print(f"Error fetching previous saldo: {e}")
        
    new_saldo = previous_saldo + monthly_sum
    try:
        DBUtils.execute_update(INSERT_SALDO, (ref_month, new_saldo))
    except Exception as e:
        print(f"Error saving new saldo: {e}")

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