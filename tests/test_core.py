import json
from pathlib import Path
from oncosignal.config import Settings
from oncosignal.pipeline import ResearchWorkspace
from oncosignal.models import Record
from oncosignal.alignment import align,links
from oncosignal.quality import report
from oncosignal.connectors import ct_record,pubmed_records,Collector
import httpx
import pytest

@pytest.fixture
def service(tmp_path):
    result=ResearchWorkspace(Settings(tmp_path));result.demo();return result

def test_demo_is_fictional_and_idempotent(service):
    assert service.status()['total']==10
    assert service.status()['real']==0
    assert service.demo()['counts']=={'inserted':0,'updated':0,'unchanged':10}
    assert len(links(service.store.records()))==5

def test_alias_boundaries():
    r=Record(id='test',source='demo',source_id='test',title='Keytruda in melanoma',text='MK-3475',url='https://example.invalid',kind='publication',demo=True)
    assert align(r).drugs==['pembrolizumab']
    assert align(r.model_copy(update={'title':'notkeytruda','text':''})).drugs==[]

def test_search_and_abstention(service):
    result=service.evidence('osimertinib')
    assert result['status']=='evidence_found'
    assert all('osimertinib' in h['record']['title'].lower() for h in result['results'])
    assert service.evidence('zzzzzznotinthecorpus')['status']=='abstained'
    for h in result['results']:
        r=service.store.get(h['record']['id'])
        assert h['citation']['quote'] in (r.text or r.title)
        assert h['citation']['hash']==r.content_hash

def test_review_invalidated_on_scientific_update(service):
    r=service.store.get('demo:trial01')
    service.store.review(r.id,'approved','Reviewer','Checked metadata',r.content_hash)
    service.store.upsert(r)
    assert service.store.get(r.id).review=='approved'
    newer=r.model_copy(update={'phase':'PHASE1'})
    service.store.upsert(newer)
    assert service.store.get(r.id).review=='pending'
    with pytest.raises(ValueError):service.store.review(r.id,'approved','Reviewer','Stale version',r.content_hash)
    with service.store.connect() as db:assert db.execute('SELECT COUNT(*) FROM versions WHERE record_id=?',(r.id,)).fetchone()[0]==2

def test_rejected_excluded(service):
    r=service.store.get('demo:trial01');service.store.review(r.id,'rejected','Reviewer','Not relevant',r.content_hash)
    assert r.id not in [x.id for x in service.store.records()]
    assert len(service.store.records(include_rejected=True))==10

def test_quality(service):
    q=report(service.store.records())
    assert q['demo']==10 and q['warnings']>0
    assert any(i['code']=='MISSING_PHASE' for i in q['issues'])

def test_fixture_parsers():
    root=Path(__file__).parent/'fixtures'
    ct=ct_record(json.loads((root/'ctgov.json').read_text())['studies'][0])
    pm=pubmed_records((root/'pubmed.xml').read_text())[0]
    assert ct.source_id=='NCT99000001'
    assert ct.phase=='PHASE2'
    assert pm.nct_ids==['NCT99000001']
    assert align(ct).drugs==['pembrolizumab']
    assert links([ct,pm])[0]['method']=='exact_nct'

def test_collect_pagination_and_snapshots(service):
    fixture=json.loads((Path(__file__).parent/'fixtures/ctgov.json').read_text())
    calls=[]
    def handle(request):
        calls.append(request)
        payload=dict(fixture)
        if len(calls)==1:payload['nextPageToken']='page2'
        else:
            payload=json.loads(json.dumps(fixture));payload['studies'][0]['protocolSection']['identificationModule']['nctId']='NCT99000002'
        return httpx.Response(200,json=payload)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result=Collector(service.store,client).collect('clinicaltrials','melanoma',2)
    assert len(result['records'])==2
    assert len(result['snapshots'])==2
    assert calls[1].url.params['pageToken']=='page2'
    assert not result['truncated']

def test_hybrid_requires_real_index(service):
    with pytest.raises(ValueError,match='Index sémantique'):service.search.query('melanoma','hybrid')

def test_demo_never_links_to_real_notice(service):
    trial=service.store.get('demo:trial01')
    pub=service.store.get('demo:pub01').model_copy(update={'demo':False,'source':'pubmed'})
    assert links([trial,pub])==[]

def test_source_errors_not_silent(service,monkeypatch):
    with pytest.raises(ValueError):pubmed_records('<eFetchResult><ERROR>bad</ERROR></eFetchResult>')
    def handle(request):return httpx.Response(200,json={'unexpected':'error'})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError,match='studies absent'):Collector(service.store,client).collect('clinicaltrials','melanoma',2)
