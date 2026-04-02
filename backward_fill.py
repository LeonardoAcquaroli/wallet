import argparse
import datetime
from services.monthly_report import monthly_report

def main():
    parser = argparse.ArgumentParser(description="Backward fill monthly reports.")
    parser.add_argument(
        "--start-date", 
        type=str, 
        help="Start reference date (YYYY-MM-DD). Months before or equal to this date will be skipped."
    )
    parser.add_argument(
        "--end-date", 
        type=str, 
        default=None, 
        help="End reference date (YYYY-MM-DD). Stops when reaching this date. Defaults to yesterday."
    )
    args = parser.parse_args()

    start_date = args.start_date
    if args.end_date:
        end_date = args.end_date
    else:
        end_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # Determine start year from start_date. Default to 2022 if something fails.
    try:
        start_year = int(start_date.split('-')[0])
    except (ValueError, AttributeError):
        raise ValueError("Invalid start date format. Use YYYY-MM-DD.")

    try:
        end_year = int(end_date.split('-')[0])
    except (ValueError, AttributeError):
        raise ValueError("Invalid end date format. Use YYYY-MM-DD.")

    break_condition = False
    for year in range(start_year, end_year + 1):
        if break_condition:
            break

        for month in range(1, 13):
            reference_date_str = f"{year}-{month:02d}-01"
            
            if reference_date_str >= end_date:
                print(f"Reached end date {reference_date_str}, stopping.")
                break_condition = True
                break

            if reference_date_str <= start_date:
                print(f"Skipping month {reference_date_str} as it's before or equal to {start_date}.")
                continue

            print(f"Generating report for the month previous to {reference_date_str}")
            monthly_report(reference_date_str=reference_date_str)

if __name__ == "__main__":
    main()