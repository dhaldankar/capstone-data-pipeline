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

class ScrNarrative(BaseModel):
    """Structured Situation-Complication-Resolution narrative returned by LLM providers."""
    situation: str
    complication: str
    resolution: str

    def to_text(self) -> str:
        return (
            f"Situation\n{self.situation.strip()}\n\n"
            f"Complication\n{self.complication.strip()}\n\n"
            f"Resolution\n{self.resolution.strip()}"
        )

class NarrativeResult(BaseModel):
    status: str
    narrative: str | None = None
    tokens: int | None = None
    message: str | None = None
    source: str | None = None
