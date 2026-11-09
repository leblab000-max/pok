"""v0.5 paired holdouts, fixed deal budgets, independent decision audits and resume."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
import sqlite3
import statistics
from time import perf_counter
from .adaptive import AdaptiveTournamentStrategy
from .advanced import AdvancedTournamentStrategy,ProfileStrategy
from .analysis import trace
from .benchmark import connect,summary
from .decision_analyzer import DecisionAnalyzer
from .engine import tournament
from .strategy import CallingBaseline,MathematicalBaseline

STRATEGIES=('call','math','advanced','adaptive')


def bootstrap(values: list[float],seed: int=51,alpha: float=.05,repeats: int=4000) -> list[float] | None:
    if len(values)<2:return None
    rng=random.Random(seed);n=len(values)
    means=sorted(sum(rng.choice(values) for _ in values)/n for _ in range(repeats))
    return [means[int(alpha/2*repeats)],means[min(repeats-1,int((1-alpha/2)*repeats))]]


def reports(rows: list[dict],config: dict) -> tuple[str,str]:
    header=['# Poker AI v0.5 benchmark','',f'Configuration: `{json.dumps(config,sort_keys=True)}`','',
            'Independent new seed window; whole tournaments are the sampling unit. Common seeds and seats do not imply identical later game histories.',
            'ROI intervals are percentile bootstrap 95% intervals (4000 resamples). Small/toy populations do not establish real-world strength.',
            'Potentially-costly rates use a deterministic subset audited by a separate larger-sample response-tree evaluator; these are not proven mistakes.',
            '', '| Opponents | Policy | N | Chip/hand | Place | ITM % | ROI % | ROI SE pp | ROI bootstrap CI % | Mean ms | P95 ms | Audits | Flagged % | Adapt ready % |',
            '|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|']
    table=[]
    for profile in ('tag','lag','passive'):
        for name in STRATEGIES:
            subset=[r['result'] for r in rows if r['profile']==profile and r['strategy']==name]
            if not subset:continue
            roi=[r['roi'] for r in subset];ci=bootstrap(roi);stats=summary(roi)
            timings=[t for r in subset for t in r['decision_seconds']]
            audited=sum(r['audited'] for r in subset);flagged=sum(r['flagged'] for r in subset)
            ndec=sum(len(r['decision_seconds']) for r in subset)
            ci_text='n/a' if ci is None else f'[{100*ci[0]:.1f}, {100*ci[1]:.1f}]'
            se='n/a' if stats['se'] is None else f"{100*stats['se']:.1f}"
            table.append((profile,f"| {profile} | {name} | {len(subset)} | {statistics.mean(r['chip_per_hand'] for r in subset):.2f} | {statistics.mean(r['place'] for r in subset):.2f} | {100*statistics.mean(r['itm'] for r in subset):.1f} | {100*stats['mean']:.1f} | {se} | {ci_text} | {1000*statistics.mean(timings) if timings else 0:.2f} | {1000*sorted(timings)[int(.95*len(timings))] if timings else 0:.2f} | {audited} | {100*flagged/max(1,audited):.1f} | {100*sum(r['adapt_ready'] for r in subset)/max(1,ndec):.1f} |"))
    paired=['', '## Paired Adaptive minus reference','',
            'Seed-paired percentile bootstrap intervals use Bonferroni alpha=.05/9 for nine comparisons. Minimum gate: 100 pairs and positive adjusted lower bound. No automatic promotion.',
            '', '| Profile | Reference | Pairs | Mean ROI difference pp | Adjusted bootstrap CI pp | Gate |',
            '|---|---|---:|---:|---|---|']
    lag_pairs=[]
    for profile in ('tag','lag','passive'):
        adaptive={r['seed']:r['result'] for r in rows if r['profile']==profile and r['strategy']=='adaptive'}
        for name in ('call','math','advanced'):
            differences=[adaptive[r['seed']]['roi']-r['result']['roi'] for r in rows if r['profile']==profile and r['strategy']==name and r['seed'] in adaptive]
            if not differences:continue
            ci=bootstrap(differences,alpha=.05/9)
            ci_text='n/a' if ci is None else f'[{100*ci[0]:.1f}, {100*ci[1]:.1f}]'
            passed=len(differences)>=100 and ci is not None and ci[0]>0
            line=f"| {profile} | {name} | {len(differences)} | {100*statistics.mean(differences):.1f} | {ci_text} | {'positive synthetic-population screen' if passed else 'not established'} |"
            paired.append(line)
            if profile=='lag':lag_pairs.append(line)
    lines=header+[t for _,t in table]+paired
    lines+=['','## Other metric uncertainty','', 'Mean/SE/normal 95% intervals per tournament; ROI inference above uses bootstrap. ITM normal bounds may exceed [0,1].','']
    for profile in ('tag','lag','passive'):
        for name in STRATEGIES:
            subset=[r['result'] for r in rows if r['profile']==profile and r['strategy']==name]
            if subset:lines.append(f"- {profile}/{name}: `{json.dumps({k:summary([r[k] for r in subset]) for k in ('chip_per_hand','place','itm')},sort_keys=True)}`")
    lines+=['','## Limits','',
            'Adaptive samples explicit fold/call subsets with exact side pots, but omits response re-raises and future-street betting. '
            'Ranges and response-price likelihoods are heuristic. Calibration learns public-stat centroids of these artificial opponents only. '
            'Advanced retains its v0.4 decision model as a frozen reference; shared optimizations preserve its numeric outputs. '
            'A fixed maximum joint-deal budget is used, not identical wall time: Advanced <=2*samples, Adaptive 2*samples, Mathematical 2*samples. '
            'Audit work is outside decision timing. No poker-room integration, spending or background training. Viewed holdouts must not be reused for tuning.']
    lag=['# LAG investigation','',
         'This report uses the predeclared new holdout window; no tuning was performed after inspecting its results.',
         '',*header[-2:],*[t for p,t in table if p=='lag'],'',*paired[4:6],*lag_pairs,'',
         '## Interpretation limits','',
         'Advanced uses all-fold/all-continue estimates and unconditional historical folds. Adaptive replaces these with explicit mixed responses, '
         'hand/price-conditioned folds and opportunity-counted public statistics. A result difference cannot isolate those changes from adaptation alone.',
         'Large disagreement rates can indicate flaws in the audit model as well as playing mistakes. The audit model itself omits re-raises/future bets, '
         'which is especially consequential against LAG. Small effective samples and opponent survival limit how often adaptation is enabled.',
         'Use separate calibration scenarios and an ablation study before attributing any advantage to opponent learning.']
    return '\n'.join(lines)+'\n','\n'.join(lag)+'\n'


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--count',type=int,default=9);p.add_argument('--seed',type=int,default=2000000)
    p.add_argument('--split',choices=['train','test'],default='test')
    p.add_argument('--samples',type=int,default=32);p.add_argument('--audit-samples',type=int,default=128)
    p.add_argument('--audit-stride',type=int,default=32);p.add_argument('--trace-stride',type=int,default=4)
    p.add_argument('--seconds',type=float,default=600);p.add_argument('--calibration')
    p.add_argument('--db',default='v05-benchmark.sqlite');p.add_argument('--out',default='reports/v05')
    args=p.parse_args()
    if (args.count<1 or not 2<=args.samples<=512 or not 2<=args.audit_samples<=512 or args.audit_stride<1 or args.trace_stride<1
            or not math.isfinite(args.seconds) or args.seconds<=0 or args.seed<0):p.error('Invalid computation budget')
    if (args.split=='test' and args.seed<2000000) or (args.split=='train' and args.seed+args.count>1000000):
        p.error('Training seeds below 1000000, fresh v0.5 test seeds >=2000000')
    source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    calibration_hash=hashlib.sha256(Path(args.calibration).read_bytes()).hexdigest() if args.calibration else None
    config=dict(version='0.5',source=source,samples=args.samples,split=args.split,calibration=calibration_hash,
                audit_samples=args.audit_samples,audit_stride=args.audit_stride,trace_stride=args.trace_stride,
                buy_in=100,fee=10,payouts=[450,270,180],players=9)
    identity=json.dumps(config,sort_keys=True);deadline=perf_counter()+args.seconds;stopped=False
    output=Path(args.out);output.mkdir(parents=True,exist_ok=True)
    analyzer=DecisionAnalyzer(args.audit_samples)
    with connect(args.db) as db:
        for seed in range(args.seed,args.seed+args.count):
            for profile in ('tag','lag','passive'):
                for name in STRATEGIES:
                    seat=seed%9
                    if db.execute('SELECT 1 FROM benchmark_runs WHERE config=? AND strategy=? AND profile=? AND seed=? AND seat=?',(identity,name,profile,seed,seat)).fetchone():continue
                    if perf_counter()>=deadline:stopped=True;break
                    factories=dict(call=CallingBaseline,math=lambda:MathematicalBaseline(seed,2*args.samples),
                                   advanced=lambda:AdvancedTournamentStrategy(seed,args.samples),
                                   adaptive=lambda:AdaptiveTournamentStrategy(seed,args.samples,calibration=args.calibration))
                    hero=factories[name]();players=[ProfileStrategy(profile,seed*10+i) for i in range(8)];players.insert(seat,hero)
                    timings=[];traces=[];audit_work=[];icm_count=ready=0
                    def sink(o,d,elapsed,context):
                        nonlocal icm_count,ready
                        if perf_counter()>=deadline:raise TimeoutError('Benchmark budget exhausted')
                        if o.seat!=seat:return
                        n=len(timings);timings.append(elapsed);icm_count+=bool(context.get('icm_used'));ready+=bool(context.get('adaptation_ready'))
                        if n%args.trace_stride==0 or n%args.audit_stride==0:
                            item=trace(o,d,elapsed,context);traces.append(item)
                            if n%args.audit_stride==0:audit_work.append((item,o,d,context))
                    try:
                        result=tournament(players,seed,decision_sink=sink,deadline=deadline)
                        audit_started=perf_counter()
                        for item,o,d,context in audit_work:
                            if perf_counter()>=deadline:raise TimeoutError('Audit budget exhausted; uncommitted tournament restarts')
                            item['independent_audit']=analyzer.analyze(o,d,context)
                        audit_seconds=perf_counter()-audit_started
                    except TimeoutError:stopped=True;break
                    place=result.places[seat];prize={1:450,2:270,3:180}.get(place,0)
                    hero_rows=[r for key,r in result.telemetry.items() if int(key.split(':')[0])==seat]
                    hands=sum(r['hands'] for r in hero_rows)
                    payload=dict(place=place,itm=float(place<=3),roi=(prize-110)/110,
                                 chip_per_hand=sum(r['chip_delta'] for r in hero_rows)/hands,
                                 hands=result.hands,places=result.places,final_stacks=result.stacks,
                                 decision_seconds=timings,icm_decisions=icm_count,adapt_ready=ready,
                                 audited=len(audit_work),flagged=sum(item['independent_audit']['potentially_costly'] for item,_,_,_ in audit_work),
                                 audit_seconds=audit_seconds)
                    cursor=db.execute('INSERT INTO benchmark_runs(config,strategy,profile,seed,seat,result) VALUES (?,?,?,?,?,?)',
                                      (identity,name,profile,seed,seat,json.dumps(payload)))
                    db.executemany('INSERT INTO decision_traces(run_id,risk,payload) VALUES (?,?,?)',
                                   [(cursor.lastrowid,t.get('independent_audit',{}).get('model_regret',0),json.dumps(t)) for t in traces])
                    db.commit()
                if stopped:break
            if stopped:break
        rows=[dict(strategy=s,profile=profile,seed=seed,seat=seat,result=json.loads(payload)) for s,profile,seed,seat,payload in db.execute(
            'SELECT strategy,profile,seed,seat,result FROM benchmark_runs WHERE config=? AND seed>=? AND seed<? ORDER BY seed,profile,strategy',
            (identity,args.seed,args.seed+args.count))]
        audits=[]
        for (payload,) in db.execute('SELECT t.payload FROM decision_traces t JOIN benchmark_runs b ON b.id=t.run_id WHERE b.config=? AND b.seed>=? AND b.seed<? ORDER BY t.id',(identity,args.seed,args.seed+args.count)):
            item=json.loads(payload)
            if 'independent_audit' in item:audits.append(item['independent_audit'])
    general,lag=reports(rows,config)
    (output/'BENCHMARK.md').write_text(general);(output/'LAG.md').write_text(lag)
    (output/'DECISIONS.md').write_text(DecisionAnalyzer.markdown(audits))
    (output/'results.json').write_text(json.dumps(dict(config=config,rows=rows),separators=(',',':'))+'\n')
    print(json.dumps(dict(completed=len(rows),requested=args.count*12,budget_exhausted=stopped,audits=len(audits),out=str(output))))

if __name__=='__main__':main()
