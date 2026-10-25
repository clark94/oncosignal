from fastapi.testclient import TestClient
from oncosignal.api import create_app
from oncosignal.config import Settings

TOKEN='test-token-at-least-24-characters'

def test_pages_search_export_auth(tmp_path):
    app=create_app(Settings(tmp_path,TOKEN))
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        assert client.get('/assets/app.js').status_code==200
        assert client.get('/health').json()=={'ok':True}
        assert client.get('/api/status').json()['total']==10
        result=client.post('/api/ask',json={'question':'melanoma'}).json()
        assert result['status']=='evidence_found'
        assert client.post('/api/ask',json={'question':'x'*1001}).status_code==422
        assert client.get('/api/search',params={'q':'melanoma','mode':'hybrid'}).status_code==409
        assert client.post('/api/collect',json={'source':'clinicaltrials','query':'melanoma'}).status_code==401
        assert client.get('/api/audit').status_code==401
        headers={'Authorization':'Bearer '+TOKEN}
        assert client.get('/api/audit',headers=headers).status_code==200
        r=client.get('/api/records/demo:trial01').json()
        review={'decision':'approved','actor':'Clark','note':'Metadata checked','expected_hash':r['content_hash']}
        assert client.post('/api/review/demo:trial01',json=review,headers=headers).status_code==200
        assert client.get('/api/status').json()['approved']==1
        assert client.get('/api/export').status_code==200
        assert client.get('/api/export?format=json').json()[0]['demo'] is True

def test_private_mode(tmp_path):
    with TestClient(create_app(Settings(tmp_path,TOKEN,True))) as client:
        assert client.get('/').status_code==200
        assert client.get('/api/status').status_code==401
        assert client.get('/api/status',headers={'Authorization':'Bearer '+TOKEN}).status_code==200

def test_csv_formula_neutralization(tmp_path):
    app=create_app(Settings(tmp_path))
    with TestClient(app) as client:
        r=app.state.service.store.get('demo:trial01')
        app.state.service.store.upsert(r.model_copy(update={'title':'=HYPERLINK("bad")'}))
        assert "'=HYPERLINK" in client.get('/api/export').text

def test_actual_stream_size_limited(tmp_path):
    with TestClient(create_app(Settings(tmp_path))) as client:
        assert client.post('/api/ask',content=b'x'*17000,headers={'Content-Type':'application/json'}).status_code==413
