"""OpenAI-compatible and keyless SCR narration from verified analysis findings.

The LLM path uses any OpenAI-compatible provider (OpenAI, DeepSeek, ...) selected
through environment variables and requests JSON-mode structured output that is
validated against the ScrNarrative schema. When no key is configured or the
provider is unavailable/inaccurate, a verified keyless offline narrative is used.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import ROOT, LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from common.schemas import Findings, ScrNarrative

SYSTEM_INSTRUCTION = (
    'You are a senior data analyst writing for Mamaearth regional operations and finance heads. '
    'Produce a Situation-Complication-Resolution narrative. Every number must come from the supplied '
    'findings and retain its exact value. Do not invent statistics. Explain the duplicate reconciliation '
    'and the outlier-corrected peak. '
    'Return ONLY a JSON object with exactly these string keys: "situation", "complication", "resolution". '
    'Do not include section labels inside the values and do not wrap the JSON in markdown. '
    'Example shape: {"situation": "...", "complication": "...", "resolution": "..."}'
)


def generate_scr_narrative(findings: dict) -> dict:
    """Generate the narrative via an OpenAI-compatible provider using JSON mode.

    Provider configuration is centralized in common.config (loaded from .env):
      LLM_PROVIDER  - label only, for attribution/logging (default: openai)
      LLM_API_KEY   - API key for the provider
      LLM_BASE_URL  - OpenAI-compatible endpoint (blank = OpenAI default)
      LLM_MODEL     - model name (default: gpt-4o-mini)
    """
    try:
        from openai import OpenAI

        if not LLM_API_KEY:
            raise ValueError('LLM_API_KEY is not set')

        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=30.0)
        # Factual reporting calls for stable output, not creative variation.
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_INSTRUCTION},
                {'role': 'user', 'content': 'Use these verified findings only:\n' + json.dumps(findings, indent=2)},
            ],
            response_format={'type': 'json_object'},
            temperature=0.0,
            max_tokens=2048,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError('Empty LLM response')
        narrative = ScrNarrative.model_validate_json(content).to_text()
        tokens = getattr(getattr(response, 'usage', None), 'total_tokens', None)
        return {'status': 'success', 'narrative': narrative, 'tokens': tokens, 'source': LLM_PROVIDER}
    except Exception as err:
        return {'status': 'error', 'narrative': None, 'message': str(err)}


def generate_scr_narrative_offline(findings: dict) -> dict:
    f=Findings.model_validate(findings)
    month=f.true_peak_month.month
    label={'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June'}[month[-2:]]
    text=(
        f"Situation\nThe cleaned order value is INR {f.cleaned_total_revenue_inr:,.2f} from the deduplicated orders. "
        f"Raw order value was INR {f.raw_total_revenue_inr:,.2f}.\n\n"
        f"Complication\nCOD has a {f.return_rate_by_payment['COD']:.1f}% return rate; "
        f"COD orders in Tier-{f.highest_risk_segment.city_tier} cities have a {f.highest_risk_segment.return_rate_pct:.1f}% rate. "
        f"Five duplicate records inflated the raw order value by INR {f.duplicate_reconciliation_delta_inr:,.2f}. "
        f"The apparent January peak of INR {f.outlier_inflated_month.apparent_revenue_inr:,.2f} falls to "
        f"INR {f.outlier_inflated_month.corrected_revenue_inr:,.2f} when two unusually large orders are excluded for trend analysis.\n\n"
        f"Resolution\nReview return causes in COD Tier-{f.highest_risk_segment.city_tier} orders and prevent duplicate submissions. "
        f"Use {label} at INR {f.true_peak_month.revenue_inr:,.2f} as the peak month for the comparison excluding bulk orders. "
        "Investigate causes before changing payment or fulfilment policies."
    )
    return {'status':'success','narrative':text,'tokens':0,'source':'offline'}

def check_numeric_accuracy(narrative: str, findings: dict) -> dict[str,bool]:
    f=Findings.model_validate(findings)
    normal=narrative.replace(',','').lower()
    checks={
        'cleaned revenue': f'{f.cleaned_total_revenue_inr:.2f}' in normal,
        'COD return rate': f"{f.return_rate_by_payment['COD']:.1f}" in normal,
        'highest risk rate': f'{f.highest_risk_segment.return_rate_pct:.1f}' in normal,
        'duplicate delta': f'{f.duplicate_reconciliation_delta_inr:.2f}' in normal,
        'March peak': 'march' in normal and f'{f.true_peak_month.revenue_inr:.2f}' in normal,
    }
    for name,ok in checks.items(): print(f'{name}: {"PASS" if ok else "FAIL"}')
    return checks

def run(*, offline: bool = False) -> dict:
    findings=json.loads((ROOT/'narrator/findings.json').read_text())
    Findings.model_validate(findings)
    use_llm = not offline and LLM_API_KEY
    result=generate_scr_narrative(findings) if use_llm else generate_scr_narrative_offline(findings)

    if result['status']!='success' or not all(check_numeric_accuracy(result['narrative'],findings)):
        print('LLM provider unavailable or inaccurate; using verified offline narrative.')
        result=generate_scr_narrative_offline(findings)
    if not all(check_numeric_accuracy(result['narrative'],findings)):
        raise ValueError('Narrative failed numerical checks')
    if result['source']!='offline':
        (ROOT/'narrator/sample_output.txt').write_text(result['narrative']+'\n')
    return result

if __name__=='__main__':
    print(run(offline='--offline' in sys.argv)['narrative'])
