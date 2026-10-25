import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EMBED_MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

def text_of(r):return '\n'.join([r.title,r.text,*r.drugs,*r.indications])

class Search:
    def __init__(self,store):self.store=store;self.encoder=None

    def index_semantic(self,encoder=None):
        if encoder is None:
            from sentence_transformers import SentenceTransformer
            encoder=SentenceTransformer(EMBED_MODEL)
        records=self.store.records()
        if not records:return {'indexed':0,'model':EMBED_MODEL}
        vectors=encoder.encode([text_of(r) for r in records],normalize_embeddings=True)
        with self.store.connect() as db:
            for r,v in zip(records,vectors):
                db.execute('INSERT OR REPLACE INTO vectors VALUES(?,?,?,?)',(r.id,r.content_hash,EMBED_MODEL,json.dumps(np.asarray(v).tolist())))
        self.encoder=encoder
        return {'indexed':len(records),'model':EMBED_MODEL}

    def query(self,query,mode='lexical',limit=10,kind='',drug='',approved=False):
        if mode not in ['lexical','hybrid']:raise ValueError('Mode lexical ou hybrid requis')
        records=[r for r in self.store.records() if (not kind or r.kind==kind) and (not drug or drug in r.drugs) and (not approved or r.review=='approved')]
        if not records:return []
        vectorizer=TfidfVectorizer(strip_accents='unicode',ngram_range=(1,2),sublinear_tf=True)
        try:
            matrix=vectorizer.fit_transform([text_of(r) for r in records]);q=vectorizer.transform([query]);scores=cosine_similarity(q,matrix)[0]
        except ValueError:return []
        lexical=[i for i in np.argsort(-scores) if scores[i]>0]
        ranks={i:1/(60+rank) for rank,i in enumerate(lexical,1)}
        if mode=='hybrid':
            with self.store.connect() as db:
                rows={r['record_id']:r for r in db.execute('SELECT * FROM vectors WHERE model=?',(EMBED_MODEL,))}
            if any(r.id not in rows or rows[r.id]['content_hash']!=r.content_hash for r in records):
                raise ValueError('Index sémantique absent ou périmé. Exécutez index-semantic après chaque collecte/modification.')
            if self.encoder is None:
                from sentence_transformers import SentenceTransformer
                self.encoder=SentenceTransformer(EMBED_MODEL)
            qv=np.asarray(self.encoder.encode([query],normalize_embeddings=True))[0]
            matrix=np.asarray([json.loads(rows[r.id]['vector']) for r in records])
            semantic=cosine_similarity([qv],matrix)[0]
            for rank,i in enumerate([i for i in np.argsort(-semantic) if semantic[i]>=.35],1):ranks[i]=ranks.get(i,0)+1/(60+rank)
        ordered=sorted(ranks,key=lambda i:(-ranks[i],records[i].id))[:limit]
        result=[]
        for i in ordered:
            r=records[i];quote=(r.text or r.title)[:600]
            result.append({'record':r.model_dump(),'score':round(float(ranks[i]),6),'lexical_similarity':round(float(scores[i]),4),
              'citation':{'id':r.id,'url':r.url,'quote':quote,'hash':r.content_hash,'retrieved_at':r.retrieved_at},
              'warning':'Classement de recherche, pas probabilité ni niveau de preuve clinique.'})
        return result
