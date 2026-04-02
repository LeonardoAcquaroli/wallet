# Wallet Dashboard

A set of automated tools to extract your financial records from Wallet by Budgetbakers and visualize them locally.

## 1. Monthly Update

### Running the Monthly Report
To save the financial data from the previous month to your local database, run:
```bash
python services\monthly_report.py
```
*Note: By default, the script pulls data for the previous month. You can override this by passing the `--reference-date YYYY-MM-DD` argument.*

### Exploring the Dashboard
To view your data interactively, start the local dashboard:
```bash
uvicorn frontend.app:app --reload
```
Next, open your web browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) to view dynamic charts and summarized tables.

## 2. Filters and Categories Map

Data is broadly categorized to make the dashboard easy to read. The mapping from Budgetbakers' internal category UUIDs to our dashboard groups is configured in `config/filters.py`.

The format of each filter group is a Python dictionary with a display `name` and a `categories` mapping containing the target Budgetbakers UUIDs and their labels:

```python
SPESE = {
    "name": "Spese senza investimenti and fees",
    "categories": {
        "025dcc04-511a-48a7-9d54-9c8330ec7fb3": "Bellezza & Benessere",
        "06b45615-a7d0-4f00-8992-95d6f9907c55": "Spesa",
        # ... other mapped UUIDs
    }
}
```

The main groups are:
- **SPESE**: Regular expenses, excluding fees and investments.
- **INCOME**: All forms of income, including salary and bonuses.
- **RIMBORSI**: Refunds.
- **INVESTIMENTI**: Investments, financial fees, and taxes.
- **BUONI_PASTO**: Meal vouchers.

You can freely update these dictionaries in `config/filters.py` to match your personal Wallet setup.

## 3. Backward Fill
*(Only needed for first-time use after using Wallet by Budgetbakers without this custom dashboard)*

If you have historical data in the Wallet app that hasn't been pulled into your database yet, you can backfill it using:
```bash
python backward_fill.py
```
This script loops through past months and sequentially runs the monthly report generation, building a complete historical dataset for your dashboard.

You can customize the script's generation boundaries using the following arguments:
- `--start-date YYYY-MM-DD`: The starting reference date. Months prior to or equal to this date will be skipped.
- `--end-date YYYY-MM-DD`: The end reference date. The script stops when it reaches this date (defaults to yesterday).

## 4. Database Schema

For hosting your database, we highly recommend using [Supabase](https://supabase.com/) as your PostgreSQL provider. It integrates seamlessly and provides an intuitive platform for managing your data. 

The application relies on the following database schema structure:

### `monthly_financial_update`
Stores the aggregated transaction data for a specific financial fund, accumulated per month.
* `ref_month` (date) **[PK]**
* `fund_id` (int8) **[PK]** - *Foreign Key to `funds.fund_id`*
* `amount` (float4)
* `details` (json)
* `created_at` (timestamptz)
* `updated_at` (timestamptz)

### `funds`
Stores the names and identifiers of the aggregate categories/funds.
* `fund_id` (int8) **[PK]**
* `fund_name` (varchar)
* `created_at` (timestamptz)
* `updated_at` (timestamptz)

### `saldo`
Tracks the global balance for each month.
* `ref_month` (date) **[PK]**
* `amount` (float4)
* `created_at` (timestamptz)
* `updated_at` (timestamptz)

## 5. Environment Variables

Before running any script, ensure you have the following environment variables set up (for example, in a `.env` file):
- `WALLET_API_TOKEN`: Your personal API token for Wallet by Budgetbakers.
- DB env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## 6. Historical Balances (Saldo)

When executing historical analysis, you should create the `saldo_old.csv` file by copying the `saldo_old_template.csv` template. Inside `saldo_old.csv`, insert the total combined amount of all your accounts at the end of each respective month in the past.