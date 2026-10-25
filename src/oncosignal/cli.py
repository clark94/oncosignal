import argparse
import json
import os
from .config import Settings
from .pipeline import ResearchWorkspace
from .quality import report

def main():
    p=argparse.ArgumentParser(prog='oncosignal');sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('serve');sub.add_parser('demo');sub.add_parser('quality');sub.add_parser('index-semantic');sub.add_parser('mcp')
    c=sub.add_parser('collect');c.add_argument('--source',choices=['clinicaltrials','pubmed'],required=True);c.add_argument('--query',required=True);c.add_argument('--limit',type=int,default=20)
    b=sub.add_parser('brief');b.add_argument('query');b.add_argument('--llm',action='store_true');
    s=sub.add_parser('search');s.add_argument('query');s.add_argument('--mode',choices=['lexical','hybrid'],default='lexical')
    args=p.parse_args()
    if args.command=='serve':
        import uvicorn
        uvicorn.run('oncosignal.api:create_app',factory=True,host=os.getenv('ONCO_HOST','127.0.0.1'),port=int(os.getenv('PORT',os.getenv('ONCO_PORT','8010'))));return
    if args.command=='mcp':
        from .mcp_server import main as serve_mcp
        serve_mcp();return
    service=ResearchWorkspace(Settings.from_env())
    try:
        if args.command=='demo':result=service.demo()
        elif args.command=='collect':result=service.collect(args.source,args.query,args.limit)
        elif args.command=='search':result=service.evidence(args.query,args.mode)
        elif args.command=='brief':
            result=service.evidence(args.query)
            if args.llm:
                from .synthesis import synthesize
                result['draft']=synthesize(args.query,result['results'])
        elif args.command=='quality':result=report(service.store.records(include_rejected=True))
        else:result=service.search.index_semantic()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as exc:
        # Éviter les URL httpx contenant api_key dans les messages de terminal.
        if isinstance(exc,(ValueError,ImportError)):p.exit(1,str(exc)+'\n')
        p.exit(1,'Échec : '+type(exc).__name__+'. Vérifiez la configuration et la disponibilité de la source.\n')

if __name__=='__main__':main()
