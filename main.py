from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from datetime import datetime
import os

from database import db, pegy_collection, init_db
from models import PEGYInput

app = FastAPI(title="PEGY + Payout Calculator")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    await init_db()

# ===================== HOME PAGE =====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    records = await pegy_collection.find().sort("pegy_ratio", 1).to_list(100)
    for r in records:
        r["_id"] = str(r["_id"])
    
    table_rows = ""
    if records:
        for r in records:
            symbol = r.get('symbol', '-')
            eps_val = f"{r['eps']:.2f}" if r.get('eps') is not None else '-'
            dps_val = f"{r.get('dps', 0):.2f}" if r.get('dps') is not None else '-'
            payout_val = f"{r.get('payout_ratio', 0):.2f}%" if r.get('payout_ratio') is not None else '-'
            growth_val = f"{r['eps_growth']:.2f}%" if r.get('eps_growth') is not None else '-'
            div_val = f"{r['dividend_yield']:.2f}%" if r.get('dividend_yield') is not None else '-'
            pe_val = f"{r['pe_ratio']:.2f}" if r.get('pe_ratio') is not None else '-'
            peg_val = f"{r['peg_ratio']:.2f}" if r.get('peg_ratio') is not None else '-'
            pegy_val = f"{r['pegy_ratio']:.2f}" if r.get('pegy_ratio') is not None else '-'
            color = r.get('color', '#fff')
            status = (r.get('status') or '-').split(' - ')[0]
            gc = "#27ae60" if (r.get('eps_growth') is not None and r.get('eps_growth', 0) >= 0) else "#e74c3c"
            
            # Payout color
            po = r.get('payout_ratio')
            if po is not None:
                if 30 <= po <= 60: pc = "#27ae60"
                elif po < 80: pc = "#f39c12"
                else: pc = "#e74c3c"
            else: pc = "#94a3b8"
            
            table_rows += f"""<tr>
                <td><b style="color:#60a5fa;">{symbol}</b></td>
                <td>{eps_val}</td>
                <td>{dps_val}</td>
                <td style="color:{pc};font-weight:bold;">{payout_val}</td>
                <td style="color:{gc};">{growth_val}</td>
                <td>{div_val}</td>
                <td>{pe_val}</td>
                <td>{peg_val}</td>
                <td><b style="color:{color};">{pegy_val}</b></td>
                <td><span style="background:{color};color:white;padding:3px 8px;border-radius:10px;font-size:11px;">{status}</span></td>
                <td>
                    <a href="/edit/{r['_id']}" style="color:#3b82f6;text-decoration:none;margin-right:6px;">✏️</a>
                    <a href="/delete/{r['_id']}" style="color:#e74c3c;text-decoration:none;" onclick="return confirm('Delete?')">🗑</a>
                </td>
            </tr>"""
    else:
        table_rows = '<tr><td colspan="11" style="text-align:center;color:#94a3b8;padding:30px;">No records yet</td></tr>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PEGY + Payout Calculator</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/static/icon-192.png">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0f172a; color:white; padding:10px; font-family:Arial,sans-serif; }}
        .card {{ background:#1e293b; border-radius:15px; padding:15px; margin-bottom:15px; }}
        input, select {{ background:#334155; color:white; border:1px solid #475569; padding:14px; border-radius:10px; width:100%; font-size:16px; margin-top:6px; }}
        input:focus, select:focus {{ outline:none; border-color:#3b82f6; }}
        input::placeholder {{ color:#94a3b8; }}
        input[readonly] {{ background:#1a2744; font-weight:bold; }}
        label {{ font-weight:600; margin-top:12px; display:block; color:#e2e8f0; font-size:14px; }}
        .btn {{ background:#3b82f6; border:none; padding:16px; font-weight:bold; border-radius:10px; width:100%; color:white; font-size:18px; margin-top:20px; cursor:pointer; }}
        .btn:active {{ background:#2563eb; }}
        table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:10px; }}
        th {{ background:#334155; padding:6px 3px; text-align:left; font-size:9px; color:#e2e8f0; }}
        td {{ padding:6px 3px; border-bottom:1px solid #334155; font-size:10px; }}
        h1 {{ text-align:center; margin-bottom:15px; font-size:22px; }}
        h4 {{ margin-bottom:10px; font-size:15px; }}
        .install-btn {{ background:#10b981; color:white; padding:14px; border-radius:30px; border:none; cursor:pointer; display:none; margin-bottom:10px; font-size:16px; font-weight:bold; width:100%; }}
        .info-text {{ color:#94a3b8; font-size:11px; margin-top:2px; display:block; }}
    </style>
</head>
<body>
    <div style="max-width:650px;margin:0 auto;">
        <h1>📊 PEGY + Payout Calculator</h1>
        <button id="installBtn" class="install-btn" onclick="installApp()">📲 Install App</button>

        <div class="card">
            <h4>📝 Input Stock Data</h4>
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
                <input type="number" step="0.01" name="eps" id="eps" placeholder="4.88" required oninput="calcAll()">
                
                <label>📊 Old EPS (3Yr Ago) *</label>
                <input type="number" step="0.01" name="eps_old" id="epsOld" placeholder="3.50" required oninput="calcAll()">
                
                <label>📈 EPS Growth 3Yr (%)</label>
                <input type="text" id="epsGrowthDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="eps_growth" id="epsGrowthHidden">
                
                <label>💵 Dividend (%) *</label>
                <input type="number" step="0.01" id="dividendPercent" placeholder="14" required oninput="calcDPS()">
                <span class="info-text">DPS = (Dividend% ÷ 100) × 10</span>
                
                <label>📊 DPS (টাকায়)</label>
                <input type="text" id="dpsDisplay" placeholder="Auto: 1.40" readonly>
                <input type="hidden" name="dps" id="dpsHidden">
                
                <label>💵 Old Dividend (%)</label>
                <input type="number" step="0.01" id="dividendPercentOld" placeholder="10" oninput="calcDPS()">
                
                <label>📊 Old DPS (টাকায়)</label>
                <input type="text" id="dpsOldDisplay" placeholder="Auto: 1.00" readonly>
                <input type="hidden" name="dps_old" id="dpsOldHidden">
                
                <label>📊 Payout Ratio (%)</label>
                <input type="text" id="payoutDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="payout_ratio" id="payoutHidden">
                
                <label>📈 Payout CAGR 3Yr (%)</label>
                <input type="text" id="payoutCAGRDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="payout_cagr" id="payoutCAGRHidden">
                
                <label>💵 Dividend Yield (%) *</label>
                <input type="number" step="0.01" name="dividend_yield" placeholder="5.60" required>
                
                <button type="submit" class="btn">📊 Calculate All</button>
            </form>
        </div>

        <div class="card">
            <h4>📊 Rankings (Low PEGY = Best)</h4>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr><th>Sym</th><th>EPS</th><th>DPS</th><th>Pay%</th><th>Grw</th><th>Div%</th><th>P/E</th><th>PEG</th><th>PEGY</th><th>St</th><th>Act</th></tr>
                    </thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        var FACE_VALUE = 10;
        
        function calcDPS() {{
            var dp = parseFloat(document.getElementById('dividendPercent').value);
            var dpo = parseFloat(document.getElementById('dividendPercentOld').value);
            
            if (dp > 0) {{
                var dps = (dp / 100) * FACE_VALUE;
                document.getElementById('dpsDisplay').value = dps.toFixed(2);
                document.getElementById('dpsHidden').value = dps.toFixed(2);
            }} else {{
                document.getElementById('dpsDisplay').value = '';
                document.getElementById('dpsHidden').value = '';
            }}
            
            if (dpo > 0) {{
                var dpsOld = (dpo / 100) * FACE_VALUE;
                document.getElementById('dpsOldDisplay').value = dpsOld.toFixed(2);
                document.getElementById('dpsOldHidden').value = dpsOld.toFixed(2);
            }} else {{
                document.getElementById('dpsOldDisplay').value = '';
                document.getElementById('dpsOldHidden').value = '';
            }}
            
            calcPayout();
        }}
        
        function calcGrowth() {{
            var c = parseFloat(document.getElementById('eps').value);
            var o = parseFloat(document.getElementById('epsOld').value);
            var d = document.getElementById('epsGrowthDisplay');
            var h = document.getElementById('epsGrowthHidden');
            if (c > 0 && o > 0) {{
                var g = (Math.pow((c/o), (1/3)) - 1) * 100;
                d.value = g.toFixed(2) + '%';
                d.style.color = g >= 0 ? '#27ae60' : '#e74c3c';
                h.value = g.toFixed(2);
            }} else {{ d.value = ''; h.value = ''; d.style.color = '#e2e8f0'; }}
            calcPayout();
        }}
        
        function calcPayout() {{
            var eps = parseFloat(document.getElementById('eps').value);
            var dps = parseFloat(document.getElementById('dpsHidden').value);
            var dpsOld = parseFloat(document.getElementById('dpsOldHidden').value);
            var pd = document.getElementById('payoutDisplay');
            var ph = document.getElementById('payoutHidden');
            var cd = document.getElementById('payoutCAGRDisplay');
            var ch = document.getElementById('payoutCAGRHidden');
            
            if (eps > 0 && dps > 0) {{
                var payout = (dps / eps) * 100;
                pd.value = payout.toFixed(2) + '%';
                ph.value = payout.toFixed(2);
                if (payout >= 30 && payout <= 60) pd.style.color = '#27ae60';
                else if (payout < 80) pd.style.color = '#f39c12';
                else pd.style.color = '#e74c3c';
            }} else {{ pd.value = ''; ph.value = ''; pd.style.color = '#e2e8f0'; }}
            
            if (eps > 0 && dpsOld > 0 && dps > 0) {{
                var epsOld = parseFloat(document.getElementById('epsOld').value) || eps;
                if (epsOld > 0) {{
                    var oldPayout = (dpsOld / epsOld) * 100;
                    var newPayout = (dps / eps) * 100;
                    if (oldPayout > 0) {{
                        var cagr = (Math.pow((newPayout/oldPayout), (1/3)) - 1) * 100;
                        cd.value = cagr.toFixed(2) + '%';
                        ch.value = cagr.toFixed(2);
                        cd.style.color = cagr >= 0 ? '#27ae60' : '#e74c3c';
                    }}
                }}
            }} else {{ cd.value = ''; ch.value = ''; cd.style.color = '#e2e8f0'; }}
        }}
        
        function calcAll() {{
            calcGrowth();
            calcPayout();
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

# ===================== FORM SUBMIT =====================
@app.post("/submit")
async def submit_form(
    symbol: str = Form(...),
    eps: float = Form(...),
    eps_old: float = Form(None),
    eps_period: str = Form(...),
    eps_growth: float = Form(None),
    dps: float = Form(0),
    dps_old: float = Form(None),
    payout_ratio: float = Form(None),
    payout_cagr: float = Form(None),
    dividend_yield: float = Form(...),
    current_price: float = Form(...),
):
    try:
        pe_ratio = round(current_price / eps, 2)
        annual_eps = eps * 4 if eps_period == "quarterly" else eps
        if eps_period == "quarterly": pe_ratio = round(current_price / annual_eps, 2)
        
        peg_ratio = round(pe_ratio / eps_growth, 2) if (eps_growth and eps_growth > 0) else None
        
        pegy_ratio = None
        if eps_growth and eps_growth > 0:
            t = eps_growth + dividend_yield
            if t > 0: pegy_ratio = round(pe_ratio / t, 2)
        
        if pegy_ratio is not None:
            if pegy_ratio < 1: status, color = "Excellent", "#27ae60"
            elif pegy_ratio < 2: status, color = "Good", "#2ecc71"
            elif pegy_ratio < 3: status, color = "Average", "#f39c12"
            else: status, color = "Poor", "#e74c3c"
        else: status, color = "N/A", "#95a5a6"
        
        # Auto calculate payout ratio if not provided
        if payout_ratio is None and dps > 0 and eps > 0:
            payout_ratio = round((dps / eps) * 100, 2)
        
        await pegy_collection.insert_one({
            "symbol": symbol.upper(), "eps": annual_eps, "eps_old": eps_old,
            "eps_period": eps_period, "dps": dps, "dps_old": dps_old,
            "payout_ratio": payout_ratio, "payout_cagr": payout_cagr,
            "dividend_yield": dividend_yield, "eps_growth": eps_growth,
            "current_price": current_price, "pe_ratio": pe_ratio,
            "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "status": status, "color": color, "created_at": datetime.utcnow(),
        })
    except Exception as e:
        print(f"Submit Error: {e}")
    
    return RedirectResponse(url="/", status_code=303)

# ===================== EDIT PAGE =====================
@app.get("/edit/{record_id}", response_class=HTMLResponse)
async def edit_page(request: Request, record_id: str):
    try:
        record = await pegy_collection.find_one({"_id": ObjectId(record_id)})
        if not record: return RedirectResponse(url="/")
    except: return RedirectResponse(url="/")
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Record</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0f172a; color:white; padding:15px; font-family:Arial; }}
        .card {{ background:#1e293b; border-radius:15px; padding:20px; max-width:500px; margin:0 auto; }}
        input, select {{ background:#334155; color:white; border:1px solid #475569; padding:14px; border-radius:10px; width:100%; font-size:16px; margin-top:6px; }}
        label {{ font-weight:600; margin-top:14px; display:block; color:#e2e8f0; font-size:14px; }}
        .btn {{ background:#3b82f6; border:none; padding:16px; font-weight:bold; border-radius:10px; width:100%; color:white; font-size:18px; margin-top:20px; cursor:pointer; }}
        .btn-cancel {{ background:#64748b; border:none; padding:12px; border-radius:10px; width:100%; color:white; margin-top:8px; cursor:pointer; display:block; text-align:center; text-decoration:none; }}
    </style>
</head>
<body>
    <div class="card">
        <h3 style="margin-bottom:15px;">✏️ Edit: {record.get('symbol','')}</h3>
        <form method="POST" action="/update/{record_id}">
            <label>Symbol</label>
            <input type="text" name="symbol" value="{record.get('symbol','')}" required>
            <label>EPS</label>
            <input type="number" step="0.01" name="eps" value="{record.get('eps',0)}" required>
            <label>Old EPS</label>
            <input type="number" step="0.01" name="eps_old" value="{record.get('eps_old',0)}">
            <label>EPS Growth (%)</label>
            <input type="number" step="0.01" name="eps_growth" value="{record.get('eps_growth',0)}">
            <label>DPS</label>
            <input type="number" step="0.01" name="dps" value="{record.get('dps',0)}">
            <label>Old DPS</label>
            <input type="number" step="0.01" name="dps_old" value="{record.get('dps_old',0)}">
            <label>Payout Ratio (%)</label>
            <input type="number" step="0.01" name="payout_ratio" value="{record.get('payout_ratio',0)}">
            <label>Dividend Yield (%)</label>
            <input type="number" step="0.01" name="dividend_yield" value="{record.get('dividend_yield',0)}">
            <label>Current Price</label>
            <input type="number" step="0.01" name="current_price" value="{record.get('current_price',0)}">
            <button type="submit" class="btn">💾 Update</button>
        </form>
        <a href="/" class="btn-cancel">Cancel</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)

# ===================== UPDATE RECORD =====================
@app.post("/update/{record_id}")
async def update_record(
    record_id: str,
    symbol: str = Form(...),
    eps: float = Form(...),
    eps_old: float = Form(None),
    eps_growth: float = Form(None),
    dps: float = Form(0),
    dps_old: float = Form(None),
    payout_ratio: float = Form(None),
    dividend_yield: float = Form(...),
    current_price: float = Form(...),
):
    try:
        obj_id = ObjectId(record_id)
        pe_ratio = round(current_price / eps, 2)
        peg_ratio = round(pe_ratio / eps_growth, 2) if (eps_growth and eps_growth > 0) else None
        pegy_ratio = None
        if eps_growth and eps_growth > 0:
            t = eps_growth + dividend_yield
            if t > 0: pegy_ratio = round(pe_ratio / t, 2)
        
        if pegy_ratio is not None:
            if pegy_ratio < 1: status, color = "Excellent", "#27ae60"
            elif pegy_ratio < 2: status, color = "Good", "#2ecc71"
            elif pegy_ratio < 3: status, color = "Average", "#f39c12"
            else: status, color = "Poor", "#e74c3c"
        else: status, color = "N/A", "#95a5a6"
        
        await pegy_collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "symbol": symbol.upper(), "eps": eps, "eps_old": eps_old,
                "dps": dps, "dps_old": dps_old, "payout_ratio": payout_ratio,
                "eps_growth": eps_growth, "dividend_yield": dividend_yield,
                "current_price": current_price, "pe_ratio": pe_ratio,
                "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
                "status": status, "color": color,
            }}
        )
    except Exception as e:
        print(f"Update error: {e}")
    
    return RedirectResponse(url="/", status_code=303)

# ===================== DELETE =====================
@app.get("/delete/{record_id}")
async def delete_record(record_id: str):
    try: await pegy_collection.delete_one({"_id": ObjectId(record_id)})
    except: pass
    return RedirectResponse(url="/", status_code=303)

# ===================== HEALTH =====================
@app.get("/health")
async def health(): return {"status": "ok"}
@app.head("/health")
async def health_head(): return HTMLResponse(content="", status_code=200)

# ===================== API =====================
@app.post("/api/calculate")
async def calculate_pegy(data: PEGYInput):
    try:
        pe_ratio = round(data.current_price / data.eps, 2)
        if data.eps_period == "quarterly": pe_ratio = round(data.current_price / (data.eps * 4), 2)
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

# ===================== MANIFEST & SW =====================
@app.get("/manifest.json")
async def manifest(): return FileResponse("static/manifest.json")

@app.get("/static/sw.js")
async def service_worker():
    return HTMLResponse(content="""const CACHE_NAME='pegy-v11';self.addEventListener('install',(e)=>{e.waitUntil(caches.open(CACHE_NAME).then((c)=>c.addAll(['/','/static/manifest.json'])));self.skipWaiting();});self.addEventListener('activate',(e)=>{e.waitUntil(clients.claim());});self.addEventListener('fetch',(e)=>{e.respondWith(caches.match(e.request).then((r)=>r||fetch(e.request)));});""", media_type="application/javascript")

# ===================== RUN =====================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)