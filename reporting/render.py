"""Render precomputed results as static files for GitHub Pages."""
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape
from common.config import ROOT, PAGES

def render(analysis: dict, sql_reports: list[dict], narrative: dict) -> None:
    PAGES.mkdir(exist_ok=True)
    assets=PAGES/'assets';assets.mkdir(exist_ok=True)
    env=Environment(loader=FileSystemLoader(ROOT/'reporting/templates'),autoescape=select_autoescape(['html']))
    page=env.get_template('index.html.j2').render(
        findings=analysis['findings'], reports=sql_reports, narrative=narrative,
        rates=analysis['rates'].reset_index().to_dict('records'),
        segments=analysis['segments'].to_dict('records'),
        monthly=[{'month':month,'raw':float(value),'corrected':float(analysis['corrected'][month])} for month,value in analysis['monthly'].items()],
        dropped=analysis['dropped'].order_id.tolist(),
        outliers=analysis['clean'].loc[analysis['clean'].is_outlier,['order_id','quantity']].to_dict('records'),
        checks=analysis['checks'],
    )
    (PAGES/'index.html').write_text(page)
    shutil.copyfile(ROOT/'reporting/static/styles.css',assets/'styles.css')
    for name in ('return_rate_by_payment.png','monthly_revenue_trend.png'):
        shutil.copyfile(ROOT/'visualizations'/name,assets/name)
