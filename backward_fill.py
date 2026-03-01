from services.monthly_report import monthly_report
import datetime

break_condition = False
for year in range(2022, datetime.date.today().year+1):
    
    if break_condition:
        break

    for month in range(1, 13):
        reference_date_str = f"{year}-{month:02d}-01"
        
        if reference_date_str >= (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
            print(f"Reached current month {reference_date_str}, stopping.")
            break_condition = True
            break

        if reference_date_str <= "2025-12-01":
            print(f"Skipping month {reference_date_str} as it's before 2025-12-01.")
            continue

        print(f"Generating report for the month previous to {reference_date_str}")
        monthly_report(reference_date_str=reference_date_str)