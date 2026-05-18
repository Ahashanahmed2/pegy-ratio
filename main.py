from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from database import db, pegy_collection, init_db
from models import PEGYInput

app = FastAPI(title="PEGY Ratio Calculator")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.cache = None

# ---------------------- Startup ----------------------
@app.on_event("startup")
async def startup():
    await init_db()

# ---------------------- Pages ----------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------------- API ----------------------
@app.post("/api/calculate")
async def calculate_pegy(data: PEGYInput):
    """Calculate PEGY Ratio and save to database"""
    
    # Calculate P/E Ratio
    pe_ratio = round(data.current_price / data.eps, 2)
    
    # Adjust EPS if quarterly
    if data.eps_period == "quarterly":
        annual_eps = data.eps * 4
        pe_ratio = round(data.current_price / annual_eps, 2)
    else:
        annual_eps = data.eps
    
    # Calculate PEG Ratio
    peg_ratio = None
    if data.eps_growth and data.eps_growth > 0:
        peg_ratio = round(pe_ratio / data.eps_growth, 2)
    
    # Calculate PEGY Ratio
    pegy_ratio = None
    if data.eps_growth and data.eps_growth > 0:
        total_return = data.eps_growth + data.dividend_yield
        if total_return > 0:
            pegy_ratio = round(pe_ratio / total_return, 2)
    
    # Determine status and color
    if pegy_ratio is not None:
        if pegy_ratio < 1:
            status = "Excellent - Undervalued"
            color = "#27ae60"
        elif pegy_ratio < 2:
            status = "Good - Fairly Valued"
            color = "#2ecc71"
        elif pegy_ratio < 3:
            status = "Average - Slightly Overvalued"
            color = "#f39c12"
        else:
            status = "Poor - Highly Overvalued"
            color = "#e74c3c"
    else:
        status = "N/A - Need EPS Growth Rate"
        color = "#95a5a6"
    
    # Save to database
    doc = {
        "symbol": data.symbol.upper(),
        "eps": annual_eps if data.eps_period == "quarterly" else data.eps,
        "eps_period": data.eps_period,
        "dividend_yield": data.dividend_yield,
        "eps_growth": data.eps_growth,
        "current_price": data.current_price,
        "pe_ratio": pe_ratio,
        "peg_ratio": peg_ratio,
        "pegy_ratio": pegy_ratio,
        "status": status,
        "color": color,
        "created_at": datetime.utcnow(),
    }
    
    result = await pegy_collection.insert_one(doc)
    
    return {
        "id": str(result.inserted_id),
        "symbol": doc["symbol"],
        "pe_ratio": doc["pe_ratio"],
        "peg_ratio": doc["peg_ratio"],
        "pegy_ratio": doc["pegy_ratio"],
        "status": doc["status"],
        "color": doc["color"],
        "dividend_yield": doc["dividend_yield"],
        "eps_growth": doc["eps_growth"],
    }

@app.get("/api/records")
async def get_records():
    """Get all records sorted by PEGY ratio (ascending)"""
    records = await pegy_collection.find().sort("pegy_ratio", 1).to_list(100)
    for r in records:
        r["_id"] = str(r["_id"])
    return records

@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    """Delete a record"""
    from bson import ObjectId
    try:
        result = await pegy_collection.delete_one({"_id": ObjectId(record_id)})
        if result.deleted_count:
            return {"message": "Deleted successfully"}
        raise HTTPException(404, "Record not found")
    except:
        raise HTTPException(400, "Invalid ID")

# ---------------------- Manifest for PWA ----------------------
@app.get("/manifest.json")
async def manifest():
    from fastapi.responses import FileResponse
    return FileResponse("static/manifest.json")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
