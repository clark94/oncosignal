from pathlib import Path
import json
import time
from threading import Lock
from .alignment import align, links
from .connectors import Collector
from .models import Record, now
from .quality import report
from .search import Search
from .store import Store

class ResearchWorkspace:
    """Agents spécialisés déterministes ; orchestration bornée et observable, sans autonomie LLM."""
    def __init__(self,settings):
        self.settings=settings;self.store=Store(settings.workspace);self.search=Search(self.store);self.lock=Lock()

    def demo(self):
        path=Path(__file__).parent/'demo'/'records.json'
        with self.lock:
            return self.ingest([Record.model_validate(r) for r in json.loads(path.read_text(encoding='utf-8'))], 'demo')

    def ingest(self,records,source):
        started=time.perf_counter();trace=[];counts={'inserted':0,'updated':0,'unchanged':0}
        trace.append({'agent':'CollectionAgent','operation':'records_received','count':len(records)})
        for record in records:
            aligned=align(record);counts[self.store.upsert(aligned)]+=1
        trace.append({'agent':'AlignmentAgent','operation':'explicit_aliases_and_nct','count':len(records)})
        all_records=self.store.records();quality=report(all_records)
        trace.append({'agent':'QualityAgent','operation':'rules','warnings':quality['warnings']})
        trace.append({'agent':'EvidenceAgent','operation':'exact_nct_links','count':len(links(all_records))})
        outcome={'at':now(),'source':source,'counts':counts,'latency_ms':round((time.perf_counter()-started)*1000,2),'trace':trace}
        self.store.log('pipeline',outcome);return outcome

    def collect(self,source,query,limit):
        # Une collecte à la fois ; verrou partagé entre CLI et API dans ce processus.
        with self.lock:
            collected=Collector(self.store).collect(source,query,limit)
            result=self.ingest(collected.pop('records'),source)
            return {**result,**collected}

    def status(self):
        records=self.store.records()
        return {'total':len(records),'demo':sum(r.demo for r in records),'real':sum(not r.demo for r in records),
          'approved':sum(r.review=='approved' for r in records),'trials':sum(r.kind=='trial' for r in records),
          'publications':sum(r.kind=='publication' for r in records),'links':len(links(records)),
          'llm_enabled':False,'note':'Synthèse extractive ; aucune recommandation thérapeutique.'}

    def evidence(self,question,mode='lexical'):
        started=time.perf_counter();hits=self.search.query(question,mode,limit=5)
        return {'question':question,'status':'evidence_found' if hits else 'abstained','results':hits,
          'answer':'\n\n'.join(f"[{h['citation']['id']}] {h['citation']['quote']}" for h in hits) if hits else 'Aucun élément retrouvé dans ce corpus. Reformulez ou collectez des sources supplémentaires.',
          'latency_ms':round((time.perf_counter()-started)*1000,2),'generation':'extractive_no_llm',
          'limitations':'Les extraits ne constituent pas une synthèse clinique validée. Pas de comparaison d’efficacité entre essais.'}
