import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis.clean_and_eda import ROOT, run_pipeline

def generate_charts(r=None):
    r = r or run_pipeline()
    output=ROOT/'visualizations'
    output.mkdir(exist_ok=True)
    with plt.rc_context({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False}):
        fig, ax=plt.subplots(figsize=(8,4.3),layout='constrained')
        rates=r['rates'].return_rate_pct
        bars=ax.bar(rates.index,rates.values,color=['#b94d38','#3c8275','#74a89a'],width=.55)
        ax.bar_label(bars,labels=[f'{x:.1f}%' for x in rates],padding=5)
        ax.set(ylim=(0,60),ylabel='Returned orders (%)',xlabel='Payment method',title=f'COD returns at {rates["COD"]:.1f}%')
        fig.savefig(output/'return_rate_by_payment.png',dpi=150);plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,4.3),layout='constrained')
        values=r['corrected']
        ax.plot(values.index,values.values,color='#256c59',marker='o',linewidth=2)
        peak=values.idxmax()
        ax.set(xlabel='Month',ylabel='Order value (INR)',title=f'Peak: {peak} — bulk orders excluded')
        ax.tick_params(axis='x',rotation=25)
        ax.grid(axis='y',alpha=.15)
        fig.savefig(output/'monthly_revenue_trend.png',dpi=150);plt.close(fig)

if __name__ == '__main__': generate_charts()
