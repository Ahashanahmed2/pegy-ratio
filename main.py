from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
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
    """Home page"""
    records = await pegy_collection.find().sort("pegy_ratio", 1).to_list(100)
    for r in records:
        r["_id"] = str(r["_id"])
    
    # Build table rows
    table_rows = ""
    if records:
        for r in records:
            symbol = r.get('symbol', '-')
            eps_val = f"{r['eps']:.2f}" if r.get('eps') is not None else '-'
            eps_old_val = f"{r['eps_old']:.2f}" if r.get('eps_old') is not None else '-'
            growth_val = f"{r['eps_growth']:.2f}%" if r.get('eps_growth') is not None else '-'
            div_val = f"{r['dividend_yield']:.2f}%" if r.get('dividend_yield') is not None else '-'
            pe_val = f"{r['pe_ratio']:.2f}" if r.get('pe_ratio') is not None else '-'
            peg_val = f"{r['peg_ratio']:.2f}" if r.get('peg_ratio') is not None else '-'
            pegy_val = f"{r['pegy_ratio']:.2f}" if r.get('pegy_ratio') is not None else '-'
            color = r.get('color', '#fff')
            status = r.get('status', '-')
            if ' - ' in status:
                status = status.split(' - ')[0]
            gc = "#27ae60" if (r.get('eps_growth') is not None and r['eps_growth'] >= 0) else "#e74c3c"
            
            table_rows += f"""<tr>
                <td><b style="color:#60a5fa;">{symbol}</b></td>
                <td>{eps_val}</td>
                <td>{eps_old_val}</td>
                <td style="color:{gc};font-weight:bold;">{growth_val}</td>
                <td>{div_val}</td>
                <td>{pe_val}</td>
                <td>{peg_val}</td>
                <td><b style="color:{color};">{pegy_val}</b></td>
                <td><span style="background:{color};color:white;padding:3px 10px;border-radius:10px;font-size:12px;">{status}</span></td>
                <td><a href="/delete/{r['_id']}" style="color:#e74c3c;text-decoration:none;font-size:18px;" onclick="return confirm('Delete?')">🗑</a></td>
            </tr>"""
    else:
        table_rows = '<tr><td colspan="10" style="text-align:center;color:#94a3b8;padding:30px;">No records yet</td></tr>'
    
    html = f"""<!DOCTYPE html>
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
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0f172a; color:white; padding:10px; font-family:Arial,sans-serif; }}
        .card {{ background:#1e293b; border-radius:15px; padding:15px; margin-bottom:15px; }}
        input, select {{ background:#334155; color:white; border:1px solid #475569; padding:14px; border-radius:10px; width:100%; font-size:16px; margin-top:8px; }}
        input:focus, select:focus {{ outline:none; border-color:#3b82f6; }}
        input::placeholder {{ color:#94a3b8; }}
        input[readonly] {{ background:#1a2744; font-weight:bold; font-size:18px; }}
        label {{ font-weight:600; margin-top:12px; display:block; color:#e2e8f0; font-size:14px; }}
        .btn {{ background:#3b82f6; border:none; padding:16px; font-weight:bold; border-radius:10px; width:100%; color:white; font-size:18px; margin-top:20px; cursor:pointer; }}
        .btn:active {{ background:#2563eb; }}
        table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:11px; }}
        th {{ background:#334155; padding:8px 4px; text-align:left; font-size:10px; color:#e2e8f0; }}
        td {{ padding:8px 4px; border-bottom:1px solid #334155; font-size:11px; }}
        h1 {{ text-align:center; margin-bottom:15px; font-size:22px; }}
        h4 {{ margin-bottom:10px; }}
        .install-btn {{ background:#10b981; color:white; padding:14px; border-radius:30px; border:none; cursor:pointer; display:none; margin-bottom:10px; font-size:16px; font-weight:bold; width:100%; }}
    </style>
</head>
<body>
    <div style="max-width:600px;margin:0 auto;">
        <h1>📊 PEGY Calculator</h1>
        <button id="installBtn" class="install-btn" onclick="installApp()">📲 Install App</button>

        <div class="card">
            <h4>📝 Input Data</h4>
            <form method="POST" action="/submit">
                <label>🏷️ Symbol *</label>
                <input type="text" name="symbol" placeholder="CITYBANK" required>
                <label>📅 Period *</label>
                <select name="eps_period" required>
                    <option value="annual">📆 Annual</option>
                    <option value="quarterly">📋 Quarterly</option>
                </select>
                <label>💹 Current Price *</label>
                <input type="number" step="0.01" name="current_price" placeholder="25.00" required>
                <label>📊 Current EPS *</label>
                <input type="number" step="0.01" name="eps" placeholder="4.88" required oninput="calcGrowth()">
                <label>📊 Old EPS (3Yr Ago) *</label>
                <input type="number" step="0.01" name="eps_old" placeholder="3.50" required oninput="calcGrowth()">
                <label>📈 EPS Growth 3Yr (%)</label>
                <input type="text" id="epsGrowthDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="eps_growth" id="epsGrowthHidden">
                <label>💵 Dividend Yield (%) *</label>
                <input type="number" step="0.01" name="dividend_yield" placeholder="5.60" required>
                <button type="submit" class="btn">📊 Calculate PEGY</button>
            </form>
        </div>

        <div class="card">
            <h4>📊 Rankings</h4>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr><th>Sym</th><th>EPS</th><th>Old</th><th>Grw</th><th>Div</th><th>P/E</th><th>PEG</th><th>PEGY</th><th>Stat</th><th>Del</th></tr>
                    </thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function calcGrowth() {{
            var c = parseFloat(document.querySelector('input[name="eps"]').value);
            var o = parseFloat(document.querySelector('input[name="eps_old"]').value);
            var d = document.getElementById('epsGrowthDisplay');
            var h = document.getElementById('epsGrowthHidden');
            if (c > 0 && o > 0) {{
                var g = (Math.pow((c/o), (1/3)) - 1) * 100;
                d.value = g.toFixed(2) + '%';
                d.style.color = g >= 0 ? '#27ae60' : '#e74c3c';
                h.value = g.toFixed(2);
            }} else {{
                d.value = '';
                h.value = '';
                d.style.color = '#e2e8f0';
            }}
        }}

        var dp;
        window.addEventListener('beforeinstallprompt', function(e) {{ e.preventDefault(); dp = e; document.getElementById('installBtn').style.display = 'block'; }});
        function installApp() {{ if (dp) {{ dp.prompt(); dp.userChoice.then(function(r) {{ if (r.outcome === 'accepted') document.getElementById('installBtn').style.display = 'none'; dp = null; }}); }} }}
        if (window.matchMedia('(display-mode: standalone)').matches) {{ document.getElementById('installBtn').style.display = 'none'; }}
        if ('serviceWorker' in navigator) {{ navigator.serviceWorker.register('/static/sw.js'); }}
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)

# ---------------------- Form Submit ----------------------
@app.post("/submit")
async def submit_form(
    symbol: str = Form(...),
    eps: float = Form(...),
    eps_old: float = Form(None),
    eps_period: str = Form(...),
    eps_growth: float = Form(None),
    dividend_yield: float = Form(...),
    current_price: float = Form(...),
):
    try:
        pe_ratio = round(current_price / eps, 2)
        if eps_period == "quarterly":
            annual_eps = eps * 4
            pe_ratio = round(current_price / annual_eps, 2)
        else:
            annual_eps = eps
        
        peg_ratio = None
        if eps_growth and eps_growth > 0:
            peg_ratio = round(pe_ratio / eps_growth, 2)
        
        pegy_ratio = None
        if eps_growth and eps_growth > 0:
            total_return = eps_growth + dividend_yield
            if total_return > 0:
                pegy_ratio = round(pe_ratio / total_return, 2)
        
        if pegy_ratio is not None:
            if pegy_ratio < 1: status, color = "Excellent", "#27ae60"
            elif pegy_ratio < 2: status, color = "Good", "#2ecc71"
            elif pegy_ratio < 3: status, color = "Average", "#f39c12"
            else: status, color = "Poor", "#e74c3c"
        else: status, color = "N/A", "#95a5a6"
        
        await pegy_collection.insert_one({
            "symbol": symbol.upper(), "eps": annual_eps if eps_period == "quarterly" else eps,
            "eps_old": eps_old, "eps_period": eps_period, "dividend_yield": dividend_yield,
            "eps_growth": eps_growth, "current_price": current_price,
            "pe_ratio": pe_ratio, "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "status": status, "color": color, "created_at": datetime.utcnow(),
        })
    except Exception as e:
        print(f"Error: {e}")
    
    return RedirectResponse(url="/", status_code=303)

# ---------------------- Delete ----------------------
@app.get("/delete/{record_id}")
async def delete_record(record_id: str):
    try:
        await pegy_collection.delete_one({"_id": ObjectId(record_id)})
    except:
        pass
    return RedirectResponse(url="/", status_code=303)

# ---------------------- Health ----------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.head("/health")
async def health_head():
    return HTMLResponse(content="", status_code=200)

# ---------------------- API ----------------------
@app.post("/api/calculate")
async def calculate_pegy(data: PEGYInput):
    try:
        pe_ratio = round(data.current_price / data.eps, 2)
        if data.eps_period == "quarterly":
            pe_ratio = round(data.current_price / (data.eps * 4), 2)
        peg_ratio = round(pe_ratio / data.eps_growth, 2) if (data.eps_growth and data.eps_growth > 0) else None
        pegy_ratio = None
        if data.eps_growth and data.eps_growth > 0:
            t = data.eps_growth + data.dividend_yield
            if t > 0: pegy_ratio = round(pe_ratio / t, 2)
        if pegy_ratio is not None:
            if pegy_ratio < 1: status, color = "Excellent", "#27ae60"
            elif pegy_ratio < 2: status, color = "Good", "#2ecc71"
            elif pegy_ratio < 3: status, color = "Average", "#f39c12"
            else: status, color = "Poor", "#e74c3c"
        else: status, color = "N/A", "#95a5a6"
        result = await pegy_collection.insert_one({
            "symbol": data.symbol.upper(), "eps": data.eps, "eps_old": data.eps_old,
            "eps_period": data.eps_period, "dividend_yield": data.dividend_yield,
            "eps_growth": data.eps_growth, "current_price": data.current_price,
            "pe_ratio": pe_ratio, "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "status": status, "color": color, "created_at": datetime.utcnow(),
        })
        return {"id": str(result.inserted_id), "pegy_ratio": pegy_ratio, "status": status, "color": color}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/api/records")
async def get_records():
    records = await pegy_collection.find().sort("pegy_ratio", 1).to_list(100)
    for r in records: r["_id"] = str(r["_id"])
    return records

# ---------------------- Manifest & SW ----------------------
@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json")

@app.get("/static/sw.js")
async def service_worker():
    return HTMLResponse(content="""const CACHE_NAME='pegy-v9';self.addEventListener('install',(e)=>{e.waitUntil(caches.open(CACHE_NAME).then((c)=>c.addAll(['/','/static/manifest.json'])));self.skipWaiting();});self.addEventListener('activate',(e)=>{e.waitUntil(clients.claim());});self.addEventListener('fetch',(e)=>{e.respondWith(caches.match(e.request).then((r)=>r||fetch(e.request)));});""", media_type="application/javascript")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)