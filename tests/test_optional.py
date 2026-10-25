import json
import numpy as np
import pytest
import httpx
from oncosignal.config import Settings
from oncosignal.pipeline import ResearchWorkspace
from oncosignal.synthesis import validate_draft,synthesize

class Encoder:
    def encode(self,texts,normalize_embeddings=True):
        return np.array([[1.,0.] if 'melanoma' in text.lower() else [0.,1.] for text in texts])

def test_persisted_vectors_and_stale_detection(tmp_path):
    service=ResearchWorkspace(Settings(tmp_path));service.demo()
    assert service.search.index_semantic(Encoder())['indexed']==10
    assert service.search.query('melanoma','hybrid')
    r=service.store.get('demo:trial01');service.store.upsert(r.model_copy(update={'text':r.text+' changed'}))
    with pytest.raises(ValueError,match='périmé'):service.search.query('melanoma','hybrid')

def test_citations_reject_fabricated_and_unknown_ids(tmp_path):
    service=ResearchWorkspace(Settings(tmp_path));service.demo();hits=service.search.query('melanoma')
    c=hits[0]['citation'];claim={'text':'Brouillon à relire','record_id':c['id'],'quote':c['quote'][:100]}
    assert validate_draft({'claims':[claim]},hits)['semantic_fidelity']=='not_measured'
    with pytest.raises(ValueError):validate_draft({'claims':[{**claim,'quote':'Citation inventée totalement absente du corpus.'}]},hits)
    with pytest.raises(ValueError):validate_draft({'claims':[{**claim,'record_id':'missing'}]},hits)

def test_llm_disabled_and_mocked_http(tmp_path,monkeypatch):
    s=ResearchWorkspace(Settings(tmp_path));s.demo();hits=s.search.query('melanoma');c=hits[0]['citation']
    monkeypatch.delenv('ONCO_ALLOW_EXTERNAL_LLM',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY','test-not-a-real-key');monkeypatch.setenv('ONCO_LLM_MODEL','fixture-model')
    with pytest.raises(ValueError,match='explicitement'):synthesize('melanoma',hits)
    monkeypatch.setenv('ONCO_ALLOW_EXTERNAL_LLM','1')
    def handler(req):
        body=json.loads(req.content);assert body['max_completion_tokens']==900
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'claims':[{'text':'Fictif à relire','record_id':c['id'],'quote':c['quote'][:100]}]})}}],'usage':{'prompt_tokens':100,'completion_tokens':30}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result=synthesize('melanoma',hits,client)
    assert result['usage']['completion_tokens']==30
    assert result['cost_usd'] is None
