import os, re, glob, math, warnings
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
warnings.filterwarnings('ignore')

AA='ACDEFGHIKLMNPQRSTVWY'; AA2I={a:i for i,a in enumerate(AA)}
MUT_RE=re.compile(r'^([ACDEFGHIKLMNPQRSTVWY])(\d+)([ACDEFGHIKLMNPQRSTVWY])$')
SOURCE_KEYS=('abundance','expression','surface')
TARGET_KEYS=('activity','function','binding')
RNG_SEEDS=list(range(10)); BUDGETS=[4,8,16,32,64]; INIT_MODES=['random','source_stratified']
TAU_GRID=[-1.0,0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]

def parse_mut(s):
    m=MUT_RE.match(str(s)); return None if not m else (m.group(1),int(m.group(2)),m.group(3))

def mutation_features(mutants):
    parsed=[parse_mut(x) for x in mutants]
    if any(x is None for x in parsed): raise ValueError('non-single mutation')
    pos=np.array([x[1] for x in parsed],float); pmax=max(1.0,pos.max())
    X=np.zeros((len(parsed),41),float); X[:,0]=pos/pmax
    for r,(a,p,b) in enumerate(parsed): X[r,1+AA2I[a]]=1; X[r,21+AA2I[b]]=1
    return X

def fspear(a,b):
    if len(a)<3: return np.nan
    r=spearmanr(a,b).statistic
    return float(r) if np.isfinite(r) else np.nan

def target_pct(y): return pd.Series(y).rank(method='average',pct=True).to_numpy(float)

def seed_idx(source,n,seed,mode):
    rng=np.random.default_rng(seed); N=len(source); n=min(n,N)
    if mode=='random': return np.array(rng.choice(N,size=n,replace=False),int)
    order=np.argsort(source); edges=np.linspace(0,N,n+1,dtype=int); out=[]
    for i in range(n):
        lo,hi=edges[i],edges[i+1]
        if hi>lo: out.append(int(order[rng.integers(lo,hi)]))
    if len(out)<n:
        rem=np.setdiff1d(np.arange(N),np.array(out,int)); out += [int(x) for x in rng.choice(rem,size=n-len(out),replace=False)]
    return np.array(out,int)

def et_predict(X,y,tr,te,seed):
    m=ExtraTreesRegressor(n_estimators=48,min_samples_leaf=2,max_features='sqrt',random_state=seed,n_jobs=-1)
    m.fit(X[tr],y[tr]); return m.predict(X[te])

def metrics(y,p):
    rho=fspear(y,p); n=len(y)
    if n<10: return rho,np.nan
    k=max(1,int(math.ceil(.1*n))); a=set(np.argsort(y)[-k:]); b=set(np.argsort(p)[-k:])
    return rho,float((len(a&b)/k)/.1)

pairs=[]; data={}
for fp in sorted(glob.glob('synfit/dataset/multi_fitness_data/*.csv')):
    df=pd.read_csv(fp)
    if 'mutant' not in df.columns: continue
    cols=[c for c in df.columns if c.startswith('DMS_score_')]
    src=[c for c in cols if any(k in c.lower() for k in SOURCE_KEYS)]
    tgt=[c for c in cols if any(k in c.lower() for k in TARGET_KEYS)]
    protein=os.path.basename(fp)[:-4]
    for sc in src:
        for tc in tgt:
            sub=df[['mutant',sc,tc]].copy(); sub['parsed']=sub.mutant.map(parse_mut); sub=sub[sub.parsed.notna()]
            sub[sc]=pd.to_numeric(sub[sc],errors='coerce'); sub[tc]=pd.to_numeric(sub[tc],errors='coerce')
            sub=sub[np.isfinite(sub[sc]) & np.isfinite(sub[tc])].reset_index(drop=True)
            if len(sub)<100: continue
            key=f'{protein}::{sc}::{tc}'; pairs.append(dict(pair_id=key,protein=protein,source_col=sc,target_col=tc,n=len(sub))); data[key]=(sub,sc,tc)
if not pairs: raise RuntimeError('no proxy-function pairs')
pair_df=pd.DataFrame(pairs); pair_df.to_csv('heldout_pair_catalog.csv',index=False)
proteins=sorted(pair_df.protein.unique())
print('PROTEINS',proteins); print(pair_df[['protein','n','source_col','target_col']].to_string(index=False))

rows=[]
for p in pairs:
    key=p['pair_id']; protein=p['protein']; df,sc,tc=data[key]
    s=df[sc].to_numpy(float); y=df[tc].to_numpy(float); X0=mutation_features(df.mutant.astype(str).to_numpy()); Xs=np.column_stack([X0,s])
    for mode in INIT_MODES:
        for nlab in BUDGETS:
            if nlab>=len(df)-10: continue
            for seed in RNG_SEEDS:
                tr=seed_idx(s,nlab,seed,mode); te=np.setdiff1d(np.arange(len(df)),tr)
                rs,es=metrics(y[te],s[te]); lin=Ridge(alpha=1).fit(s[tr,None],y[tr]); rl,el=metrics(y[te],lin.predict(s[te,None]))
                pt=et_predict(X0,y,tr,te,seed); ps=et_predict(Xs,y,tr,te,seed); rt,et=metrics(y[te],pt); ra,ea=metrics(y[te],ps)
                rows.append(dict(pair_id=key,protein=protein,init_mode=mode,n_labels=nlab,seed=seed,seed_rho=fspear(s[tr],y[tr]),rho_static_source=rs,rho_linear_source=rl,rho_target_only=rt,rho_source_aware=ra,enrich_static_source=es,enrich_linear_source=el,enrich_target_only=et,enrich_source_aware=ea))
