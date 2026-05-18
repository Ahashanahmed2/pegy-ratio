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
    <title>PEGY Calculator</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/static/icon-192.png">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background:#0f172a; color:white; padding:10px; font-family:Arial,sans-serif; }
        .card { background:#1e293b; border-radius:15px; padding:15px; margin-bottom:15px; border:1px solid #334155; }
        input, select { background:#334155; color:white !important; border:1px solid #475569; padding:14px; border-radius:10px; width:100%; font-size:16px; margin-top:8px; }
        input:focus, select:focus { outline:none; border-color:#3b82f6; }
        input::placeholder { color:#94a3b8; }
        input[readonly] { background:#1a2744; font-weight:bold; font-size:18px; }
        label { font-weight:600; margin-top:12px; display:block; color:#e2e8f0; font-size:14px; }
        .btn-submit { background:#3b82f6; border:none; padding:16px; font-weight:bold; border-radius:10px; width:100%; color:white; font-size:18px; margin-top:20px; cursor:pointer; }
        .btn-submit:active { background:#2563eb; }
        .btn-delete { background:#e74c3c; border:none; color:white; padding:8px 12px; border-radius:6px; cursor:pointer; font-size:14px; }
        table { width:100%; border-collapse:collapse; margin-top:10px; font-size:12px; }
        th { background:#334155; padding:8px 6px; text-align:left; font-size:11px; color:#e2e8f0; }
        td { padding:8px 6px; border-bottom:1px solid #334155; font-size:12px; }
        .install-btn { background:#10b981; color:white; padding:14px; border-radius:30px; border:none; cursor:pointer; display:none; margin-bottom:10px; font-size:16px; font-weight:bold; width:100%; }
        h1 { text-align:center; margin-bottom:15px; font-size:22px; }
        h4 { margin-bottom:10px; font-size:16px; }
    </style>
</head>
<body>
    <div style="max-width:600px;margin:0 auto;">
        <h1>📊 PEGY Calculator</h1>
        
        <button id="installBtn" class="install-btn" onclick="installApp()">📲 Install App</button>

        <div class="card">
            <h4>📝 Input Data</h4>
            <form id="pegyForm" autocomplete="off" onsubmit="return false;">
                <label>🏷️ Symbol *</label>
                <input type="text" id="symbol" placeholder="CITYBANK" required>
                
                <label>📅 Period *</label>
                <select id="epsPeriod" required>
                    <option value="annual">📆 Annual</option>
                    <option value="quarterly">📋 Quarterly</option>
                </select>
                
                <label>💹 Current Price *</label>
                <input type="number" step="0.01" id="currentPrice" placeholder="25.00" required>
                
                <label>📊 Current EPS *</label>
                <input type="number" step="0.01" id="epsCurrent" placeholder="4.88" required oninput="calcGrowth()">
                
                <label>📊 Old EPS (3Yr Ago) *</label>
                <input type="number" step="0.01" id="epsOld" placeholder="3.50" required oninput="calcGrowth()">
                
                <label>📈 EPS Growth 3Yr (%)</label>
                <input type="text" id="epsGrowth" placeholder="Auto" readonly>
                
                <label>💵 Dividend Yield (%) *</label>
                <input type="number" step="0.01" id="dividendYield" placeholder="5.60" required>
            </form>
            <button class="btn-submit" id="submitBtn" onclick="submitData()">📊 Calculate PEGY</button>
        </div>

        <div class="card">
            <h4>📊 Rankings</h4>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr><th>Symbol</th><th>EPS</th><th>Old</th><th>Grw</th><th>Div</th><th>P/E</th><th>PEG</th><th>PEGY</th><th>Status</th><th></th></tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="10" style="text-align:center;color:#94a3b8;padding:20px;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function calcGrowth() {
            var c = parseFloat(document.getElementById('epsCurrent').value);
            var o = parseFloat(document.getElementById('epsOld').value);
            var f = document.getElementById('epsGrowth');
            if (c > 0 && o > 0) {
                var g = (Math.pow((c/o), (1/3)) - 1) * 100;
                f.value = g.toFixed(2) + '%';
                f.style.color = g >= 0 ? '#27ae60' : '#e74c3c';
            } else {
                f.value = '';
                f.style.color = '#e2e8f0';
            }
        }

        var deferredPrompt;
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installBtn').style.display = 'block';
        });
        function installApp() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(r) {
                    if (r.outcome === 'accepted') document.getElementById('installBtn').style.display = 'none';
                    deferredPrompt = null;
                });
            }
        }
        if (window.matchMedia('(display-mode: standalone)').matches) {
            document.getElementById('installBtn').style.display = 'none';
        }

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js');
        }

        function loadRecords() {
            fetch('/api/records')
            .then(function(r) { return r.json(); })
            .then(function(records) {
                var t = document.getElementById('tableBody');
                if (!records || records.length === 0) {
                    t.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#94a3b8;padding:20px;">No records</td></tr>';
                    return;
                }
                var h = '';
                for (var i=0; i<records.length; i++) {
                    var r = records[i];
                    var gc = (r.eps_growth != null && r.eps_growth >= 0) ? '#27ae60' : '#e74c3c';
                    h += '<tr>' +
                        '<td><b style="color:#60a5fa;">' + (r.symbol||'-') + '</b></td>' +
                        '<td>' + (r.eps!=null ? Number(r.eps).toFixed(2) : '-') + '</td>' +
                        '<td>' + (r.eps_old!=null ? Number(r.eps_old).toFixed(2) : '-') + '</td>' +
                        '<td style="color:'+gc+';">' + (r.eps_growth!=null ? Number(r.eps_growth).toFixed(2)+'%' : '-') + '</td>' +
                        '<td>' + (r.dividend_yield!=null ? Number(r.dividend_yield).toFixed(2)+'%' : '-') + '</td>' +
                        '<td>' + (r.pe_ratio!=null ? Number(r.pe_ratio).toFixed(2) : '-') + '</td>' +
                        '<td>' + (r.peg_ratio!=null ? Number(r.peg_ratio).toFixed(2) : '-') + '</td>' +
                        '<td><b style="color:'+(r.color||'#fff')+';">' + (r.pegy_ratio!=null ? Number(r.pegy_ratio).toFixed(2) : '-') + '</b></td>' +
                        '<td><span style="background:'+(r.color||'#95a5a6')+';color:white;padding:2px 8px;border-radius:8px;font-size:11px;">' + (r.status ? r.status.split(' - ')[0] : '-') + '</span></td>' +
                        '<td><button class="btn-delete" onclick="delRecord(\'' + r._id + '\')">🗑</button></td>' +
                    '</tr>';
                }
                t.innerHTML = h;
            });
        }

        function submitData() {
            var btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.innerHTML = '⏳ Wait...';
            
            var gr = document.getElementById('epsGrowth').value.replace('%', '');
            
            var data = {
                symbol: document.getElementById('symbol').value.toUpperCase().trim(),
                eps: parseFloat(document.getElementById('epsCurrent').value),
                eps_old: parseFloat(document.getElementById('epsOld').value) || null,
                eps_period: document.getElementById('epsPeriod').value,
                eps_growth: parseFloat(gr) || null,
                dividend_yield: parseFloat(document.getElementById('dividendYield').value),
                current_price: parseFloat(document.getElementById('currentPrice').value)
            };
            
            fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(function(r) {
                if (r.ok) return r.json();
                return r.json().then(function(e) { throw new Error(e.detail || 'Failed'); });
            })
            .then(function() {
                document.getElementById('pegyForm').reset();
                document.getElementById('epsPeriod').value = 'annual';
                document.getElementById('epsGrowth').value = '';
                loadRecords();
            })
            .catch(function(e) {
                alert('Error: ' + e.message);
            })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = '📊 Calculate PEGY';
            });
        }

        function delRecord(id) {
            if (!confirm('Delete?')) return;
            fetch('/api/records/' + id, { method: 'DELETE' })
            .then(function(r) { if (r.ok) loadRecords(); });
        }

        loadRecords();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)

# ---------------------- Health Check ----------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "PEGY Calculator is running"}

@app.head("/health")
async def health_check_head():
    return HTMLResponse(content="", status_code=200)

# ---------------------- API ----------------------
@app.post("/api/calculate")
async def calculate_pegy(data: PEGYInput):
    """Calculate PEGY Ratio and save to database"""
    try:
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
            "eps_old": data.eps_old,
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
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/api/records")
async def get_records():
    """Get all records sorted by PEGY ratio (ascending)"""
    records = await pegy_collection.find().sort("pegy_ratio", 1).to_list(100)
    result = []
    for r in records:
        r["_id"] = str(r["_id"])
        result.append(r)
    return result

@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    """Delete a record"""
    try:
        obj_id = ObjectId(record_id)
        result = await pegy_collection.delete_one({"_id": obj_id})
        if result.deleted_count:
            return {"message": "Deleted successfully"}
        raise HTTPException(404, "Record not found")
    except Exception as e:
        raise HTTPException(400, f"Invalid ID: {str(e)}")

# ---------------------- Manifest ----------------------
@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json")

# ---------------------- Service Worker ----------------------
@app.get("/static/sw.js")
async def service_worker():
    sw_js = """
const CACHE_NAME = 'pegy-v8';
const ASSETS = ['/', '/static/manifest.json', '/static/icon-192.png', '/static/icon-512.png'];
self.addEventListener('install', (e) => { e.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(ASSETS))); self.skipWaiting(); });
self.addEventListener('activate', (e) => { e.waitUntil(clients.claim()); });
self.addEventListener('fetch', (e) => { e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request))); });
"""
    return HTMLResponse(content=sw_js, media_type="application/javascript")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)