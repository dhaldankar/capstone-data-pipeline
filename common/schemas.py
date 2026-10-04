"""Structure and runtime validation only; calculations live in assignment files."""
from pydantic import BaseModel, Field

class RiskSegment(BaseModel):
    payment_method: str
    city_tier: int
    return_rate_pct: float

class PeakMonth(BaseModel):
    month: str
    revenue_inr: float

class InflatedMonth(BaseModel):
    month: str
    apparent_revenue_inr: float
    corrected_revenue_inr: float

class Findings(BaseModel):
    cleaned_total_revenue_inr: float
    raw_total_revenue_inr: float
    duplicate_reconciliation_delta_inr: float
    return_rate_by_payment: dict[str, float]
    highest_risk_segment: RiskSegment
    true_peak_month: PeakMonth
    outlier_inflated_month: InflatedMonth

class NarrativeResult(BaseModel):
    status: str
    narrative: str | None = None
    tokens: int | None = None
    message: str | None = None
    source: str | None = None
