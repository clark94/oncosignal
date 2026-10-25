from datetime import datetime, timezone

def issues(record):
    found=[]
    def add(code,severity,message):found.append({'record_id':record.id,'code':code,'severity':severity,'message':message})
    if record.demo:add('DEMO','info','Donnée entièrement fictive : ne pas utiliser pour une décision scientifique.')
    if not record.text.strip():add('MISSING_TEXT','warning','Texte scientifique absent.')
    if not record.drugs:add('UNMAPPED_DRUG','warning','Aucune intervention médicamenteuse reconnue ou renseignée.')
    if record.kind=='trial' and not record.phase:add('MISSING_PHASE','warning','Phase non renseignée ; ne pas la déduire.')
    if record.kind=='trial' and not record.sponsor:add('MISSING_SPONSOR','warning','Promoteur non renseigné.')
    if record.kind=='publication' and not record.nct_ids:add('NO_NCT','info','Aucun identifiant NCT explicite : aucun lien automatique à un essai.')
    if record.review!='approved':add('REVIEW_REQUIRED','info','Validation scientifique humaine en attente ou rejetée.')
    if record.updated:
        try:
            date=datetime.fromisoformat(record.updated[:10]).replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc)-date).days>365:add('STALE','warning','Date source supérieure à un an : vérifier son actualité.')
        except ValueError:add('INVALID_DATE','warning','Date source incomplète ou non ISO.')
    else:add('MISSING_DATE','warning','Date source manquante.')
    return found

def report(records):
    findings=[i for r in records for i in issues(r)]
    return {'records':len(records),'issues':findings,'warnings':sum(i['severity']=='warning' for i in findings),
            'pending':sum(r.review=='pending' for r in records),'demo':sum(r.demo for r in records),
            'coverage':{key:round(sum(bool(getattr(r,key)) for r in records)/len(records),3) if records else None for key in ['text','drugs','phase','sponsor','updated']},
            'note':'Couverture descriptive. Phase et promoteur ne sont pas applicables à toutes les publications.'}
