from contextlib import asynccontextmanager
from pathlib import Path
import csv
import io
import json
import secrets
import threading
from typing import Literal
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from .config import Settings
from .pipeline import ResearchWorkspace
from .quality import report
from .alignment import links

STATIC=Path(__file__).parent/'static'

class Ask(BaseModel):
    question: str=Field(min_length=2,max_length=1000)
    mode: Literal['lexical','hybrid']='lexical'

class Collect(BaseModel):
    source: Literal['clinicaltrials','pubmed']
    query: str=Field(min_length=2,max_length=500)
    limit: int=Field(default=20,ge=1,le=100)

class Review(BaseModel):
    decision: Literal['approved','pending','rejected']
    actor: str=Field(min_length=2,max_length=100)
    note: str=Field(min_length=3,max_length=1000)
    expected_hash: str=Field(pattern='^[a-f0-9]{64}$')

def create_app(settings=None):
    cfg=settings or Settings.from_env();service=ResearchWorkspace(cfg)
    gate=threading.BoundedSemaphore(4)
    @asynccontextmanager
    async def lifespan(app):
        if not service.store.records(include_rejected=True):service.demo()
        yield
    app=FastAPI(title='OncoSignal — Scientific Intelligence',version='0.1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.service=service

    def authorized(request):
        header=request.headers.get('authorization','')
        return bool(cfg.admin_token) and secrets.compare_digest(header,'Bearer '+cfg.admin_token)

    def admin(request):
        if not authorized(request):raise HTTPException(401,'Jeton administrateur requis. Définir ONCO_ADMIN_TOKEN côté serveur.')

    @app.middleware('http')
    async def guard(request,call_next):
        path=request.url.path
        if cfg.private and (path.startswith('/api/') or path in ['/docs','/openapi.json']) and not authorized(request):
            return JSONResponse({'detail':'Espace privé : saisissez le jeton.'},status_code=401)
        if request.method=='POST':
            try:
                if int(request.headers.get('content-length','0'))>16384:return JSONResponse({'detail':'Requête trop volumineuse.'},status_code=413)
            except ValueError:return JSONResponse({'detail':'Longueur invalide.'},status_code=400)
            chunks=[];size=0
            async for chunk in request.stream():
                size+=len(chunk)
                if size>16384:return JSONResponse({'detail':'Requête trop volumineuse.'},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        response.headers['Cache-Control']='no-store' if path.startswith('/api/') else 'no-cache'
        return response

    def bounded(fn,*args,**kwargs):
        if not gate.acquire(blocking=False):raise HTTPException(429,'Serveur occupé. Réessayez.')
        try:return fn(*args,**kwargs)
        finally:gate.release()

    @app.get('/health')
    def health():return {'ok':True}

    @app.get('/')
    def home():return FileResponse(STATIC/'index.html')

    @app.get('/assets/{name}')
    def asset(name:str):
        if name not in ['app.js','style.css']:raise HTTPException(404)
        return FileResponse(STATIC/name)

    @app.get('/api/status')
    def status():return service.status()

    @app.get('/api/records')
    def records():return [{**r.model_dump(),'content_hash':r.content_hash} for r in service.store.records()]

    @app.get('/api/records/{record_id}')
    def record(record_id:str):
        r=service.store.get(record_id)
        if not r:raise HTTPException(404,'Fiche absente')
        return {**r.model_dump(),'content_hash':r.content_hash}

    @app.get('/api/search')
    def search(q:str=Query(default='',max_length=1000),mode:Literal['lexical','hybrid']='lexical',kind:str='',drug:str='',approved:bool=False):
        if not q.strip():return []
        try:return bounded(service.search.query,q,mode,10,kind,drug,approved)
        except (ValueError,ImportError) as exc:raise HTTPException(409,str(exc)) from exc

    @app.post('/api/ask')
    def ask(body:Ask):
        try:return bounded(service.evidence,body.question,body.mode)
        except (ValueError,ImportError) as exc:raise HTTPException(409,str(exc)) from exc

    @app.get('/api/quality')
    def quality():return report(service.store.records(include_rejected=True))

    @app.get('/api/links')
    def evidence_links():return links(service.store.records())

    @app.get('/api/audit')
    def audit(request:Request):admin(request);return service.store.audit()

    @app.post('/api/collect')
    async def collect(body:Collect,request:Request):
        admin(request)
        try:return await run_in_threadpool(bounded,service.collect,body.source,body.query,body.limit)
        except HTTPException:raise
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        except Exception as exc:
            # Ne pas exposer de chaîne d'URL contenant un secret NCBI dans la réponse.
            raise HTTPException(502,'Collecte indisponible. Vérifiez le réseau, la source et NCBI_EMAIL ; aucune collecte exhaustive garantie.') from exc

    @app.post('/api/review/{record_id}')
    def review(record_id:str,body:Review,request:Request):
        admin(request)
        try:return service.store.review(record_id,body.decision,body.actor,body.note,body.expected_hash).model_dump()
        except KeyError as exc:raise HTTPException(404,'Fiche absente') from exc
        except ValueError as exc:raise HTTPException(409,str(exc)) from exc

    @app.get('/api/export')
    def export(format:Literal['csv','json']='csv'):
        records=service.store.records()
        if format=='json':return Response(json.dumps([r.model_dump() for r in records],ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename=oncosignal.json'})
        buffer=io.StringIO();columns=['id','title','kind','drugs','indications','phase','status','sponsor','url','review','demo','content_hash']
        writer=csv.DictWriter(buffer,fieldnames=columns);writer.writeheader()
        for r in records:
            row={**r.model_dump(),'content_hash':r.content_hash}
            def safe(value):
                s=' | '.join(value) if isinstance(value,list) else str(value)
                return "'"+s if s.lstrip().startswith(('=','+','-','@')) else s
            writer.writerow({k:safe(row[k]) for k in columns})
        return Response('\ufeff'+buffer.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=oncosignal.csv'})
    return app
