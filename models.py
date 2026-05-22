from pydantic import BaseModel, Field
from typing import Optional

class PEGYInput(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Ticker Symbol")
    eps: float = Field(..., gt=0, description="Current EPS (টাকায়)")
    eps_old: Optional[float] = Field(None, description="Old EPS 3 Years Ago (টাকায়)")
    eps_period: str = Field(..., description="annual or quarterly")
    dividend_yield: float = Field(..., ge=0, description="Dividend Yield (%)")
    eps_growth: Optional[float] = Field(None, description="EPS Growth Rate 3Yr (%)")
    current_price: float = Field(..., gt=0, description="Current Stock Price (টাকায়)")
    dps: Optional[float] = Field(None, description="Dividend Per Share (টাকায়)")
    dps_old: Optional[float] = Field(None, description="Old DPS 3 Years Ago (টাকায়)")
    payout_ratio: Optional[float] = Field(None, description="Payout Ratio (%)")
    payout_cagr: Optional[float] = Field(None, description="Payout CAGR 3Yr (%)")
    
    # ✅ নতুন: স্টক ডিভিডেন্ড ফিল্ড
    stock_dividend: Optional[float] = Field(None, description="Stock Dividend (%) - যেমন: 10 মানে 10% বোনাস শেয়ার")

    # Valuation Fields
    nav_ps: Optional[float] = Field(None, description="NAV Per Share (টাকায়)")
    total_shares: Optional[float] = Field(None, description="Total Shares (কোটি)")
    industry_pe: Optional[float] = Field(None, description="Industry P/E Ratio")
    bond_yield: Optional[float] = Field(None, description="Bond Yield (%)")