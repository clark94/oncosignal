"""Petit garde-fou synthétique reproductible ; ce n'est pas un benchmark métier."""
import json
import tempfile
from pathlib import Path
from time import perf_counter
from oncosignal.pipeline import ResearchWorkspace
from oncosignal.config import Settings

CASES=[('pembrolizumab',['demo:trial01','demo:pub01']),('osimertinib',['demo:trial02','demo:pub02']),('trastuzumab deruxtecan',['demo:trial03','demo:pub03']),('nivolumab',['demo:trial04','demo:pub04']),('Molecule-X',['demo:trial05','demo:pub05']),('zzzzzznotinthecorpus',[])]

def run():
    with tempfile.TemporaryDirectory() as tmp:
        s=ResearchWorkspace(Settings(Path(tmp)));s.demo();rows=[]
        for query,expected in CASES:
            t=perf_counter();hits=s.search.query(query,limit=2);ids=[h['record']['id'] for h in hits];latency=(perf_counter()-t)*1000
            precision=sum(i in expected for i in ids)/len(ids) if ids else None
            recall=sum(i in ids for i in expected)/len(expected) if expected else None
            rank=next((i+1 for i,v in enumerate(ids) if v in expected),None)
            rows.append({'query':query,'expected':expected,'retrieved':ids,'precision_at_2':precision,'recall_at_2':recall,'reciprocal_rank':1/rank if rank else (None if not expected else 0),'correct_abstention':not ids if not expected else None,'latency_ms':round(latency,3)})
        return {'scope':'6 questions synthétiques du corpus fictif ; aucune généralisation clinique','cases':rows,'semantic_model_tested':False,'llm_cost':None,'clinical_fidelity':None}

if __name__=='__main__':print(json.dumps(run(),indent=2,ensure_ascii=False))
