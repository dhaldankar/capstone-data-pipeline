import tempfile
import unittest
from pathlib import Path

from analysis.clean_and_eda import run_pipeline
from common.database import connection, reports, reset
from narrator.generate_narrative import check_numeric_accuracy, generate_scr_narrative_offline

class EndToEndChecks(unittest.TestCase):
    def test_raw_sql_and_independent_cleaning_reconcile(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.sqlite3'
            reset(path)
            sql=reports(path)
            analysis=run_pipeline()
            self.assertEqual(sql[0]['rows'][0]['total_revenue'],analysis['findings']['raw_total_revenue_inr'])
            self.assertEqual(
                round(sql[0]['rows'][0]['total_revenue']-analysis['findings']['duplicate_reconciliation_delta_inr'],2),
                analysis['findings']['cleaned_total_revenue_inr'],
            )
            self.assertEqual(len(reports(path)),len(sql))  # ALTER report is safe to rerun
            with connection(path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],180)

    def test_offline_narrative_tracks_changed_findings(self):
        f=run_pipeline()['findings']
        output=generate_scr_narrative_offline(f)['narrative']
        self.assertTrue(all(check_numeric_accuracy(output,f).values()))
        changed={**f,'cleaned_total_revenue_inr':12345.67}
        self.assertIn('12,345.67',generate_scr_narrative_offline(changed)['narrative'])

if __name__=='__main__': unittest.main()
