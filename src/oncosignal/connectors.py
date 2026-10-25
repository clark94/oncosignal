"""Collecte bornée, endpoints fixes, instantanés bruts et pagination explicite."""
import os
import re
import time
from defusedxml import ElementTree as ET
import httpx
from .models import Record

CT_URL='https://clinicaltrials.gov/api/v2/studies'
NCBI='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

def ct_record(study):
    p=study.get('protocolSection',{})
    ident=p.get('identificationModule',{}); status=p.get('statusModule',{})
    design=p.get('designModule',{}); sponsor=p.get('sponsorCollaboratorsModule',{})
    inter=p.get('armsInterventionsModule',{}).get('interventions',[])
    nct=ident.get('nctId','')
    if not re.fullmatch(r'NCT\d{8}',nct):raise ValueError('Identifiant NCT absent/invalide')
    return Record(id='ct:'+nct,source='clinicaltrials',source_id=nct,kind='trial',
        title=ident.get('briefTitle',''),text=p.get('descriptionModule',{}).get('briefSummary',''),
        url='https://clinicaltrials.gov/study/'+nct,
        drugs=[i['name'] for i in inter if i.get('type') in ['DRUG','BIOLOGICAL'] and i.get('name')],
        indications=p.get('conditionsModule',{}).get('conditions',[]),
        phase=' / '.join(design.get('phases',[])),status=status.get('overallStatus',''),
        sponsor=sponsor.get('leadSponsor',{}).get('name',''),nct_ids=[nct],
        updated=status.get('lastUpdatePostDateStruct',{}).get('date',''),
        rights='Notice publique ClinicalTrials.gov ; vérifier conditions et mentions des contributeurs.')

def pubmed_records(xml):
    root=ET.fromstring(xml);records=[]
    if root.tag!='PubmedArticleSet' or root.find('.//ERROR') is not None:
        raise ValueError('Réponse XML PubMed inattendue ou en erreur.')
    for item in root.findall('.//PubmedArticle'):
        def txt(path):return ''.join(item.find(path).itertext()).strip() if item.find(path) is not None else ''
        pmid=txt('.//MedlineCitation/PMID')
        if not pmid.isdigit():continue
        title=txt('.//ArticleTitle')
        abstract='\n'.join(''.join(x.itertext()).strip() for x in item.findall('.//Abstract/AbstractText'))
        ncts=set(re.findall(r'\bNCT\d{8}\b',title+' '+abstract))
        # Identifiants NCT structurés explicitement déclarés.
        for bank in item.findall('.//DataBank'):
            if ''.join(bank.findtext('DataBankName','')).lower()=='clinicaltrials.gov':
                ncts.update(re.findall(r'\bNCT\d{8}\b',' '.join(x.text or '' for x in bank.findall('.//AccessionNumber'))))
        doi=next((x.text or '' for x in item.findall('.//ArticleId') if x.attrib.get('IdType')=='doi'),'')
        date=item.find('.//DateRevised')
        updated=''
        if date is not None:
            parts=[date.findtext(x,'') for x in ['Year','Month','Day']]
            if all(parts):updated='-'.join(parts)
        records.append(Record(id='pm:'+pmid,source='pubmed',source_id=pmid,kind='publication',title=title,text=abstract,
          url='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/',nct_ids=sorted(ncts),doi=doi,updated=updated,
          rights='Métadonnées PubMed ; les résumés peuvent être protégés par les droits des éditeurs.'))
    return records

class Collector:
    def __init__(self,store,client=None):
        self.store=store;self.client=client
        self.last=0.

    def _get(self,client,url,params):
        # Au plus 2 requêtes/seconde dans ce processus CLI/API.
        delay=.5-(time.monotonic()-self.last)
        if delay>0:time.sleep(delay)
        self.last=time.monotonic()
        for attempt in range(3):
            response=client.get(url,params=params)
            if response.status_code in [429,500,502,503,504] and attempt<2:
                time.sleep(1+attempt);continue
            response.raise_for_status()
            return response
        raise RuntimeError('Source indisponible')

    def collect(self,source,query,limit=20):
        if source not in ['clinicaltrials','pubmed']:raise ValueError('Source inconnue')
        if not query.strip() or len(query)>500:raise ValueError('Requête requise, 500 caractères maximum')
        if not 1<=limit<=100:raise ValueError('Limite de 1 à 100')
        owned=self.client is None
        client=self.client or httpx.Client(timeout=30,follow_redirects=False,headers={'User-Agent':'OncoSignal/0.1 research-prototype'})
        records=[];snapshots=[];errors=[];truncated=False
        try:
            if source=='clinicaltrials':
                token=None;seen_tokens=set();pages=0
                while len(records)<limit:
                    params={'query.term':query,'pageSize':min(50,limit-len(records)),'format':'json'}
                    if token:params['pageToken']=token
                    pages+=1
                    if pages>10:raise ValueError('Collecte interrompue après 10 pages ; affiner la requête.')
                    payload=self._get(client,CT_URL,params).json()
                    snapshots.append(self.store.snapshot(source,payload))
                    studies=payload.get('studies')
                    if not isinstance(studies,list):raise ValueError('Réponse ClinicalTrials invalide : studies absent.')
                    for item in studies:
                        try:records.append(ct_record(item))
                        except ValueError as exc:errors.append(str(exc))
                    token=payload.get('nextPageToken')
                    if token and token in seen_tokens:raise ValueError('Jeton de pagination répété par la source.')
                    if token:seen_tokens.add(token)
                    if not token or not studies:break
                truncated=bool(token)
            else:
                email=os.getenv('NCBI_EMAIL','').strip()
                if '@' not in email:raise ValueError('Définir NCBI_EMAIL avec une véritable adresse de contact.')
                common={'db':'pubmed','tool':'oncosignal','email':email}
                key=os.getenv('NCBI_API_KEY','')
                if key:common['api_key']=key
                payload=self._get(client,NCBI+'esearch.fcgi',{**common,'term':query,'retmax':limit,'retmode':'json','sort':'pub_date'}).json()
                snapshots.append(self.store.snapshot(source,payload))
                if 'esearchresult' not in payload or 'error' in payload:raise ValueError('Réponse NCBI invalide ou en erreur.')
                ids=payload.get('esearchresult',{}).get('idlist',[])
                truncated=int(payload.get('esearchresult',{}).get('count',0))>len(ids)
                if ids:
                    xml=self._get(client,NCBI+'efetch.fcgi',{**common,'id':','.join(ids),'retmode':'xml'}).text
                    snapshots.append(self.store.snapshot(source,{'xml':xml}))
                    records=pubmed_records(xml)
            return {'records':records[:limit],'snapshots':snapshots,'errors':errors,'truncated':truncated,
                    'note':'Échantillon borné à la limite demandée ; aucune exhaustivité garantie.'}
        finally:
            if owned:client.close()
