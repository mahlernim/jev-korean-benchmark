import argparse
from .prepare import prepare
from .runner import run
from .report import report


def main():
    parser=argparse.ArgumentParser(description="Staged Korean and medical evaluation of Jev")
    parser.add_argument("command",choices=["prepare","run","report","export","restore"])
    parser.add_argument("--experiment",default="pilot-v1")
    parser.add_argument("--stage",type=int,choices=range(5))
    parser.add_argument("--limit",type=int)
    parser.add_argument("--model",default="jev-latest")
    args=parser.parse_args()
    if not args.experiment or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.experiment):
        parser.error("Experiment must be a simple directory name")
    if args.limit is not None and args.limit<1: parser.error("Limit must be positive")
    if args.command=="prepare": prepare(args.experiment,args.model)
    elif args.command=="report": report(args.experiment,args.stage)
    elif args.command in ('export','restore'):
        from .publish import export,restore
        (export if args.command=='export' else restore)(args.experiment)
    else:
        for stage in ([args.stage] if args.stage is not None else range(5)):
            run(args.experiment,stage,args.limit)


if __name__=="__main__": main()
