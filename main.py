from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from datetime import datetime
import os

from database import db, pegy_collection, init_db
from models import PEGYInput

app = FastAPI(title="PEGY Ratio Calculator")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------- Startup ----------------------
@app.on_event("startup")
async def startup():
    await init_db()

# ---------------------- Pages ----------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with inline HTML"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PEGY Ratio Calculator</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/static/icon-192.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: white; padding: 20px; font-family: Arial; }
        .card { background: #1e293b; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
        .form-control, .form-select { background: #334155; color: white; border: 1px solid #475569; padding: 10px; border-radius: 8px; width: 100%; }
        .form-control:focus { background: #334155; color: white; outline: none; }
        label { font-weight: 600; margin-top: 10px; display: block; }
        .btn-primary { background: #3b82f6; border: none; padding: 12px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; color: white; font-size: 16px; }
        .btn-primary:hover { background: #2563eb; }
        .btn-danger { background: #e74c3c; border: none; color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #334155; padding: 12px; text-align: left; }
        td { padding: 12px; border-bottom: 1px solid #334155; }
        .install-btn { background: #10b981; color: white; padding: 10px 20px; border-radius: 20px; border: none; cursor: pointer; display: none; margin-bottom: 15px; font-size: 14px; }
        h1 { text-align: center; margin-bottom: 25px; }
        h4 { margin-bottom: 20px; }
        .row { display: flex; flex-wrap: wrap; gap: 15px; }
        .col-md-6 { flex: 1 1 48%; }
        .col-md-3 { flex: 1 1 23%; }
        .col-md-4 { flex: 1 1 31%; }
        @media (max-width: 768px) {
            .col-md-6, .col-md-3, .col-md-4 { flex: 1 1 100%; }
        }
    </style>
</head>
<body>
    <div class="container" style="max-width: 900px; margin: 0 auto;">
        <h1>📊 PEGY Ratio Calculator</h1>
        
        <div style="text-align: center;">
            <button id="installBtn" class="install-btn">📲 Install App</button>
        </div>

        <div class="card">
            <h4>📝 Input Stock Data</h4>
            <form id="pegyForm">
                <div class="row">
                    <div class="col-md-6">
                        <label>Symbol *</label>
                        <input type="text" class="form-control" id="symbol" placeholder="e.g., CITYBANK" required>
                    </div>
                    <div class="col-md-3">
                        <label>EPS *</label>
                        <input type="number" step="0.01" class="form-control" id="eps" placeholder="0.00" required>
                    </div>
                    <div class="col-md-3">
                        <label>EPS Period *</label>
                        <select class="form-select" id="epsPeriod" required>
                            <option value="annual">Annual</option>
                            <option value="quarterly">Quarterly</option>
                        </select>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-4">
                        <label>Dividend Yield (%) *</label>
                        <input type="number" step="0.01" class="form-control" id="dividendYield" placeholder="5.60" required>
                    </div>
                    <div class="col-md-4">
                        <label>EPS Growth 3Yr (%)</label>
                        <input type="number" step="0.01" class="form-control" id="epsGrowth" placeholder="11.70">
                    </div>
                    <div class="col-md-4">
                        <label>Current Price *</label>
                        <input type="number" step="0.01" class="form-control" id="currentPrice" placeholder="25.00" required>
                    </div>
                </div>
                <button type="submit" class="btn-primary mt-3">📊 Calculate PEGY</button>
            </form>
        </div>

        <div class="card">
            <h4>📊 PEGY Rankings (Lowest = Best Value)</h4>
            <div style="overflow-x: auto;">
                <table id="resultTable">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>EPS</th>
                            <th>Div Yield</th>
                            <th>Growth</th>
                            <th>P/E</th>
                            <th>PEG</th>
                            <th>PEGY</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="9" style="text-align: center; color: #94a3b8;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        var deferredPrompt;
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installBtn').style.display = 'inline-block';
        });

        document.getElementById('installBtn').addEventListener('click', async function() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                var result = await deferredPrompt.userChoice;
                if (result.outcome === 'accepted') {
                    document.getElementById('installBtn').style.display = 'none';
                }
                deferredPrompt = null;
            }
        });

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js');
        }

        async function loadRecords() {
            var res = await fetch('/api/records');
            var records = await res.json();
            var tbody = document.getElementById('tableBody');
            
            if (records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #94a3b8;">No records yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = records.map(function(r) {
                return '<tr>' +
                    '<td><strong>' + r.symbol + '</strong></td>' +
                    '<td>' + (r.eps ? r.eps.toFixed(2) : '-') + '</td>' +
                    '<td>' + (r.dividend_yield ? r.dividend_yield.toFixed(2) + '%' : '-') + '</td>' +
                    '<td>' + (r.eps_growth ? r.eps_growth.toFixed(2) + '%' : 'N/A') + '</td>' +
                    '<td>' + (r.pe_ratio ? r.pe_ratio.toFixed(2) : '-') + '</td>' +
                    '<td>' + (r.peg_ratio ? r.peg_ratio.toFixed(2) : 'N/A') + '</td>' +
                    '<td><strong style="color: ' + r.color + ';">' + (r.pegy_ratio ? r.pegy_ratio.toFixed(2) : 'N/A') + '</strong></td>' +
                    '<td><span style="background: ' + r.color + '; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">' + (r.status ? r.status.split(' - ')[0] : '-') + '</span></td>' +
                    '<td><button onclick="deleteRecord(\'' + r._id + '\')" class="btn-danger">🗑</button></td>' +
                '</tr>';
            }).join('');
        }

        document.getElementById('pegyForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            var btn = this.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '⏳ Calculating...';
            
            var data = {
                symbol: document.getElementById('symbol').value.toUpperCase(),
                eps: parseFloat(document.getElementById('eps').value),
                eps_period: document.getElementById('epsPeriod').value,
                dividend_yield: parseFloat(document.getElementById('dividendYield').value),
                eps_growth: parseFloat(document.getElementById('epsGrowth').value) || null,
                current_price: parseFloat(document.getElementById('currentPrice').value),
            };
            
            try {
                var res = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (res.ok) {
                    document.getElementById('pegyForm').reset();
                    loadRecords();
                } else {
                    var err = await res.json();
                    alert('Error: ' + (err.detail || 'Failed'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
            
            btn.disabled = false;
            btn.innerHTML = '📊 Calculate PEGY';
        });

        async function deleteRecord(id) {
            if (!confirm('Delete this record?')) return;
            var res = await fetch('/api/records/' + id, { method: 'DELETE' });
            if (res.ok) loadRecords();
        }

        loadRecords();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)

# ---------------------- API ----------------------
@app.post("/api/calculate")
async def calculate_pegy(data: PEGYInput):
    """Calculate PEGY Ratio and save to database"""
    
    pe_ratio = round(data.current_price / data.eps, 2)
    
    if data.eps_period == "quarterly":
        annual_eps = data.eps * 4
        pe_ratio = round(data.current_price / annual_eps, 2)
    else:
        annual_eps = data.eps
    
    peg_ratio = None
    if data.eps_growth and data.eps_growth > 0:
        peg_ratio = round(pe_ratio / data.eps_growth, 2)
    
    pegy_ratio = None
    if data.eps_growth and data.eps_growth > 0:
        total_return = data.eps_growth + data.dividend_yield
        if total_return > 0:
            pegy_ratio = round(pe_ratio / total_return, 2)
    
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
    try:
        result = await pegy_collection.delete_one({"_id": ObjectId(record_id)})
        if result.deleted_count:
            return {"message": "Deleted successfully"}
        raise HTTPException(404, "Record not found")
    except:
        raise HTTPException(400, "Invalid ID")

# ---------------------- Manifest ----------------------
@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
