"""Development commands; stage implementations are in assignment files."""
import argparse
from common import database

def main() -> None:
    parser=argparse.ArgumentParser(prog='capstone')
    sub=parser.add_subparsers(dest='command',required=True)
    db=sub.add_parser('db');db.add_argument('action',choices=['init','seed','clear','drop','reset']);db.add_argument('--yes',action='store_true')
    for name in ('reports','analyze','charts','narrate','render','run-all'):
        command=sub.add_parser(name)
        if name in ('narrate','run-all'):
            mode=command.add_mutually_exclusive_group()
            mode.add_argument('--online',action='store_true')
            mode.add_argument('--offline',action='store_true')
        if name=='run-all': command.add_argument('--reset-db',action='store_true')
    args=parser.parse_args()
    if args.command=='db':
        if args.action in ('clear','drop','reset') and not args.yes:
            raise SystemExit('Pass --yes to confirm this database change')
        getattr(database,args.action)();return
    if args.command=='reports':
        for report in database.reports(): print(report['title'],report['rows'])
    elif args.command=='analyze':
        from analysis.clean_and_eda import main as analyze
        analyze()
    elif args.command=='charts':
        from analysis.visualize import generate_charts
        generate_charts()
    elif args.command=='narrate':
        from narrator.generate_narrative import run
        print(run(offline=not args.online)['narrative'])
    elif args.command=='render':
        from analysis.clean_and_eda import run_pipeline
        from narrator.generate_narrative import run
        from reporting.render import render
        render(run_pipeline(),database.reports(),run(offline=True))
    elif args.command=='run-all':
        from pipelines.run import run_all
        run_all(offline=not args.online,reset_database=args.reset_db)

if __name__=='__main__': main()
