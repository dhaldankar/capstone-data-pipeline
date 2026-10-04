"""Gemini and keyless SCR narration from verified analysis findings."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import ROOT
from common.schemas import Findings

def generate_scr_narrative(findings: dict) -> dict:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=30000))
        # Factual reporting calls for stable output, not creative variation.
        response = client.models.generate_content(
            model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            contents='Use these verified findings only:\n'+json.dumps(findings,indent=2),
            config=types.GenerateContentConfig(
                system_instruction=('You are a senior data analyst writing for Mamaearth regional operations and finance heads. '
                  'Write three labeled sections: Situation, Complication, Resolution. Every number must come from supplied findings '
                  'and retain its value. Do not invent statistics. Explain the duplicate reconciliation and outlier-corrected peak.'),
                temperature=0.0, max_output_tokens=2048),
        )
        if not response.text:
            raise ValueError('Empty Gemini response')
        tokens = getattr(getattr(response,'usage_metadata',None),'total_token_count',None)
        return {'status':'success','narrative':response.text,'tokens':tokens,'source':'gemini'}
    except Exception as err:
        return {'status':'error','narrative':None,'message':str(err)}

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
    result=generate_scr_narrative_offline(findings) if offline or not os.getenv('GEMINI_API_KEY') else generate_scr_narrative(findings)
    if result['status']!='success' or not all(check_numeric_accuracy(result['narrative'],findings)):
        print('Gemini unavailable or inaccurate; using verified offline narrative.')
        result=generate_scr_narrative_offline(findings)
    if not all(check_numeric_accuracy(result['narrative'],findings)):
        raise ValueError('Narrative failed numerical checks')
    if result['source']=='gemini':
        (ROOT/'narrator/sample_output.txt').write_text(result['narrative']+'\n')
    return result

if __name__=='__main__':
    print(run(offline='--offline' in sys.argv)['narrative'])
