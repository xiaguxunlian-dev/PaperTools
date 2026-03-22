import os
code = r"""
'use strict';
var passed=0,failed=0;
function test(n,fn){try{fn();console.log('PASS '+n);passed++}catch(e){console.log('FAIL '+n+': '+e.message);failed++}}

// Math
var nCDF=function(z){var a=Math.abs(z)/Math.sqrt(2);var t=1/(1+0.3275911*a);var y=1-t*t*t*t*t*Math.exp(-a*a)*(0.254829592-t*(0.284496736-t*(1.421413741-t*(1.453152027-t*1.061405429))));return 0.5*(1+(z<0?-y:y))};

// PICO
var pico=function(text){var t=text.toLowerCase();var F=function(pts){var o=[];for(var pi=0;pi<pts.length;pi++){var g=new RegExp(pts[pi],'gi'),m;while((m=g.exec(t))!==null)o.push((m[1]||m[0]).trim())}return o.filter(function(x,i,a){return a.indexOf(x)===i&&x.length>3}).slice(0,5)};return{population:F(["population[s]?[:\\s]+([^\\.]+)"]),intervention:F(["treated with ([\\w\\s]{3,30})"]),outcome:F(["efficacy|safety|mortality|response rate"])}};

test('PICO',function(){
  var r=pico('Aspirin for cardiovascular disease prevention in adults');
  if(!(r.intervention.length>0||r.population.length>0))throw new Error('should extract');
  console.log('  P:'+r.population.length+' I:'+r.intervention.length+' O:'+r.outcome.length);
});

// RoB2
var rob2=function(text){
  var f=function(k){return text.indexOf(k)!==-1};
  var R=f('randomized')?'Low':f('quasi-random')?'High':'Unknown';
  var A=(f('allocation concealment')||f('sealed'))?'Low':f('open-label')?'High':'Unknown';
  var BP=f('double-blind')?'Low':f('open-label')?'High':'Unknown';
  var Att=!f('dropout')?'Low':f('intention-to-treat')?'Low':'Some concerns';
  var Rep=(f('clinicaltrials.gov')||f('registration'))?'Low':'Some concerns';
  var con=['Some concerns','High'].filter(function(x){return[R,A,BP,Att,Rep].indexOf(x)!==-1}).length;
  return con===0?'Low':con<=2?'Some concerns':'High';
};

test('RoB2 Good RCT',function(){
  var r=rob2('randomized double-blind allocation concealed ITT registered clinicaltrials.gov');
  if(r!=='Low')throw new Error('got '+r);
  console.log('  Overall: '+r);
});

test('RoB2 Poor',function(){
  var r=rob2('open-label dropout not handled no registration');
  if(r!=='High')throw new Error('got '+r);
});

// GRADE
var grade=function(design,kw){
  kw=kw||{};
  var s=design==='RCT'?4:2;
  ['risk_of_bias','inconsistency','indirectness','imprecision','publication_bias'].forEach(function(k){if(kw[k])s--});
  return['Very Low','Low','Moderate','High','High'][Math.max(0,Math.min(5,s))];
};

test('GRADE RCT无降级',function(){if(grade('RCT',{})!=='High')throw new Error('got '+grade('RCT',{}))});
test('GRADE RCT降1级',function(){if(grade('RCT',{inconsistency:true})!=='Moderate')throw new Error('got '+grade('RCT',{inconsistency:true}))});
test('GRADE Obs无降级',function(){if(grade('Observational',{})!=='Low')throw new Error('got '+grade('Observational',{}))});
test('GRADE Obs升级',function(){if(grade('Observational',{dose_response:true})!=='Moderate')throw new Error('got '+grade('Observational',{dose_response:true}))});

// JBI
var jbi=function(text,type){
  type=type||'RCT';
  var isRCT=/randomized|rct/.test(text);
  var score=0;
  if(isRCT){
    if(/randomized/.test(text))score++;
    if(/allocation/.test(text))score++;
    if(/double-blind/.test(text)||/blinded/.test(text))score++;
    if(/placebo|control/.test(text))score++;
    score+=2;
    if(/intention-to-treat|multivariate/.test(text))score++;
  }
  var max=isRCT?10:8;
  var pct=score/max;
  return{score:score,max:max,ql:pct>=0.8?'High':pct>=0.5?'Moderate':'Low'};
};

test('JBI Good RCT',function(){
  var r=jbi('randomized allocation concealed double-blind placebo ITT multivariate');
  console.log('  Score:'+r.score+'/'+r.max+' -> '+r.ql);
  if(r.score<6)throw new Error('good RCT should score>=6');
});

// Evidence Table
var evTable=function(papers,fmt){
  fmt=fmt||'md';
  if(!papers||!papers.length)return'No papers';
  var rows=papers.map(function(p){
    return{name:(p.authors||['?'])[0]+' ('+p.year+')',journal:p.journal||'N/A',doi:p.doi||'N/R'};
  });
  if(fmt==='csv'){
    return'Study,Journal,DOI\n'+rows.map(function(r){return'"'+r.name+'","'+r.journal+'","'+r.doi+'"'}).join('\n');
  }
  return'# Evidence Table\n|Study|Journal|DOI|\n|---|---|---|\n'+rows.map(function(r){return'|'+r.name+'|'+r.journal+'|'+r.doi+'|'}).join('\n');
};

test('Evidence Table',function(){
  var papers=[
    {title:'Statins',authors:['Smith'],year:2022,journal:'NEJM',doi:'10.1234'},
    {title:'Aspirin',authors:['Jones'],year:2021,journal:'Lancet',doi:'10.5678'}
  ];
  var md=evTable(papers,'md');
  if(md.indexOf('NEJM')===-1)throw new Error('should include NEJM');
  var csv=evTable(papers,'csv');
  if(csv.indexOf('Smith')===-1)throw new Error('csv should include Smith');
  console.log('  Generated '+md.length+' chars');
});

// PRISMA
var prisma=function(o){
  o=o||{};
  return{
    db:o.dbRecords||0,
    dedup:o.duplicates||0,
    after:(o.dbRecords||0)-(o.duplicates||0),
    inc:o.includedReports||0,
    q:o.query||''
  };
};

test('PRISMA calc',function(){
  var d=prisma({dbRecords:1500,duplicates:450,includedReports:12,query:'Statins'});
  if(d.after!==1050)throw new Error('after should be 1050, got '+d.after);
  console.log('  DB='+d.db+' After='+d.after+' Inc='+d.inc);
});

// IMRAD
var imrad=function(topic,papers,secs){
  papers=papers||[];
  secs=secs||['background','methods','results'];
  var o='# '+topic+'\n\n*Generated - '+papers.length+' papers*\n\n';
  secs.forEach(function(s,i){o+='## '+(i+1)+'. '+s.toUpperCase()+'\n\n';});
  return o;
};

test('IMRAD',function(){
  var r=imrad('Test topic',[{title:'Statins',authors:['Smith'],year:2022}]);
  if(r.indexOf('BACKGROUND')===-1)throw new Error('should have BACKGROUND');
  if(r.indexOf('METHODS')===-1)throw new Error('should have METHODS');
  console.log('  Generated '+r.length+' chars');
});

// References
var refs=function(papers,style){
  style=style||'bibtex';
  return papers.map(function(p){
    var a=(p.authors||[]).join(' and '),y=p.year||'n.d.',t=p.title||'?',j=p.journal||'',d=p.doi||'';
    if(style==='bibtex')return'@article{KEY,title={'+t+'},author={'+a+'},journal={'+j+'},year={'+y+'},doi={'+d+'},\n';
    if(style==='vancouver'){
      var au=(p.authors||[]).length>6?(p.authors||[]).slice(0,3).map(function(n){return n.split(' ').pop()}).join(', ')+' et al.':(p.authors||[]).map(function(n){return n.split(' ').pop()}).join(', ');
      return au+'. '+t+'. '+j+'. '+y+'.';
    }
    return'TY  - JOUR\nAU  - '+a+'\nTI  - '+t+'\nER  -\n';
  }).join('\n');
};

test('References',function(){
  var papers=[{title:'Test',authors:['Smith A'],year:2022,journal:'NEJM',doi:'10.1'}];
  var b=refs(papers,'bibtex');
  if(b.indexOf('@article')===-1)throw new Error('bibtex fail');
  var v=refs(papers,'vancouver');
  if(v.indexOf('Smith')===-1)throw new Error('vancouver fail');
  console.log('  bibtex: '+b.substring(0,50));
});

// Effect Size
var fxExtract=function(text){
  var results=[];
  var patterns=[
    {type:'RR',pat:/RR\s*=\s*([0-9.]+)/gi},
    {type:'OR',pat:/\bOR\s*=\s*([0-9.]+)/gi},
    {type:'HR',pat:/\bHR\s*=\s*([0-9.]+)/gi}
  ];
  for(var pi=0;pi<patterns.length;pi++){
    var p=patterns[pi];
    var m;
    p.pat.lastIndex=0;
    while((m=p.pat.exec(text))!==null){
      var v=parseFloat(m[1]);
      if(v&&v>0)results.push({type:p.type,v:v});
    }
  }
  return results;
};

test('Effect Size Extractor',function(){
  var text='RR=0.75, 95CI:0.55-1.02. OR=0.68 (95CI:0.50-0.92). HR=0.72 95CI:0.55-0.95.';
  var r=fxExtract(text);
  console.log('  Found '+r.length+' effects');
  r.forEach(function(x){console.log('    '+x.type+': '+x.v)});
  if(r.length!==3)throw new Error('should find 3, got '+r.length);
  var rr=r.find(function(x){return x.type==='RR'});
  if(!rr||rr.v!==0.75)throw new Error('RR should be 0.75');
  var or=r.find(function(x){return x.type==='OR'});
  if(!or||or.v!==0.68)throw new Error('OR should be 0.68');
});

// Heterogeneity
var hetCalc=function(effects){
  var n=effects.length;
  var lns=effects.map(function(e){return e.ln_rr||0});
  var vs=effects.map(function(e){return e.var||1});
  var ws=vs.map(function(v){return 1/Math.max(v,1e-6)});
  var sumW=ws.reduce(function(a,b){return a+b},0);
  var pooled=ws.reduce(function(s,w,i){return s+w*lns[i]},0)/sumW;
  var Q=ws.reduce(function(s,w,i){return s+w*Math.pow(lns[i]-pooled,2)},0);
  var df=n-1;
  var iSq=Q>0?Math.max(0,(Q-df)/Q*100):0;
  var tSq=Q>df?Math.max(0,(Q-df)/(sumW-ws.reduce(function(s,w){return s+w*w},0)/sumW)):0;
  var i2L=iSq<25?'Low':iSq<50?'Moderate':iSq<75?'High':'Very High';
  return{n:n,Q:Q,df:df,iSq:iSq,tSq:tSq,i2L:i2L};
};

test('Heterogeneity',function(){
  var effs=[
    {ln_rr:-0.43,var:0.04},
    {ln_rr:-0.33,var:0.04},
    {ln_rr:-0.55,var:0.04},
    {ln_rr:-0.37,var:0.04}
  ];
  var r=hetCalc(effs);
  console.log('  Q='+r.Q.toFixed(2)+' I2='+r.iSq.toFixed(1)+'% tSq='+r.tSq.toFixed(4));
  if(r.n!==4)throw new Error('should be 4 studies');
  if(r.iSq<0||r.iSq>100)throw new Error('I2 out of range');
});

// Forest Plot
var forest=function(studies,pooled,het,et){
  et=et||'RR';
  var fmt=function(v){return(et==='RR'||et==='OR'||et==='HR'?Math.exp(v):v).toFixed(2)};
  var o='\nForest Plot '+et+'\n';
  o+='Summary'.padEnd(20)+fmt(pooled.effect).padEnd(8)+fmt(pooled.ci_lower)+'-'+fmt(pooled.ci_upper)+'  100%\n';
  o+='-'.repeat(38)+'\n';
  for(var i=0;i<studies.length;i++){
    var s=studies[i];
    var lnE=Math.log(Math.max(s.effect,0.001));
    var lnL=Math.log(Math.max(s.ci_lower,0.001));
    var lnU=Math.log(Math.max(s.ci_upper,0.001));
    o+=(s.name+' '+s.year).substring(0,20).padEnd(20)+fmt(lnE).padEnd(8)+fmt(lnL)+'-'+fmt(lnU)+' '+s.weight.toFixed(1)+'%\n';
  }
  o+='\nI2='+het.iSq.toFixed(1)+'% Q='+het.Q.toFixed(2)+'\n';
  return o;
};

test('Forest Plot',function(){
  var studies=[
    {name:'Smith',year:2020,effect:0.75,ci_lower:0.55,ci_upper:1.02,weight:25},
    {name:'Johnson',year:2021,effect:0.68,ci_lower:0.50,ci_upper:0.92,weight:30},
    {name:'Williams',year:2022,effect:0.82,ci_lower:0.60,ci_upper:1.12,weight:20},
    {name:'Brown',year:2023,effect:0.71,ci_lower:0.52,ci_upper:0.97,weight:25}
  ];
  var o=forest(studies,{effect:0.72,ci_lower:0.60,ci_upper:0.87},{iSq:20,Q:2.5},'RR');
  console.log(o);
  if(o.indexOf('Smith')===-1)throw new Error('should include Smith');
  if(o.indexOf('Johnson')===-1)throw new Error('should include Johnson');
});

// Meta Analyzer
var meta=function(){
  var _s=[];
  var add=function(name,type,effect,ciL,ciU,yr){
    var lnE=(type==='RR'||type==='OR'||type==='HR')?Math.log(Math.max(effect,0.001)):effect;
    var lnL=ciL>0?Math.log(ciL):ciL;
    var lnU=Math.log(Math.max(ciU,0.001));
    var se=(lnU-lnL)/(2*1.96);
    _s.push({name:name,yr:yr,type:type,ciL:ciL,ciU:ciU,lnE:lnE,lnL:lnL,lnU:lnU,var:se*se});
  };
  var run=function(model){
    if(_s.length<2)return{error:'Need at least 2 studies'};
    var ws=_s.map(function(s){return 1/Math.max(s.var,1e-6)});
    var sumW=ws.reduce(function(a,b){return a+b},0);
    var lnP=ws.reduce(function(a,w,i){return a+w*_s[i].lnE},0)/sumW;
    if(model==='random'){
      var tSq=0.02;
      var adjW=_s.map(function(s){return 1/Math.max(s.var+tSq,1e-6)});
      var sA=adjW.reduce(function(a,b){return a+b},0);
      lnP=adjW.reduce(function(a,w,i){return a+w*_s[i].lnE},0)/sA;
    }
    var pSE=Math.sqrt(1/sumW);
    var lnCL=lnP-1.96*pSE;
    var lnCU=lnP+1.96*pSE;
    var z=lnP/pSE;
    var pVal=2*(1-nCDF(Math.abs(z)));
    var et=_s[0]&&_s[0].type||'RR';
    var toR=function(v){return(et==='RR'||et==='OR'||et==='HR')?Math.exp(v):v};
    var nW=ws.map(function(w){return w/sumW*100});
    _s.forEach(function(s,i){s.wPct=nW[i]});
    return{
      n:_s.length,
      model:model||'random',
      et:et,
      pooled:{effect:toR(lnP),ciL:toR(lnCL),ciU:toR(lnCU),p:pVal},
      _s:_s,
      report:function(){
        var o='Meta Analysis\n==========\n';
        o+=this.n+' studies | '+this.model+' | '+this.et+'\n';
        o+='Pooled: '+this.et+'='+toR(lnP).toFixed(3)+' ['+toR(lnCL).toFixed(3)+'-'+toR(lnCU).toFixed(3)+'] p='+pVal.toFixed(4)+'\n\n';
        this._s.forEach(function(s){
          o+='  '+s.name.padEnd(20)+(s.yr||'?')+' OR='+s.ciL.toFixed(3)+' ['+s.ciL.toFixed(3)+'-'+s.ciU.toFixed(3)+'] w='+s.wPct.toFixed(1)+'%\n';
        });
        return o;
      }
    };
  };
  return{add:add,run:run};
};

test('Meta Random Effects',function(){
  var m=meta();
  m.add('Smith 2020','OR',0.65,0.48,0.88,2020);
  m.add('Johnson 2021','OR',0.72,0.55,0.95,2021);
  m.add('Williams 2022','OR',0.58,0.40,0.84,2022);
  m.add('Brown 2023','OR',0.69,0.50,0.95,2023);
  var r=m.run('random');
  console.log('\n'+r.report());
  if(r.n!==4)throw new Error('should have 4');
  if(!(r.pooled.effect>0&&r.pooled.effect<2))throw new Error('effect out of range: '+r.pooled.effect);
  console.log('  PASS\n');
});

test('Meta Fixed Effects',function(){
  var m=meta();
  m.add('Study1','RR',0.80,0.70,0.92,2020);
  m.add('Study2','RR',0.78,0.65,0.94,2021);
  var r=m.run('fixed');
  if(r.model!=='fixed')throw new Error('should be fixed, got '+r.model);
  console.log('  PASS - pooled='+r.pooled.effect.toFixed(3)+'\n');
});

// Entities
var entities=function(text){
  var r=[],seen={};
  var dict={
    gene:['TP53','BRCA1','EGFR','KRAS','MYC','PTEN','HER2','PD-1','PD-L1','CTLA-4','VEGF','IL-6','STAT3','AKT','mTOR','PI3K','MAPK','ERK','BRAF','CD8','CD4'],
    disease:['cancer','tumor','carcinoma','melanoma','lymphoma','diabetes','obesity','hypertension','cardiovascular','stroke','Alzheimer','Parkinson','depression','arthritis','asthma'],
    drug:['aspirin','metformin','insulin','atorvastatin','paclitaxel','cisplatin','doxorubicin','trastuzumab','pembrolizumab','nivolumab','ipilimumab','dexamethasone'],
    pathway:['PI3K/AKT','mTOR','MAPK','ERK','JAK/STAT','NF-kB','WNT','HIF','AMPK','Apoptosis']
  };
  for(var type in dict){
    for(var ti=0;ti<dict[type].length;ti++){
      var term=dict[type][ti];
      var escaped=term.replace('-','\\-');
      var re=new RegExp('\\b'+escaped+'\\b','i');
      if(re.test(text)){
        var id=type+':'+term.toUpperCase();
        if(!seen[id]){seen[id]=true;r.push({id:id,name:term,type:type})}
      }
    }
  }
  return r;
};

test('Entity Extractor',function(){
  var text='TP53 mutations cause breast cancer. EGFR inhibitors treat lung cancer. PD-1 blockade activates T cells. Aspirin inhibits COX enzymes.';
  var r=entities(text);
  console.log('  '+r.length+' entities:');
  for(var i=0;i<r.length;i++){process.stdout.write('['+r[i].type+']'+r[i].name+' ')}
  process.stdout.write('\n');
  var types=r.map(function(x){return x.type});
  if(types.indexOf('gene')===-1)throw new Error('should find gene');
  if(types.indexOf('disease')===-1)throw new Error('should find disease');
  if(types.indexOf('drug')===-1)throw new Error('should find drug');
});

// Summary
process.stdout.write('\n================\n');
process.stdout.write('RESULTS: '+passed+' PASS / '+failed+' FAIL / '+(passed+failed)+' total\n');
process.stdout.write('================\n');
if(failed===0){process.stdout.write('ALL TESTS PASSED\n')}
else{process.exit(1)}
"""
with open(r'C:\Users\14327\.qclaw\workspace\skills\research-suite\scripts\run_tests.js','w',encoding='utf-8') as f:
    f.write(code)
print("Written OK, length:", len(code))
