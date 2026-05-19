from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from datetime import datetime
import os

from database import db, pegy_collection, init_db
from models import PEGYInput

app = FastAPI(title="PEGY + Multi-Valuation + Scoring Calculator")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    await init_db()

# ===================== SCORING ENGINE =====================
def calculate_score(r):
    score = 0
    
    # PEGY Score (0-30)
    pegy = r.get('pegy_ratio')
    if pegy is not None:
        if pegy < 0.5: score += 30
        elif pegy < 1: score += 25
        elif pegy < 1.5: score += 20
        elif pegy < 2: score += 15
        elif pegy < 3: score += 10
        else: score += 5
    
    # Growth Score (0-20)
    growth = r.get('eps_growth')
    if growth is not None:
        if growth > 20: score += 20
        elif growth > 15: score += 15
        elif growth > 10: score += 10
        elif growth > 5: score += 5
    
    # Payout Score (0-15)
    payout = r.get('payout_ratio')
    if payout is not None:
        if 30 <= payout <= 60: score += 15
        elif payout < 80: score += 10
        else: score += 5
    
    # Upside Score (0-20)
    upside = r.get('upside')
    if upside is not None:
        if upside > 50: score += 20
        elif upside > 20: score += 15
        elif upside > 0: score += 10
        elif upside > -10: score += 5
    
    # P/B Score (0-15)
    pb = r.get('pb_ratio')
    if pb is not None:
        if pb < 1: score += 15
        elif pb < 2: score += 10
        elif pb < 3: score += 5
    
    return score

def get_stars(score):
    if score >= 80: return "⭐⭐⭐⭐⭐", "#f59e0b"
    elif score >= 60: return "⭐⭐⭐⭐", "#27ae60"
    elif score >= 40: return "⭐⭐⭐", "#2ecc71"
    elif score >= 20: return "⭐⭐", "#f39c12"
    else: return "⭐", "#e74c3c"

def get_rating(score):
    if score >= 80: return "Strong BUY", "#f59e0b"
    elif score >= 60: return "BUY", "#27ae60"
    elif score >= 40: return "HOLD", "#2ecc71"
    elif score >= 20: return "Weak HOLD", "#f39c12"
    else: return "SELL", "#e74c3c"

