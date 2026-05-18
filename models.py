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