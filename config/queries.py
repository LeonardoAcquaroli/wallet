# queries.py
INSERT_MONTHLY_FINANCIAL_UPDATE = """
    INSERT INTO monthly_financial_update (ref_month, fund_id, amount, details)
    VALUES (%s, %s, %s, %s)
"""

SELECT_FUNDS = "SELECT fund_id, fund_name FROM funds"

GET_PREVIOUS_SALDO = """
    SELECT amount 
    FROM saldo 
    WHERE ref_month < %s 
    ORDER BY ref_month DESC 
    LIMIT 1
"""

INSERT_SALDO = """
    INSERT INTO saldo (ref_month, amount)
    VALUES (%s, %s)
"""
