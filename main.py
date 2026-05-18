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
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0f172a; color: white; font-family: Arial, sans-serif; }
        
        .navbar { background: #1e293b; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; position: sticky; top: 0; z-index: 100; }
        .navbar h3 { color: white; font-size: 18px; margin: 0; }
        .install-nav-btn { background: #10b981; color: white; padding: 10px 20px; border-radius: 25px; border: none; cursor: pointer; font-size: 14px; font-weight: bold; display: none; box-shadow: 0 4px 15px rgba(16,185,129,0.3); }
        .install-nav-btn:hover { background: #059669; }
        
        .container { max-width: 950px; margin: 0 auto; padding: 20px; }
        .card { background: #1e293b; border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 1px solid #334155; }
        .form-control, .form-select { background: #334155; color: white !important; border: 1px solid #475569; padding: 12px; border-radius: 8px; width: 100%; font-size: 16px; }
        .form-control:focus, .form-select:focus { background: #334155; color: white !important; outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.3); }
        .form-control::placeholder { color: #94a3b8; }
        .form-control[readonly] { background: #1a2744 !important; font-weight: bold; font-size: 18px; cursor: default; }
        label { font-weight: 600; margin-top: 12px; margin-bottom: 4px; display: block; color: #e2e8f0; font-size: 14px; }
        .btn-primary { background: #3b82f6; border: none; padding: 14px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; color: white; font-size: 16px; margin-top: 15px; }
        .btn-primary:hover { background: #2563eb; }
        .btn-primary:disabled { background: #64748b; cursor: not-allowed; }
        .btn-danger { background: #e74c3c; border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .btn-danger:hover { background: #c0392b; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #334155; padding: 12px; text-align: left; font-size: 13px; color: #e2e8f0; }
        td { padding: 12px; border-bottom: 1px solid #334155; font-size: 14px; }
        tr:hover { background: rgba(59,130,246,0.05); }
        h1 { text-align: center; margin-bottom: 25px; font-size: 28px; }
        h4 { margin-bottom: 20px; color: #e2e8f0; }
        .row { display: flex; flex-wrap: wrap; gap: 15px; }
        .col-md-6 { flex: 1 1 48%; min-width: 200px; }
        .col-md-3 { flex: 1 1 23%; min-width: 150px; }
        .col-md-4 { flex: 1 1 31%; min-width: 180px; }
        .badge-status { color: white; padding: 5px 14px; border-radius: 15px; font-size: 12px; font-weight: bold; white-space: nowrap; }
        
        @media (max-width: 768px) {
            .col-md-6, .col-md-3, .col-md-4 { flex: 1 1 100%; }
            h1 { font-size: 22px; }
            .navbar h3 { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h3>📊 PEGY Calculator</h3>
        <button id="installNavBtn" class="install-nav-btn" onclick="installApp()">📲 Install App</button>
    </div>

    <div class="container">
        <h1>📊 PEGY Ratio Calculator</h1>

        <div class="card">
            <h4>📝 Input Stock Data</h4>
            <form id="pegyForm" autocomplete="off">
                <div class="row">
                    <div class="col-md-6">
                        <label>🏷️ Symbol *</label>
                        <input type="text" class="form-control" id="symbol" placeholder="e.g., CITYBANK" required autocomplete="off">
                    </div>
                    <div class="col-md-3">
                        <label>📅 EPS Period *</label>
                        <select class="form-select" id="epsPeriod" required>
                            <option value="annual">📆 Annual</option>
                            <option value="quarterly">📋 Quarterly</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label>💹 Current Price *</label>
                        <input type="number" step="0.01" class="form-control" id="currentPrice" placeholder="e.g., 25.00" required>
                    </div>
                </div>

                <div class="row mt-2">
                    <div class="col-md-4">
                        <label>📊 Current EPS *</label>
                        <input type="number" step="0.01" class="form-control" id="epsCurrent" placeholder="e.g., 4.88" required oninput="autoCalcGrowth()">
                    </div>
                    <div class="col-md-4">
                        <label>📊 Old EPS (3 Years Ago) *</label>
                        <input type="number" step="0.01" class="form-control" id="epsOld" placeholder="e.g., 3.50" required oninput="autoCalcGrowth()">
                    </div>
                    <div class="col-md-4">
                        <label>📈 EPS Growth 3Yr (%)</label>
                        <input type="text" class="form-control" id="epsGrowth" placeholder="Auto calculated" readonly>
                    </div>
                </div>

                <div class="row mt-2">
                    <div class="col-md-6">
                        <label>💵 Dividend Yield (%) *</label>
                        <input type="number" step="0.01" class="form-control" id="dividendYield" placeholder="e.g., 5.60" required>
                    </div>
                </div>

                <button type="submit" class="btn-primary">📊 Calculate PEGY</button>
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
                            <th>Old EPS</th>
                            <th>Growth</th>
                            <th>Div Yield</th>
                            <th>P/E</th>
                            <th>PEG</th>
                            <th>PEGY</th>
                            <th>Status</th>
                            <th>Action</th>
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
            document.getElementById('installNavBtn').style.display = 'inline-block';
        });

        window.addEventListener('appinstalled', function() {
            document.getElementById('installNavBtn').style.display = 'none';
            deferredPrompt = null;
        });

        function installApp() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(result) {
                    if (result.outcome === 'accepted') {
                        document.getElementById('installNavBtn').style.display = 'none';
                    }
                    deferredPrompt = null;
                });
            } else {
                alert('Open in Chrome/Edge and try again.');
            }
        }

        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
            document.getElementById('installNavBtn').style.display = 'none';
        }

        // ===== Service Worker =====
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/static/sw.js').then(function(reg) {
                    console.log('SW registered:', reg.scope);
                }).catch(function(err) {
                    console.log('SW failed:', err);
                });
            });
        }

        // ===== Load Records =====
        function loadRecords() {
            fetch('/api/records')
                .then(function(res) { return res.json(); })
                .then(function(records) {
                    var tbody = document.getElementById('tableBody');
                    
                    if (!records || records.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #94a3b8; padding: 30px;">No records yet. Add your first stock!</td></tr>';
                        return;
                    }
                    
                    var html = '';
                    records.forEach(function(r) {
                        var growthColor = (r.eps_growth != null && r.eps_growth >= 0) ? '#27ae60' : '#e74c3c';
                        html += '<tr>' +
                            '<td><strong style="color:#60a5fa;">' + (r.symbol || '-') + '</strong></td>' +
                            '<td>' + (r.eps != null ? parseFloat(r.eps).toFixed(2) : '-') + '</td>' +
                            '<td>' + (r.eps_old != null ? parseFloat(r.eps_old).toFixed(2) : '-') + '</td>' +
                            '<td style="color:' + growthColor + ';font-weight:bold;">' + (r.eps_growth != null ? parseFloat(r.eps_growth).toFixed(2) + '%' : 'N/A') + '</td>' +
                            '<td>' + (r.dividend_yield != null ? parseFloat(r.dividend_yield).toFixed(2) + '%' : '-') + '</td>' +
                            '<td>' + (r.pe_ratio != null ? parseFloat(r.pe_ratio).toFixed(2) : '-') + '</td>' +
                            '<td>' + (r.peg_ratio != null ? parseFloat(r.peg_ratio).toFixed(2) : 'N/A') + '</td>' +
                            '<td><strong style="color: ' + (r.color || '#fff') + '; font-size: 16px;">' + (r.pegy_ratio != null ? parseFloat(r.pegy_ratio).toFixed(2) : 'N/A') + '</strong></td>' +
                            '<td><span class="badge-status" style="background: ' + (r.color || '#95a5a6') + ';">' + (r.status ? r.status.split(' - ')[0] : '-') + '</span></td>' +
                            '<td><button onclick="deleteRecord(\'' + r._id + '\')" class="btn-danger">🗑</button></td>' +
                        '</tr>';
                    });
                    tbody.innerHTML = html;
                })
                .catch(function(error) {
                    console.error('Load error:', error);
                    document.getElementById('tableBody').innerHTML = '<tr><td colspan="10" style="text-align: center; color: #e74c3c; padding: 30px;">Error loading records</td></tr>';
                });
        }

        // ===== Form Submit =====
        document.getElementById('pegyForm').addEventListener('submit', function(e) {
            e.preventDefault();
            var btn = this.querySelector('button[type="submit"]');
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
                console.log('Saved:', result);
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
        });

        // ===== Delete Record =====
        function deleteRecord(id) {
            if (!confirm('Delete this record?')) return;
            fetch('/api/records/' + id, { method: 'DELETE' })
                .then(function(res) {
                    if (res.ok) loadRecords();
                })
                .catch(function(error) {
                    alert('Error deleting record');
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
const CACHE_NAME = 'pegy-calc-v5';
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