import os
import sys
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional


# Add parent directory to path to import DBUtils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.db_utils import DBUtils
from frontend.helpers import get_all_funds, get_chart2_data, get_filtered_data

app = FastAPI()

# Mount frontend directory for static assets if needed
# app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")

@app.on_event("startup")
def startup():
    DBUtils.initialize_pool()

@app.on_event("shutdown")
def shutdown():
    DBUtils.close_pool()

@app.get("/")
def read_root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/api/funds")
def get_funds():
    return get_all_funds()

@app.get("/api/chart2")
def get_chart2():
    return get_chart2_data()

@app.get("/api/filtered_data")
def api_filtered_data(
    start_month: Optional[str] = None, 
    end_month: Optional[str] = None, 
    fund_id: Optional[str] = None
):
    return get_filtered_data(start_month, end_month, fund_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend.app:app", host="0.0.0.0", port=8000, reload=True)