pred=pd.DataFrame(rows); pred.to_csv('heldout_prediction_episodes.csv',index=False)

gates=[]; tau_map={}
for held in proteins:
  for mode in INIT_MODES:
    for nlab in BUDGETS:
      dev=pred[(pred.protein!=held)&(pred.init_mode==mode)&(pred.n_labels==nlab)]; test=pred[(pred.protein==held)&(pred.init_mode==mode)&(pred.n_labels==nlab)]
      if len(dev)==0 or len(test)==0: continue
      best_tau=0.4; best=-1e9
      for tau in TAU_GRID:
        vals=np.where(dev.seed_rho.fillna(-2).to_numpy()>=tau,dev.rho_source_aware,dev.rho_target_only); score=np.nanmean(vals)
        if score>best: best=float(score); best_tau=float(tau)
      tau_map[(held,mode,nlab)]=best_tau; gv=np.where(test.seed_rho.fillna(-2).to_numpy()>=best_tau,test.rho_source_aware,test.rho_target_only)
      gates.append(dict(protein=held,init_mode=mode,n_labels=nlab,tau_from_other_proteins=best_tau,target_only_rho=np.nanmean(test.rho_target_only),source_aware_rho=np.nanmean(test.rho_source_aware),gated_rho=np.nanmean(gv),static_source_rho=np.nanmean(test.rho_static_source),delta_source_aware_vs_target=np.nanmean(test.rho_source_aware-test.rho_target_only),delta_gated_vs_target=np.nanmean(gv-test.rho_target_only),n_episodes=len(test)))
gate=pd.DataFrame(gates); gate.to_csv('heldout_lopo_summary.csv',index=False)

seq=[]; n0=8; batch=8; rounds=4
for p in pairs:
    held=p['protein']; key=p['pair_id']; df,sc,tc=data[key]; s=df[sc].to_numpy(float); y=df[tc].to_numpy(float); pct=target_pct(y)
    X0=mutation_features(df.mutant.astype(str).to_numpy()); Xs=np.column_stack([X0,s])
    for mode in INIT_MODES:
      tau=tau_map.get((held,mode,8),0.4)
      for seed in RNG_SEEDS:
        init=seed_idx(s,n0,seed,mode)
        for method in ['random','static_source','target_only','source_aware','gated']:
          rng=np.random.default_rng(10000+seed); obs=list(map(int,init)); queried=[]
          for r in range(rounds):
            avail=np.setdiff1d(np.arange(len(df)),np.array(obs,int)); b=min(batch,len(avail))
            if b==0: break
            if method=='random': q=np.array(rng.choice(avail,size=b,replace=False),int)
            elif method=='static_source': q=avail[np.argsort(s[avail])[-b:]]
            else:
              tr=np.array(obs,int)
              if method=='target_only': use=False
              elif method=='source_aware': use=True
              else:
                rr=fspear(s[tr],y[tr]); use=bool(np.isfinite(rr) and rr>=tau)
              pp=et_predict(Xs if use else X0,y,tr,avail,seed+100*r); q=avail[np.argsort(pp)[-b:]]
            obs.extend(map(int,q)); queried.extend(map(int,q))
          q=np.array(queried,int)
          if len(q): seq.append(dict(pair_id=key,protein=held,init_mode=mode,seed=seed,method=method,tau=tau,query_percentile_mean=np.mean(pct[q]),top_decile_hit_rate=np.mean(pct[q]>=.9),top_quartile_hit_rate=np.mean(pct[q]>=.75),n_queried=len(q)))
seq=pd.DataFrame(seq); seq.to_csv('heldout_sequential_episodes.csv',index=False)
seqsum=seq.groupby(['protein','init_mode','method'])[['query_percentile_mean','top_decile_hit_rate','top_quartile_hit_rate']].agg(['mean','std']).reset_index(); seqsum.columns=['_'.join([str(x) for x in c if x!='']).rstrip('_') for c in seqsum.columns]; seqsum.to_csv('heldout_sequential_summary.csv',index=False)
agg=gate.groupby(['init_mode','n_labels'])[['target_only_rho','source_aware_rho','gated_rho','static_source_rho','delta_source_aware_vs_target','delta_gated_vs_target']].mean().reset_index(); agg.to_csv('heldout_aggregate.csv',index=False)
seqagg=seq.groupby(['init_mode','method'])[['query_percentile_mean','top_decile_hit_rate','top_quartile_hit_rate']].mean().reset_index(); seqagg.to_csv('heldout_sequential_aggregate.csv',index=False)
open('heldout_summary.md','w').write('# Real leave-one-protein-out proxy→function experiment\n\nProteins: %d; directed assay pairs: %d; repeats: %d.\n\nGate thresholds are tuned only on other proteins. ExtraTrees is a cheap sanity baseline, not PRIMO/FolDE. Both random and source-stratified target seeds are reported.\n' % (len(proteins),len(pairs),len(RNG_SEEDS)))
print(agg.to_string(index=False)); print(seqagg.to_string(index=False))
