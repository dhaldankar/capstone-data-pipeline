"""Shared calculations; no HTTP, model calls or file writes."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def run_pipeline():
    customers, products, raw = [pd.read_csv(ROOT / 'data' / f'{name}.csv') for name in ('customers', 'products', 'orders')]
    assert raw.shape == (180, 9)
    orders = raw.copy()
    raw_methods = orders.payment_method.unique().tolist()
    orders['payment_method'] = orders.payment_method.str.strip().str.upper()
    method_counts = orders.payment_method.value_counts().to_dict()
    duplicate_mask = orders.duplicated(subset=[c for c in orders if c != 'order_id'], keep='first')
    dropped = orders.loc[duplicate_mask].copy()
    clean = orders.loc[~duplicate_mask].copy()
    missing = clean[['discount_pct', 'rating']].isna().sum().to_dict()
    median = float(clean.rating.median())
    clean['discount_pct'] = clean.discount_pct.fillna(0)
    clean['rating'] = clean.rating.fillna(median)

    def enrich(frame):
        result = frame.merge(products, on='product_id', how='left', validate='many_to_one').merge(customers, on='customer_id', how='left', validate='many_to_one')
        assert len(result) == len(frame) and result[['price', 'city_tier']].notna().all().all()
        result['order_value'] = result.quantity * result.price * (1 - result.discount_pct.fillna(0) / 100)
        return result

    merged = enrich(clean)
    raw_revenue = round(float(enrich(raw).order_value.sum()), 2)
    delta = round(float(enrich(dropped).order_value.sum()), 2)
    total = round(float(merged.order_value.sum()), 2)
    q1, q3 = merged.quantity.quantile([.25, .75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    merged['is_outlier'] = ~merged.quantity.between(lower, upper)
    merged['month'] = pd.to_datetime(merged.order_date).dt.strftime('%Y-%m')
    rates = merged.groupby('payment_method').returned.agg(['count', 'mean'])
    rates['return_rate_pct'] = (rates['mean'] * 100).round(1)
    rates = rates.sort_values('return_rate_pct', ascending=False)
    segments = merged.groupby(['payment_method', 'city_tier']).returned.agg(['count', 'mean']).reset_index()
    segments['return_rate_pct'] = (segments['mean'] * 100).round(1)
    segments = segments.sort_values('return_rate_pct', ascending=False)
    highest = segments.iloc[0]
    monthly = merged.groupby('month').order_value.sum().round(2)
    corrected = merged.loc[~merged.is_outlier].groupby('month').order_value.sum().round(2)
    peak, inflated = corrected.idxmax(), monthly.idxmax()
    corr = merged[['rating', 'returned', 'discount_pct', 'quantity']].corr()
    pairs = []
    for i, left in enumerate(corr.columns):
        for right in corr.columns[i+1:]:
            value = float(corr.loc[left, right])
            band = next(label for threshold, label in [(0.2,'negligible'),(.4,'weak'),(.7,'moderate'),(1.01,'strong')] if abs(value) < threshold)
            pairs.append({'pair': f'{left} / {right}', 'correlation': round(value, 4), 'strength': band})
    findings = {
        'cleaned_total_revenue_inr': total,
        'raw_total_revenue_inr': raw_revenue,
        'duplicate_reconciliation_delta_inr': delta,
        'return_rate_by_payment': rates.return_rate_pct.to_dict(),
        'highest_risk_segment': {'payment_method': highest.payment_method, 'city_tier': int(highest.city_tier), 'return_rate_pct': float(highest.return_rate_pct)},
        'true_peak_month': {'month': peak, 'revenue_inr': float(corrected[peak])},
        'outlier_inflated_month': {'month': inflated, 'apparent_revenue_inr': float(monthly[inflated]), 'corrected_revenue_inr': float(corrected[inflated])},
    }
    checks = {
        'Source counts': (len(customers),len(products),len(raw)) == (45,16,180),
        'Duplicate IDs': dropped.order_id.tolist() == [f'O{i:04}' for i in range(176,181)],
        'Cleaned rows': len(merged) == 175,
        'Missing values resolved': not merged[['discount_pct','rating']].isna().any().any(),
        'Raw revenue': raw_revenue == 99860.20,
        'Cleaned revenue': total == 97358.30,
        'Independent reconciliation': delta == 2501.90 and round(raw_revenue-delta,2) == total,
        'Outlier IDs': merged.loc[merged.is_outlier,'order_id'].tolist() == ['O0011','O0098'],
        'Return rates': findings['return_rate_by_payment'] == {'CARD':14.7,'COD':44.4,'UPI':18.9},
        'Highest-risk segment': highest.payment_method == 'COD' and int(highest.city_tier) == 2 and highest.return_rate_pct == 54.5,
        'Corrected peak': peak == '2026-03' and float(corrected[peak]) == 20318.90,
    }
    if not all(checks.values()):
        raise ValueError('Validation failed: '+', '.join(k for k,v in checks.items() if not v))
    return dict(raw=raw, clean=merged, dropped=dropped, findings=findings, checks=checks, rates=rates, segments=segments, monthly=monthly, corrected=corrected, correlations=corr, pairs=pairs, raw_methods=raw_methods, method_counts=method_counts, missing=missing, median=median, iqr=dict(Q1=float(q1),Q3=float(q3),IQR=float(iqr),lower=float(lower),upper=float(upper)))

import json
import sys
from pathlib import Path

def main():
    r = run_pipeline()
    for key in ('raw_methods','method_counts','missing','median','iqr','rates','segments','correlations','pairs','monthly','corrected','checks'):
        print(f'\n{key}:\n{r[key]}')
    print('Raw shape:', r['raw'].shape, 'Cleaned original shape:', r['clean'][r['raw'].columns].shape)
    print('Dropped IDs:', r['dropped'].order_id.tolist())
    print('Remaining missing:', r['clean'][['discount_pct','rating']].isna().sum().to_dict())
    print('Outliers:', r['clean'].loc[r['clean'].is_outlier,['order_id','quantity','order_date']].to_string(index=False))
    f=r['findings']
    print(f"Raw revenue {f['raw_total_revenue_inr']:.2f} minus duplicate value {f['duplicate_reconciliation_delta_inr']:.2f} equals cleaned revenue {f['cleaned_total_revenue_inr']:.2f}. The independently valued five duplicates explain the full difference; discount/rating imputation does not change that total.")
    print('Hypothesis: COD has higher returns — Confirmed in this dataset. Highest risk:', f['highest_risk_segment'])
    print('Higher discounts reduce returns — Busted per the brief; correlation is negligible, not evidence of causation.')
    print('January’s apparent lead comes from two bulk orders; March is the genuine peak after excluding them.')
    (ROOT/'narrator/findings.json').write_text(json.dumps(f,indent=2)+'\n')

if __name__ == '__main__': main()
