'use strict';
const $=id=>document.getElementById(id);
let token='', records=[], quality=null;
function node(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
function fail(e){$('error').textContent=e.message||String(e);}
async function request(path,options={}){
 const headers={...options.headers};if(token)headers.Authorization='Bearer '+token;
 let response;try{response=await fetch(path,{...options,headers,signal:AbortSignal.timeout(180000)});}catch{throw new Error('Serveur inaccessible ou délai dépassé. Gardez le terminal actif et vérifiez le réseau.');}
 let data;try{data=await response.json();}catch{throw new Error('Réponse serveur non JSON.');}
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Requête refusée ('+response.status+').');return data;
}
function tab(id){document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==id);document.querySelectorAll('[data-tab]').forEach(el=>el.classList.toggle('selected',el.dataset.tab===id));}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));
function metric(parent,value,label){const box=node('div',undefined,'metric');box.append(node('strong',String(value)),node('span',label));parent.append(box);}
async function refresh(){
 const [status,data,q,links]=await Promise.all([request('/api/status'),request('/api/records'),request('/api/quality'),request('/api/links')]);records=data;quality=q;
 $('connection').textContent='● Espace connecté · '+status.total+' notices · Réponses extractives sans LLM';
 $('demo-banner').textContent=status.demo ? 'DÉMONSTRATION · '+status.demo+' notice(s) fictive(s) sur '+status.total+'. Les molécules citées ne rendent pas ces essais réels. Filtrez et vérifiez les sources avant toute analyse.' : 'CORPUS COLLECTÉ · Les notices proviennent de sources publiques. Leur interprétation exige une validation scientifique.';
 $('metrics').replaceChildren();for(const [key,label] of [['trials','Essais'],['publications','Publications'],['links','Liens NCT explicites'],['approved','Notices revues']])metric($('metrics'),status[key],label);
 const phases={};for(const r of records.filter(r=>r.kind==='trial'))phases[r.phase||'Non renseignée']=(phases[r.phase||'Non renseignée']||0)+1;
 $('phases').replaceChildren();const total=Object.values(phases).reduce((a,b)=>a+b,0)||1;
 for(const [phase,count] of Object.entries(phases)){const row=node('div',phase+' · '+count,'bar-row');const meter=document.createElement('meter');meter.min=0;meter.max=total;meter.value=count;meter.setAttribute('aria-label',phase);row.append(document.createElement('br'),meter);$('phases').append(row);}
 $('links').replaceChildren();for(const l of links.slice(0,5))$('links').append(node('p',l.publication+' ↔ '+l.trial+' · '+l.evidence,'muted'));
 if(!links.length)$('links').append(node('p','Aucun lien explicite détecté.','muted'));
 $('quality-metrics').replaceChildren();metric($('quality-metrics'),q.warnings,'Alertes documentaires');metric($('quality-metrics'),q.pending,'Notices en attente');metric($('quality-metrics'),q.demo,'Notices fictives');metric($('quality-metrics'),q.records,'Notices contrôlées, rejets inclus');
 $('issues').replaceChildren();for(const issue of q.issues){const tr=node('tr');for(const value of [issue.record_id,issue.code,issue.severity,issue.message])tr.append(node('td',value));$('issues').append(tr);}
 renderCatalog();
}
function renderCatalog(){
 $('records').replaceChildren();const text=$('catalog-filter').value.toLowerCase();const kind=$('kind-filter').value;
 for(const r of records.filter(r=>(!kind||r.kind===kind)&&JSON.stringify(r).toLowerCase().includes(text))){
  const tr=node('tr'),title=node('td'),b=node('button',r.title);b.type='button';b.addEventListener('click',()=>showRecord(r.id));title.append(b,node('small',r.id+' · '+(r.demo?'FICTIF':r.source)));
  tr.append(title,node('td',r.drugs.join(', ')||'Non renseigné'),node('td',[r.phase,r.status].filter(Boolean).join(' · ')||'—'),node('td',r.review));$('records').append(tr);
 }
}
$('catalog-filter').addEventListener('input',renderCatalog);$('kind-filter').addEventListener('change',renderCatalog);
function sourceLink(url,text){const a=node('a',text,'source');try{const u=new URL(url);if(u.protocol==='https:'){a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';}}catch{}return a;}
async function showRecord(id){
 try{const r=await request('/api/records/'+encodeURIComponent(id));const el=$('detail');el.replaceChildren();el.hidden=false;
 el.append(node('h2',r.title),node('p',r.text,'quote'),sourceLink(r.url,'Ouvrir la notice source ↗'),node('p','Date source : '+(r.updated||'Absente')+' · Collecte : '+r.retrieved_at,'muted'),node('p','Empreinte SHA-256 : '+r.content_hash,'hash'),node('p',r.rights,'muted'));
 const form=node('form');form.append(node('h3','Revue scientifique humaine'));
 const decision=node('select');decision.setAttribute('aria-label','Décision');for(const [v,t] of [['approved','Approuver la notice'],['pending','Maintenir en attente'],['rejected','Rejeter la notice']]){const o=node('option',t);o.value=v;decision.append(o);}decision.value=r.review;
 const actor=node('input');actor.placeholder='Nom du relecteur (déclaratif)';actor.setAttribute('aria-label','Relecteur');actor.required=true;actor.minLength=2;actor.maxLength=100;
 const note=node('textarea');note.placeholder='Motif de la décision';note.setAttribute('aria-label','Motif');note.required=true;note.minLength=3;note.maxLength=1000;
 const save=node('button','Enregistrer la revue');form.append(decision,actor,note,save);form.addEventListener('submit',async e=>{e.preventDefault();save.disabled=true;try{await request('/api/review/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision:decision.value,actor:actor.value,note:note.value,expected_hash:r.content_hash})});await refresh();el.hidden=true;$('error').textContent='';}catch(err){fail(err);}finally{save.disabled=false;}});el.append(form);el.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){fail(e);}
}
$('search-form').addEventListener('submit',async e=>{
 e.preventDefault();$('search-button').disabled=true;$('error').textContent='';$('results').replaceChildren();$('search-state').textContent='Recherche dans les sources…';
 try{const result=await request('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('question').value.trim(),mode:$('mode').value})});$('search-state').textContent=result.results.length+' source(s) · '+result.latency_ms+' ms · '+(result.status==='abstained'?'Abstention : aucun élément retrouvé.':'Extraits cités, sans génération LLM.');
 for(const hit of result.results){const r=hit.record,card=node('article',undefined,'panel hit');card.append(node('span',r.demo?'FICTIF':r.source,'tag'),node('span',r.review,'tag'),node('h2',r.title),node('p',hit.citation.quote,'quote'),sourceLink(hit.citation.url,'Consulter la source ↗'),node('p','SHA-256 : '+hit.citation.hash,'hash'),node('p',hit.warning,'muted'));$('results').append(card);}
 }catch(e){$('search-state').textContent='Recherche interrompue.';fail(e);}finally{$('search-button').disabled=false;}
});
document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>{$('question').value=b.dataset.query;$('question').focus();}));
$('collect-form').addEventListener('submit',async e=>{
 e.preventDefault();if(!token){fail(new Error('Cliquez sur Accès administrateur et saisissez le jeton configuré sur le serveur.'));return;}
 $('collect-button').disabled=true;$('error').textContent='';$('collect-state').textContent='Collecte en cours…';
 try{const result=await request('/api/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:$('source').value,query:$('collect-query').value.trim(),limit:Number($('limit').value)})});$('collect-state').textContent=JSON.stringify(result,null,2);await refresh();}catch(e){$('collect-state').textContent='Échec de collecte. Aucun succès annoncé.';fail(e);}finally{$('collect-button').disabled=false;}
});
$('export').addEventListener('click',async()=>{try{const headers=token?{Authorization:'Bearer '+token}:{};const r=await fetch('/api/export?format=csv',{headers});if(!r.ok)throw new Error('Export refusé.');const url=URL.createObjectURL(await r.blob());const a=node('a');a.href=url;a.download='oncosignal.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){fail(e);}});
const dialog=node('dialog');const authForm=node('form');authForm.append(node('h2','Accès administrateur'),node('p','Jeton conservé en mémoire de cette page uniquement. Ne saisissez aucune clé OpenAI.','muted'));
const password=node('input');password.type='password';password.autocomplete='off';password.required=true;password.setAttribute('aria-label','Jeton administrateur');const login=node('button','Se connecter');const close=node('button','Annuler','subtle');close.type='button';close.addEventListener('click',()=>dialog.close());authForm.append(password,login,close);dialog.append(authForm);document.body.append(dialog);
$('connect').addEventListener('click',()=>{dialog.showModal();password.focus();});authForm.addEventListener('submit',async e=>{e.preventDefault();token=password.value;password.value='';dialog.close();try{await refresh();$('error').textContent='';}catch(err){token='';fail(err);}});
refresh().catch(fail);
