// Dépendance de test seulement : jsdom@26.1.0 ; voir docs/VALIDATION.md.
const {JSDOM,VirtualConsole}=require('jsdom');
const {spawn}=require('node:child_process');
const net=require('node:net'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const sock=net.createServer();await new Promise(r=>sock.listen(0,'127.0.0.1',r));const port=sock.address().port;await new Promise(r=>sock.close(r));
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'onco-ui-'));
 const child=spawn(process.env.ONCO_TEST_PYTHON||'python',['-m','oncosignal','serve'],{env:{...process.env,ONCO_WORKSPACE:tmp,ONCO_HOST:'127.0.0.1',PORT:String(port)},stdio:['ignore','pipe','pipe']});
 let logs='';child.stderr.on('data',x=>logs+=x);child.stdout.on('data',x=>logs+=x);const base='http://127.0.0.1:'+port;let dom;
 async function until(check){for(let i=0;i<100;i++){if(await check())return;await delay(100);}throw Error('Timeout UI '+logs);}
 try{
  await until(async()=>{try{return(await fetch(base+'/health')).ok;}catch{return false;}});
  const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
  dom=await JSDOM.fromURL(base,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.fetch=(url,opts)=>fetch(new URL(url,base),opts);w.AbortSignal=AbortSignal;w.HTMLElement.prototype.scrollIntoView=function(){};}});
  const d=dom.window.document;await until(()=>d.getElementById('connection').textContent.includes('10 notices'));
  assert.equal(d.querySelectorAll('#records tr').length,10);
  d.querySelector('[data-tab="research"]').click();assert.equal(d.getElementById('research').hidden,false);
  d.getElementById('question').value='osimertinib';d.getElementById('search-form').dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true}));
  await until(()=>d.querySelectorAll('#results .hit').length>0);assert.match(d.getElementById('results').textContent,/osimertinib/);
  d.querySelector('[data-tab="catalog"]').click();d.getElementById('kind-filter').value='trial';d.getElementById('kind-filter').dispatchEvent(new dom.window.Event('change'));assert.equal(d.querySelectorAll('#records tr').length,5);
  d.querySelector('#records button').click();await until(()=>d.getElementById('detail').hidden===false);assert.match(d.getElementById('detail').textContent,/SHA-256/);
  assert.equal(errors.length,0,errors.join('\n'));console.log('PASS DOM : chargement, navigation, recherche citée, filtre et détail.');
 }finally{dom?.window.close();child.kill();if(child.exitCode===null)await new Promise(r=>child.once('exit',r));fs.rmSync(tmp,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
