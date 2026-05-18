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
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f172a; color: white; padding: 15px; font-family: Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        .card { background: #1e293b; border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
        .form-control, .form-select { background: #334155; color: white !important; border: 1px solid #475569; padding: 14px; border-radius: 10px; width: 100%; font-size: 16px; -webkit-appearance: none; }
        .form-control:focus, .form-select:focus { background: #334155; color: white !important; outline: none; border-color: #3b82f6; }
        .form-control::placeholder { color: #94a3b8; }
        .form-control[readonly] { background: #1a2744 !important; font-weight: bold; font-size: 18px; cursor: default; }
        label { font-weight: 600; margin-top: 14px; margin-bottom: 6px; display: block; color: #e2e8f0; font-size: 14px; }
        .btn-primary { background: #3b82f6; border: none; padding: 16px; font-weight: bold; border-radius: 10px; cursor: pointer; width: 100%; color: white; font-size: 18px; margin-top: 20px; }
        .btn-primary:active { background: #2563eb; transform: scale(0.98); }
        .btn-primary:disabled { background: #64748b; cursor: not-allowed; }
        .btn-danger { background: #e74c3c; border: none; color: white; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-size: 16px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th { background: #334155; padding: 10px 8px; text-align: left; font-size: 12px; color: #e2e8f0; white-space: nowrap; }
        td { padding: 10px 8px; border-bottom: 1px solid #334155; font-size: 13px; }
        .install-btn { background: #10b981; color: white; padding: 14px 28px; border-radius: 30px; border: none; cursor: pointer; display: none; margin-bottom: 15px; font-size: 18px; font-weight: bold; width: 100%; max-width: 300px; }
        .install-btn:active { background: #059669; }
        h1 { text-align: center; margin-bottom: 20px; font-size: 24px; }
        .row { display: flex; flex-wrap: wrap; gap: 12px; }
        .col-md-6 { flex: 1 1 100%; }
        .col-md-3 { flex: 1 1 100%; }
        .col-md-4 { flex: 1 1 100%; }
        @media (min-width: 768px) {
            .col-md-6 { flex: 1 1 48%; }
            .col-md-3 { flex: 1 1 23%; }
            .col-md-4 { flex: 1 1 31%; }
            body { padding: 30px; }
        }
    </style>
</head>
<body>
    <div class="container" style="max-width: 950px; margin: 0 auto;">
        <h1>📊 PEGY Ratio Calculator</h1>
        
        <div style="text-align: center;">
            <button id="installBtn" class="install-btn" onclick="installApp()">📲 Install App</button>
        </div>

        <div class="card">
            <h4 style="margin-bottom: 15px;">📝 Input Stock Data</h4>
            <form id="pegyForm" autocomplete="off" onsubmit="handleSubmit(event); return false;">
                <div class="row">
                    <div class="col-md-6">
                        <label>🏷️ Symbol *</label>
                        <input type="text" class="form-control" id="symbol" placeholder="CITYBANK" required autocomplete="off">
                    </div>
                    <div class="col-md-3">
                        <label>📅 Period *</label>
                        <select class="form-select" id="epsPeriod" required>
                            <option value="annual">📆 Annual</option>
                            <option value="quarterly">📋 Quarterly</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label>💹 Price *</label>
                        <input type="number" step="0.01" class="form-control" id="currentPrice" placeholder="25.00" required>
                    </div>
                </div>

                <div class="row mt-2">
                    <div class="col-md-4">
                        <label>📊 Current EPS *</label>
                        <input type="number" step="0.01" class="form-control" id="epsCurrent" placeholder="4.88" required oninput="autoCalcGrowth()">
                    </div>
                    <div class="col-md-4">
                        <label>📊 Old EPS (3Yr) *</label>
                        <input type="number" step="0.01" class="form-control" id="epsOld" placeholder="3.50" required oninput="autoCalcGrowth()">
                    </div>
                    <div class="col-md-4">
                        <label>📈 Growth 3Yr (%)</label>
                        <input type="text" class="form-control" id="epsGrowth" placeholder="Auto" readonly>
                    </div>
                </div>

                <div class="row mt-2">
                    <div class="col-md-6">
                        <label>💵 Dividend Yield (%) *</label>
                        <input type="number" step="0.01" class="form-control" id="dividendYield" placeholder="5.60" required>
                    </div>
                </div>

                <button type="submit" class="btn-primary" id="submitBtn">📊 Calculate PEGY</button>
            </form>
        </div>

        <div class="card">
            <h4 style="margin-bottom: 15px;">📊 PEGY Rankings</h4>
            <div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
                <table id="resultTable">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>EPS</th>
                            <th>Old</th>
                            <th>Grow</th>
                            <th>Div</th>
                            <th>P/E</th>
                            <th>PEG</th>
                            <th>PEGY</th>
                            <th>Status</th>
                            <th>Del</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="10" style="text-align: center; color: #94a3b8; padding: 30px;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // ===== Auto Calculate EPS Growth =====
        function autoCalcGrowth() {
            var currentEps = parseFloat(document.getElementById('epsCurrent').value);
            var oldEps = parseFloat(document.getElementById('epsOld').value);
            var growthField = document.getElementById('epsGrowth');
            
            if (currentEps > 0 && oldEps > 0) {
                var growth = (Math.pow((currentEps / oldEps), (1/3)) - 1) * 100;
                growthField.value = growth.toFixed(2) + '%';
                growthField.style.color = growth >= 0 ? '#27ae60' : '#e74c3c';
            } else {
                growthField.value = '';
                growthField.style.color = '#e2e8f0';
            }
        }

        // ===== PWA Install =====
        var deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            deferredPrompt = e;
            var btn = document.getElementById('installBtn');
            if (btn) btn.style.display = 'block';
        });

        function installApp() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(result) {
                    if (result.outcome === 'accepted') {
                        document.getElementById('installBtn').style.display = 'none';
                    }
                    deferredPrompt = null;
                });
            } else {
                alert('Open in Chrome/Edge to install');
            }
        }

        if (window.matchMedia('(display-mode: standalone)').matches) {
            var btn = document.getElementById('installBtn');
            if (btn) btn.style.display = 'none';
        }

        // ===== Service Worker =====
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js');
        }

        // ===== Load Records =====
        function loadRecords() {
            fetch('/api/records')
                .then(function(res) { return res.json(); })
                .then(function(records) {
                    var tbody = document.getElementById('tableBody');
                    
                    if (!records || records.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #94a3b8; padding: 30px;">No records yet</td></tr>';
                        return;
                    }
                    
                    var html = '';
                    for (var i = 0; i < records.length; i++) {
                        var r = records[i];
                        var gc = (r.eps_growth != null && r.eps_growth >= 0) ? '#27ae60' : '#e74c3c';
                        html += '<tr>' +
                            '<td><strong style="color:#60a5fa;">' + (r.symbol || '-') + '</strong></td>' +
                            '<td>' + (r.eps != null ? Number(r.eps).toFixed(2) : '-') + '</td>' +
                            '<td>' + (r.eps_old != null ? Number(r.eps_old).toFixed(2) : '-') + '</td>' +
                            '<td style="color:' + gc + ';font-weight:bold;">' + (r.eps_growth != null ? Number(r.eps_growth).toFixed(2) + '%' : '-') + '</td>' +
                            '<td>' + (r.dividend_yield != null ? Number(r.dividend_yield).toFixed(2) + '%' : '-') + '</td>' +
                            '<td>' + (r.pe_ratio != null ? Number(r.pe_ratio).toFixed(2) : '-') + '</td>' +
                            '<td>' + (r.peg_ratio != null ? Number(r.peg_ratio).toFixed(2) : '-') + '</td>' +
                            '<td><strong style="color:' + (r.color || '#fff') + ';">' + (r.pegy_ratio != null ? Number(r.pegy_ratio).toFixed(2) : '-') + '</strong></td>' +
                            '<td><span style="background:' + (r.color || '#95a5a6') + ';color:white;padding:4px 8px;border-radius:10px;font-size:11px;font-weight:bold;">' + (r.status ? r.status.split(' - ')[0] : '-') + '</span></td>' +
                            '<td><button onclick="deleteRecord(\'' + r._id + '\')" class="btn-danger" style="padding:6px 10px;font-size:14px;">🗑</button></td>' +
                        '</tr>';
                    }
                    tbody.innerHTML = html;
                })
                .catch(function(error) {
                    console.error('Load error:', error);
                });
        }

        // ===== Form Submit Handler =====
        function handleSubmit(e) {
            if (e) e.preventDefault();
            
            var btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.innerHTML = '⏳ Calculating...';
            
            var growthRaw = document.getElementById('epsGrowth').value.replace('%', '');
            var growthVal = parseFloat(growthRaw) || null;
            
            var data = {
                symbol: document.getElementById('symbol').value.toUpperCase().trim(),
                eps: parseFloat(document.getElementById('epsCurrent').value),
                eps_old: parseFloat(document.getElementById('epsOld').value) || null,
                eps_period: document.getElementById('epsPeriod').value,
                eps_growth: growthVal,
                dividend_yield: parseFloat(document.getElementById('dividendYield').value),
                current_price: parseFloat(document.getElementById('currentPrice').value),
            };
            
            fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(function(res) {
                if (res.ok) return res.json();
                return res.json().then(function(err) { throw new Error(err.detail || 'Failed'); });
            })
            .then(function(result) {
                document.getElementById('pegyForm').reset();
                document.getElementById('epsPeriod').value = 'annual';
                document.getElementById('epsGrowth').value = '';
                document.getElementById('epsGrowth').style.color = '#e2e8f0';
                loadRecords();
            })
            .catch(function(error) {
                alert('Error: ' + error.message);
            })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = '📊 Calculate PEGY';
            });
            
            return false;
        }

        // ===== Delete Record =====
        function deleteRecord(id) {
            if (!confirm('Delete this record?')) return;
            fetch('/api/records/' + id, { method: 'DELETE' })
                .then(function(res) {
                    if (res.ok) loadRecords();
                });
        }

        // ===== Init =====
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
const CACHE_NAME = 'pegy-calc-v7';
const ASSETS = ['/', '/static/manifest.json', '/static/icon-192.png', '/static/icon-512.png'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => response || fetch(event.request))
    );
});
"""
    return HTMLResponse(content=sw_js, media_type="application/javascript")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)