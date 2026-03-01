import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.db_utils import DBUtils

def get_all_funds():
    funds = DBUtils.execute_query("SELECT fund_id, fund_name FROM funds")
    return [{"fund_id": row[0], "fund_name": row[1]} for row in funds]

def get_chart2_data():
    query_m = """
        SELECT ref_month, SUM(amount)
        FROM monthly_financial_update
        GROUP BY ref_month  
    """
    results_m = DBUtils.execute_query(query_m)
    
    query_s = """
        SELECT ref_month, amount
        FROM saldo
    """
    results_s = DBUtils.execute_query(query_s)
    
    data_map = {}
    
    for row in results_m:
        month_str = str(row[0])[:7]  # YYYY-MM
        val = float(row[1]) if row[1] else 0.0
        if month_str not in data_map:
            data_map[month_str] = {"bar": 0.0, "line": None}
        data_map[month_str]["bar"] = val
        
    for row in results_s:
        month_str = str(row[0])[:7]  # YYYY-MM
        val = float(row[1]) if row[1] is not None else None
        if month_str not in data_map:
            data_map[month_str] = {"bar": 0.0, "line": None}
        data_map[month_str]["line"] = val
        
    labels = sorted(data_map.keys())
    bar_data = [data_map[lbl]["bar"] for lbl in labels]
    line_data = [data_map[lbl]["line"] for lbl in labels]
        
    return {
        "labels": labels,
        "bar_data": bar_data,
        "line_data": line_data
    }

def get_filtered_data(start_month: str = None, end_month: str = None, fund_id: str = None):
    # Base query for table and Chart 1
    # If no start_month and no end_month are provided, we should default to the last available month
    if not start_month and not end_month:
        try:
            last_month_res = DBUtils.execute_query("SELECT MAX(ref_month) FROM monthly_financial_update")
            if last_month_res and last_month_res[0][0]:
                last_m = str(last_month_res[0][0])[:7]
                start_month = last_m
                end_month = last_m
        except Exception:
            pass

    params = []
    conditions = []
    
    if start_month and start_month != "null" and start_month != "undefined":
        conditions.append("m.ref_month::varchar >= %s")
        params.append(f"{start_month}-01")
    if end_month and end_month != "null" and end_month != "undefined":
        conditions.append("m.ref_month::varchar <= %s")
        params.append(f"{end_month}-31")
    if fund_id and fund_id != "null" and fund_id != "undefined":
        conditions.append("m.fund_id::varchar = %s")
        params.append(str(fund_id))
        
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        
    query = f"""
        SELECT m.ref_month, m.fund_id, m.amount, m.details, f.fund_name
        FROM monthly_financial_update m
        LEFT JOIN funds f ON m.fund_id::varchar = f.fund_id::varchar
        {where_clause}
        ORDER BY m.ref_month ASC
    """
    
    results = DBUtils.execute_query(query, tuple(params) if params else None)
    
    table_data = []
    chart1_map = {}
    
    for row in results:
        month_str = str(row[0])[:7]
        amount = float(row[2]) if row[2] else 0.0
        fund_name = row[4]
        
        # Details might be a dict if parsed by psycopg2, or None
        details_val = row[3]
        if isinstance(details_val, dict):
            import json
            details_str = json.dumps(details_val)
        elif details_val:
            details_str = str(details_val)
        else:
            details_str = ""
            
        table_data.append({
            "ref_month": month_str,
            "fund_id": row[1],
            "amount": amount,
            "details": details_str,
            "fund_name": fund_name
        })
        
        if month_str not in chart1_map:
            chart1_map[month_str] = 0
        chart1_map[month_str] += amount
        
    chart1_labels = sorted(chart1_map.keys())
    chart1_values = [chart1_map[lbl] for lbl in chart1_labels]
    
    return {
        "table_data": table_data,
        "chart1_data": {
            "labels": chart1_labels,
            "values": chart1_values
        }
    }