# ===================== HOME PAGE =====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    records = await pegy_collection.find().sort("score", -1).to_list(100)
    for r in records:
        r["_id"] = str(r["_id"])
        if "score" not in r:
            r["score"] = calculate_score(r)
            r["stars"], r["stars_color"] = get_stars(r["score"])
            r["rating"], r["rating_color"] = get_rating(r["score"])
    
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
            pb_val = f"{r.get('pb_ratio', 0):.2f}" if r.get('pb_ratio') is not None else '-'
            fv_pe = f"{r.get('fv_pe', 0):.2f}" if r.get('fv_pe') is not None else '-'
            fv_pegy = f"{r.get('fv_pegy', 0):.2f}" if r.get('fv_pegy') is not None else '-'
            fv_graham = f"{r.get('fv_graham', 0):.2f}" if r.get('fv_graham') is not None else '-'
            fv_lynch = f"{r.get('fv_lynch', 0):.2f}" if r.get('fv_lynch') is not None else '-'
            fv_book = f"{r.get('fv_book', 0):.2f}" if r.get('fv_book') is not None else '-'
            fv_avg = f"{r.get('fv_average', 0):.2f}" if r.get('fv_average') is not None else '-'
            upside_val = f"{r.get('upside', 0):.2f}%" if r.get('upside') is not None else '-'
            score_val = r.get('score', 0)
            stars = r.get('stars', '⭐')
            stars_color = r.get('stars_color', '#f59e0b')
            rating = r.get('rating', '-')
            rating_color = r.get('rating_color', '#95a5a6')
            color = r.get('color', '#fff')
            rec = r.get('recommendation', '-')
            rec_color = "#27ae60" if rec == "BUY" else ("#e74c3c" if rec == "SELL" else "#f39c12")
            status = (r.get('status') or '-').split(' - ')[0]
            gc = "#27ae60" if (r.get('eps_growth') is not None and r.get('eps_growth', 0) >= 0) else "#e74c3c"
            
            po = r.get('payout_ratio')
            if po is not None:
                if 30 <= po <= 60: pc = "#27ae60"
                elif po < 80: pc = "#f39c12"
                else: pc = "#e74c3c"
            else: pc = "#94a3b8"
            
            table_rows += f"""<tr>
                <td><b style="color:#60a5fa;">{symbol}</b></td>
                <td style="color:{stars_color};font-size:10px;">{stars}</td>
                <td><b style="color:{rating_color};">{rating}</b></td>
                <td style="color:{gc};">{growth_val}</td>
                <td>{eps_val}</td>
                <td>{dps_val}</td>
                <td style="color:{pc};font-weight:bold;">{payout_val}</td>
                <td>{div_val}</td>
                <td>{pe_val}</td>
                <td>{peg_val}</td>
                <td><b style="color:{color};">{pegy_val}</b></td>
                <td><span style="background:{color};color:white;padding:3px 8px;border-radius:10px;font-size:9px;">{status}</span></td>
                <td>{pb_val}</td>
                <td>{fv_pe}</td>
                <td>{fv_pegy}</td>
                <td>{fv_graham}</td>
                <td>{fv_lynch}</td>
                <td>{fv_book}</td>
                <td><b style="color:#f59e0b;">{fv_avg}</b></td>
                <td style="color:{rec_color};font-weight:bold;">{upside_val}</td>
                <td><span style="background:{rec_color};color:white;padding:3px 8px;border-radius:10px;font-size:9px;">{rec}</span></td>
                <td>
                    <a href="/edit/{r['_id']}" style="color:#3b82f6;text-decoration:none;margin-right:3px;">✏️</a>
                    <a href="/delete/{r['_id']}" style="color:#e74c3c;text-decoration:none;" onclick="return confirm('Delete?')">🗑</a>
                </td>
            </tr>"""
    else:
        table_rows = '<tr><td colspan="22" style="text-align:center;color:#94a3b8;padding:30px;">No records yet</td></tr>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PEGY + Multi-Valuation + Scoring</title>
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
        table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:7px; }}
        th {{ background:#334155; padding:4px 1px; text-align:left; font-size:7px; color:#e2e8f0; }}
        td {{ padding:4px 1px; border-bottom:1px solid #334155; font-size:7px; }}
        h1 {{ text-align:center; margin-bottom:15px; font-size:22px; }}
        h4 {{ margin-bottom:10px; font-size:15px; }}
        .install-btn {{ background:#10b981; color:white; padding:14px; border-radius:30px; border:none; cursor:pointer; display:none; margin-bottom:10px; font-size:16px; font-weight:bold; width:100%; }}
        .info-text {{ color:#94a3b8; font-size:11px; margin-top:2px; display:block; }}
        hr {{ border-color:#334155; margin:15px 0; }}
    </style>
</head>
<body>
    <div style="max-width:850px;margin:0 auto;">
        <h1>📊 PEGY + Scoring</h1>
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
                <input type="number" step="0.01" name="current_price" id="currentPrice" placeholder="25.00" required oninput="calcAll()">
                
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
                <input type="number" step="0.01" name="dividend_yield" id="dividendYield" placeholder="5.60" required oninput="calcAll()">
                
                <hr>
                <h4>📊 Valuation Inputs</h4>
                
                <label>📖 NAV Per Share (টাকা)</label>
                <input type="number" step="0.01" name="nav_ps" id="navPs" placeholder="41.67" oninput="calcAll()">
                
                <label>📊 Total Shares (কোটি)</label>
                <input type="number" step="0.01" name="total_shares" id="totalShares" placeholder="1200" oninput="calcAll()">
                
                <label>📈 Industry P/E</label>
                <input type="number" step="0.01" name="industry_pe" id="industryPE" placeholder="12" oninput="calcAll()">
                
                <label>🏦 Bond Yield (%)</label>
                <input type="number" step="0.01" name="bond_yield" id="bondYield" placeholder="12" value="12" oninput="calcAll()">
                
                <hr>
                <h4>📊 Fair Value Outputs</h4>
                
                <label>1️⃣ P/E Fair Value</label>
                <input type="text" id="fvPEDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="fv_pe" id="fvPEHidden">
                
                <label>2️⃣ PEGY Fair Value</label>
                <input type="text" id="fvPEGYDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="fv_pegy" id="fvPEGYHidden">
                
                <label>3️⃣ Graham Fair Value</label>
                <input type="text" id="fvGrahamDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="fv_graham" id="fvGrahamHidden">
                
                <label>4️⃣ Peter Lynch Fair Value</label>
                <input type="text" id="fvLynchDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="fv_lynch" id="fvLynchHidden">
                
                <label>5️⃣ Book Value (NAV)</label>
                <input type="text" id="fvBookDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="fv_book" id="fvBookHidden">
                
                <label>⭐ Average Fair Value</label>
                <input type="text" id="fvAvgDisplay" placeholder="Auto" readonly style="background:#1a2744;font-weight:bold;font-size:18px;color:#f59e0b;">
                <input type="hidden" name="fv_average" id="fvAvgHidden">
                
                <label>📊 P/B Ratio</label>
                <input type="text" id="pbRatioDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="pb_ratio" id="pbRatioHidden">
                
                <label>📈 Upside/Downside (%)</label>
                <input type="text" id="upsideDisplay" placeholder="Auto" readonly>
                <input type="hidden" name="upside" id="upsideHidden">
                
                <label>🎯 Recommendation</label>
                <input type="text" id="recommendationDisplay" placeholder="Auto" readonly style="font-size:20px;font-weight:bold;">
                <input type="hidden" name="recommendation" id="recommendationHidden">
                
                <button type="submit" class="btn">📊 Calculate All</button>
            </form>
        </div>

        <div class="card">
            <h4>📊 Rankings (Highest Score First)</h4>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr><th>Sym</th><th>⭐</th><th>Rating</th><th>Grw</th><th>EPS</th><th>DPS</th><th>Pay%</th><th>Div%</th><th>P/E</th><th>PEG</th><th>PEGY</th><th>St</th><th>P/B</th><th>FvPE</th><th>FvPGY</th><th>FvGr</th><th>FvLy</th><th>FvBk</th><th>⭐Avg</th><th>Up%</th><th>Rec</th><th>Act</th></tr>
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
            calcAll();
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
            
            var price = parseFloat(document.getElementById('currentPrice').value) || 0;
            var eps = parseFloat(document.getElementById('eps').value) || 0;
            var growth = parseFloat(document.getElementById('epsGrowthHidden').value) || 0;
            var divYield = parseFloat(document.getElementById('dividendYield').value) || 0;
            var navPs = parseFloat(document.getElementById('navPs').value) || 0;
            var industryPE = parseFloat(document.getElementById('industryPE').value) || 0;
            var bondYield = parseFloat(document.getElementById('bondYield').value) || 12;
            
            var fvPE = 0, fvPEGY = 0, fvGraham = 0, fvLynch = 0, fvBook = 0;
            var count = 0, total = 0;
            
            if (eps > 0 && industryPE > 0) {{
                fvPE = eps * industryPE;
                document.getElementById('fvPEDisplay').value = fvPE.toFixed(2);
                document.getElementById('fvPEHidden').value = fvPE.toFixed(2);
                count++; total += fvPE;
            }} else {{
                document.getElementById('fvPEDisplay').value = '';
                document.getElementById('fvPEHidden').value = '';
            }}
            
            if (eps > 0 && growth > 0 && divYield > 0) {{
                fvPEGY = eps * (growth + divYield);
                document.getElementById('fvPEGYDisplay').value = fvPEGY.toFixed(2);
                document.getElementById('fvPEGYHidden').value = fvPEGY.toFixed(2);
                count++; total += fvPEGY;
            }} else {{
                document.getElementById('fvPEGYDisplay').value = '';
                document.getElementById('fvPEGYHidden').value = '';
            }}
            
            if (eps > 0 && growth > 0 && bondYield > 0) {{
                fvGraham = eps * (8.5 + 2 * growth) * 4.4 / bondYield;
                document.getElementById('fvGrahamDisplay').value = fvGraham.toFixed(2);
                document.getElementById('fvGrahamHidden').value = fvGraham.toFixed(2);
                count++; total += fvGraham;
            }} else {{
                document.getElementById('fvGrahamDisplay').value = '';
                document.getElementById('fvGrahamHidden').value = '';
            }}
            
            if (eps > 0 && growth > 0) {{
                fvLynch = eps * growth;
                document.getElementById('fvLynchDisplay').value = fvLynch.toFixed(2);
                document.getElementById('fvLynchHidden').value = fvLynch.toFixed(2);
                count++; total += fvLynch;
            }} else {{
                document.getElementById('fvLynchDisplay').value = '';
                document.getElementById('fvLynchHidden').value = '';
            }}
            
            if (navPs > 0) {{
                fvBook = navPs;
                document.getElementById('fvBookDisplay').value = fvBook.toFixed(2);
                document.getElementById('fvBookHidden').value = fvBook.toFixed(2);
                count++; total += fvBook;
            }} else {{
                document.getElementById('fvBookDisplay').value = '';
                document.getElementById('fvBookHidden').value = '';
            }}
            
            var fvAvg = count > 0 ? total / count : 0;
            document.getElementById('fvAvgDisplay').value = fvAvg > 0 ? fvAvg.toFixed(2) : '';
            document.getElementById('fvAvgHidden').value = fvAvg > 0 ? fvAvg.toFixed(2) : '';
            
            if (price > 0 && navPs > 0) {{
                var pb = price / navPs;
                document.getElementById('pbRatioDisplay').value = pb.toFixed(2);
                document.getElementById('pbRatioHidden').value = pb.toFixed(2);
            }} else {{
                document.getElementById('pbRatioDisplay').value = '';
                document.getElementById('pbRatioHidden').value = '';
            }}
            
            if (price > 0 && fvAvg > 0) {{
                var upside = ((fvAvg - price) / price) * 100;
                document.getElementById('upsideDisplay').value = upside.toFixed(2) + '%';
                document.getElementById('upsideHidden').value = upside.toFixed(2);
                document.getElementById('upsideDisplay').style.color = upside > 0 ? '#27ae60' : '#e74c3c';
                
                var rec;
                if (upside > 20) rec = 'BUY';
                else if (upside > 0) rec = 'HOLD';
                else if (upside > -10) rec = 'HOLD';
                else rec = 'SELL';
                document.getElementById('recommendationDisplay').value = rec;
                document.getElementById('recommendationHidden').value = rec;
                var rc = rec == 'BUY' ? '#27ae60' : (rec == 'SELL' ? '#e74c3c' : '#f39c12');
                document.getElementById('recommendationDisplay').style.color = rc;
            }} else {{
                document.getElementById('upsideDisplay').value = '';
                document.getElementById('upsideHidden').value = '';
                document.getElementById('recommendationDisplay').value = '';
                document.getElementById('recommendationHidden').value = '';
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
    nav_ps: float = Form(None),
    total_shares: float = Form(None),
    industry_pe: float = Form(None),
    bond_yield: float = Form(None),
    fv_pe: float = Form(None),
    fv_pegy: float = Form(None),
    fv_graham: float = Form(None),
    fv_lynch: float = Form(None),
    fv_book: float = Form(None),
    fv_average: float = Form(None),
    pb_ratio: float = Form(None),
    upside: float = Form(None),
    recommendation: str = Form(None),
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
        
        if payout_ratio is None and dps > 0 and eps > 0:
            payout_ratio = round((dps / eps) * 100, 2)
        
        doc = {
            "symbol": symbol.upper(), "eps": annual_eps, "eps_old": eps_old,
            "eps_period": eps_period, "dps": dps, "dps_old": dps_old,
            "payout_ratio": payout_ratio, "payout_cagr": payout_cagr,
            "dividend_yield": dividend_yield, "eps_growth": eps_growth,
            "current_price": current_price, "pe_ratio": pe_ratio,
            "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "nav_ps": nav_ps, "total_shares": total_shares,
            "industry_pe": industry_pe, "bond_yield": bond_yield,
            "fv_pe": fv_pe, "fv_pegy": fv_pegy, "fv_graham": fv_graham,
            "fv_lynch": fv_lynch, "fv_book": fv_book, "fv_average": fv_average,
            "pb_ratio": pb_ratio, "upside": upside,
            "recommendation": recommendation,
            "status": status, "color": color, "created_at": datetime.utcnow(),
        }
        
        # Calculate Score
        doc["score"] = calculate_score(doc)
        doc["stars"], doc["stars_color"] = get_stars(doc["score"])
        doc["rating"], doc["rating_color"] = get_rating(doc["score"])
        
        await pegy_collection.insert_one(doc)
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
        hr {{ border-color:#334155; margin:15px 0; }}
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
            <label>Payout CAGR (%)</label>
            <input type="number" step="0.01" name="payout_cagr" value="{record.get('payout_cagr',0)}">
            <label>Dividend Yield (%)</label>
            <input type="number" step="0.01" name="dividend_yield" value="{record.get('dividend_yield',0)}">
            <label>Current Price</label>
            <input type="number" step="0.01" name="current_price" value="{record.get('current_price',0)}">
            <hr>
            <h4>Valuation</h4>
            <label>NAV Per Share</label>
            <input type="number" step="0.01" name="nav_ps" value="{record.get('nav_ps',0)}">
            <label>Total Shares (Crore)</label>
            <input type="number" step="0.01" name="total_shares" value="{record.get('total_shares',0)}">
            <label>Industry P/E</label>
            <input type="number" step="0.01" name="industry_pe" value="{record.get('industry_pe',0)}">
            <label>Bond Yield (%)</label>
            <input type="number" step="0.01" name="bond_yield" value="{record.get('bond_yield',12)}">
            <label>FV P/E</label>
            <input type="number" step="0.01" name="fv_pe" value="{record.get('fv_pe',0)}">
            <label>FV PEGY</label>
            <input type="number" step="0.01" name="fv_pegy" value="{record.get('fv_pegy',0)}">
            <label>FV Graham</label>
            <input type="number" step="0.01" name="fv_graham" value="{record.get('fv_graham',0)}">
            <label>FV Lynch</label>
            <input type="number" step="0.01" name="fv_lynch" value="{record.get('fv_lynch',0)}">
            <label>FV Book</label>
            <input type="number" step="0.01" name="fv_book" value="{record.get('fv_book',0)}">
            <label>FV Average</label>
            <input type="number" step="0.01" name="fv_average" value="{record.get('fv_average',0)}">
            <label>P/B Ratio</label>
            <input type="number" step="0.01" name="pb_ratio" value="{record.get('pb_ratio',0)}">
            <label>Upside (%)</label>
            <input type="number" step="0.01" name="upside" value="{record.get('upside',0)}">
            <label>Recommendation</label>
            <input type="text" name="recommendation" value="{record.get('recommendation','')}">
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
    payout_cagr: float = Form(None),
    dividend_yield: float = Form(...),
    current_price: float = Form(...),
    nav_ps: float = Form(None),
    total_shares: float = Form(None),
    industry_pe: float = Form(None),
    bond_yield: float = Form(None),
    fv_pe: float = Form(None),
    fv_pegy: float = Form(None),
    fv_graham: float = Form(None),
    fv_lynch: float = Form(None),
    fv_book: float = Form(None),
    fv_average: float = Form(None),
    pb_ratio: float = Form(None),
    upside: float = Form(None),
    recommendation: str = Form(None),
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
        
        update_doc = {
            "symbol": symbol.upper(), "eps": eps, "eps_old": eps_old,
            "dps": dps, "dps_old": dps_old, "payout_ratio": payout_ratio,
            "payout_cagr": payout_cagr, "eps_growth": eps_growth,
            "dividend_yield": dividend_yield, "current_price": current_price,
            "pe_ratio": pe_ratio, "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "nav_ps": nav_ps, "total_shares": total_shares,
            "industry_pe": industry_pe, "bond_yield": bond_yield,
            "fv_pe": fv_pe, "fv_pegy": fv_pegy, "fv_graham": fv_graham,
            "fv_lynch": fv_lynch, "fv_book": fv_book, "fv_average": fv_average,
            "pb_ratio": pb_ratio, "upside": upside,
            "recommendation": recommendation,
            "status": status, "color": color,
        }
        
        # Recalculate Score
        update_doc["score"] = calculate_score(update_doc)
        update_doc["stars"], update_doc["stars_color"] = get_stars(update_doc["score"])
        update_doc["rating"], update_doc["rating_color"] = get_rating(update_doc["score"])
        
        await pegy_collection.update_one({"_id": obj_id}, {"$set": update_doc})
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
            "dps": data.dps, "dps_old": data.dps_old,
            "payout_ratio": data.payout_ratio, "payout_cagr": data.payout_cagr,
            "pe_ratio": pe_ratio, "peg_ratio": peg_ratio, "pegy_ratio": pegy_ratio,
            "status": status, "color": color, "created_at": datetime.utcnow(),
        })
        return {"id": str(result.inserted_id), "pegy_ratio": pegy_ratio, "status": status, "color": color}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/api/records")
async def get_records():
    records = await pegy_collection.find().sort("score", -1).to_list(100)
    for r in records: r["_id"] = str(r["_id"])
    return records

# ===================== MANIFEST & SW =====================
@app.get("/manifest.json")
async def manifest(): return FileResponse("static/manifest.json")

@app.get("/static/sw.js")
async def service_worker():
    return HTMLResponse(content="""const CACHE_NAME='pegy-v15';self.addEventListener('install',(e)=>{e.waitUntil(caches.open(CACHE_NAME).then((c)=>c.addAll(['/','/static/manifest.json'])));self.skipWaiting();});self.addEventListener('activate',(e)=>{e.waitUntil(clients.claim());});self.addEventListener('fetch',(e)=>{e.respondWith(caches.match(e.request).then((r)=>r||fetch(e.request)));});""", media_type="application/javascript")

# ===================== RUN =====================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)