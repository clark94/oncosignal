"""Alignement conservateur : dictionnaire explicite et liens d'identifiants exacts."""
import re
import unicodedata

ALIASES = {
 'pembrolizumab': ['pembrolizumab', 'keytruda', 'mk-3475'],
 'nivolumab': ['nivolumab', 'opdivo', 'bms-936558'],
 'osimertinib': ['osimertinib', 'tagrisso', 'azd9291'],
 'trastuzumab deruxtecan': ['trastuzumab deruxtecan', 'ds-8201', 'enhertu'],
}
INDICATIONS = {
 'non-small cell lung cancer': ['non-small cell lung cancer', 'nsclc', 'cancer bronchique non a petites cellules'],
 'melanoma': ['melanoma', 'melanome'],
 'breast cancer': ['breast cancer', 'cancer du sein'],
}

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def entities(text, mapping):
    text = normalize(text)
    return sorted(k for k,values in mapping.items() if any(re.search(r'(?<!\w)'+re.escape(normalize(v))+r'(?!\w)',text) for v in values))

def align(record):
    text = '\n'.join([record.title,record.text,*record.drugs,*record.indications])
    original_drugs = record.drugs
    mapped = entities(text, ALIASES)
    preserved = [d for d in original_drugs if not entities(d, ALIASES)]
    return record.model_copy(update={
        'drugs': sorted(set(mapped+preserved)),
        'indications': sorted(set(record.indications+entities(text, INDICATIONS))),
        'nct_ids': sorted(set(record.nct_ids+re.findall(r'\bNCT\d{8}\b',text.upper()))),
    })

def links(records):
    result=[]
    trials={(n,r.demo):r for r in records if r.kind=='trial' for n in r.nct_ids}
    for r in records:
        if r.kind!='publication':continue
        for n in r.nct_ids:
            if (n,r.demo) in trials:
                result.append({'publication':r.id,'trial':trials[(n,r.demo)].id,'evidence':n,'method':'exact_nct','needs_review':True})
    return result
