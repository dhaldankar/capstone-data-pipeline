"""Only coordinates the modules that own each assignment task."""
from analysis.clean_and_eda import main as analyze, run_pipeline
from analysis.visualize import generate_charts
from common.database import reports, reset
from narrator.generate_narrative import run as narrate
from reporting.render import render

def run_all(*, offline: bool = True, reset_database: bool = False) -> None:
    if reset_database:
        reset()
    sql_results = reports()
    analyze()
    analysis = run_pipeline()
    generate_charts(analysis)
    narrative = narrate(offline=offline)
    render(analysis, sql_results, narrative)
