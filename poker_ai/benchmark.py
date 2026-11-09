"""Reproducible four-policy benchmark, transaction checkpoints and Markdown reports."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import platform
from pathlib import Path
import sqlite3
import statistics
from time import perf_counter
from .advanced import AdvancedTournamentStrategy, ProfileStrategy
from .analysis import trace, review
from .engine import tournament
from .strategy import CallingBaseline, ConservativeBaseline, MathematicalBaseline

STRATEGIES = ('fold','call','math','advanced')


def summary(values: list[float]) -> dict:
    n=len(values); mean=statistics.mean(values)
    se=statistics.stdev(values)/math.sqrt(n) if n>1 else None
    return dict(n=n,mean=mean,se=se,ci=None if se is None else [mean-1.96*se,mean+1.96*se])


def connect(path: str) -> sqlite3.Connection:
    db=sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS benchmark_runs (
          id INTEGER PRIMARY KEY, config TEXT NOT NULL, strategy TEXT NOT NULL,
          profile TEXT NOT NULL, seed INTEGER NOT NULL, seat INTEGER NOT NULL,
          result TEXT NOT NULL, UNIQUE(config,strategy,profile,seed,seat));
        CREATE TABLE IF NOT EXISTS decision_traces (
          id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES benchmark_runs(id),
          risk REAL NOT NULL, payload TEXT NOT NULL);
    ''')
    return db


def report(db: sqlite3.Connection, config: str, start: int, count: int) -> str:
    data = [(s,p,seed,json.loads(r)) for s,p,seed,r in db.execute(
        'SELECT strategy,profile,seed,result FROM benchmark_runs WHERE config=? AND seed>=? AND seed<? ORDER BY profile,strategy,seed',
        (config,start,start+count))]
    lines=['# Poker AI v0.4 benchmark','',f'Configuration: `{config}`', '',
           'Confidence intervals are exploratory normal 95% intervals over independent tournaments, not decisions. Small samples cannot establish superiority.',
           'Chip EV is realized net chip delta per hero hand; final tournament chip totals are not proof of action EV.',
           '', '| Opponents | Hero | N | Chip/hand | Place | ITM % | ROI % | ROI SE pp | ROI 95% CI % | Mean decision ms | P95 ms | ICM decisions |',
           '|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|']
    for profile in ('tag','lag','passive'):
        for strategy in STRATEGIES:
            rows=[r for s,p,_,r in data if s==strategy and p==profile]
            if not rows: continue
            roi=summary([r['roi'] for r in rows]); places=summary([r['place'] for r in rows])
            itm=summary([float(r['itm']) for r in rows]); chip=summary([r['chip_per_hand'] for r in rows])
            timings=[t for r in rows for t in r['decision_seconds']]
            ci='n/a' if roi['ci'] is None else f"[{100*roi['ci'][0]:.1f}, {100*roi['ci'][1]:.1f}]"
            se='n/a' if roi['se'] is None else f"{100*roi['se']:.1f}"
            p95=sorted(timings)[min(len(timings)-1,int(.95*len(timings)))] if timings else 0
            lines.append(f"| {profile} | {strategy} | {len(rows)} | {chip['mean']:.2f} | {places['mean']:.2f} | {100*itm['mean']:.1f} | {100*roi['mean']:.1f} | {se} | {ci} | {1000*statistics.mean(timings) if timings else 0:.2f} | {1000*p95:.2f} | {sum(r['icm_decisions'] for r in rows)} |")
    lines += ['', '## Paired advanced minus legacy comparisons','',
              'Common seeds and hero-seat rotation; differing actions change later game trajectories.',
              'Bonferroni normal intervals cover 9 comparisons. Gate requires >=100 pairs per comparison and positive lower bound; never promotes a policy.',
              '', '| Opponents | Reference | Pairs | ROI difference pp | Adjusted interval pp | Gate |','|---|---|---:|---:|---|---|']
    z=statistics.NormalDist().inv_cdf(1-.05/(2*9))
    for profile in ('tag','lag','passive'):
        advanced={seed:r for s,p,seed,r in data if s=='advanced' and p==profile}
        for baseline in ('fold','call','math'):
            paired=[advanced[seed]['roi']-r['roi'] for s,p,seed,r in data if s==baseline and p==profile and seed in advanced]
            if not paired: continue
            stats=summary(paired); half=None if stats['se'] is None else z*stats['se']
            passed=stats['n']>=100 and half is not None and stats['mean']-half>0
            ci='n/a' if half is None else f"[{100*(stats['mean']-half):.1f}, {100*(stats['mean']+half):.1f}]"
            lines.append(f"| {profile} | {baseline} | {stats['n']} | {100*stats['mean']:.1f} | {ci} | {'PASS' if passed else 'insufficient evidence'} |")
    lines += ['', '## Other metric uncertainty','',
              'Mean, standard error and 95% CI (chip/hand, place, ITM fraction) follow. ITM normal intervals may extend beyond [0,1].', '']
    for profile in ('tag','lag','passive'):
        for strategy in STRATEGIES:
            rows=[r for s,p,_,r in data if s==strategy and p==profile]
            if rows:
                values={k:summary([float(r[k]) for r in rows]) for k in ('chip_per_hand','place','itm')}
                lines.append(f'- {profile}/{strategy}: `{json.dumps(values,sort_keys=True)}`')
    lines += ['', '## Limits','',
              'Heuristic opponent policies; uniform initial dealt-card priors; action-likelihood inference is uncalibrated. '
              'Few equity samples can select noisy actions. Multiway raises omit mixed responses and future betting. '
              'ICM is applied only to terminal heads-up calls and a restricted short-stack preflop push/fold subgame. '
              'No positive profitability or general superiority claim. Runtime measurements depend on hardware. '
              'Do not reuse a viewed test set for tuning; reserve a new confirmation set.']
    return '\n'.join(lines)+'\n'


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count',type=int,default=9,help='Seeds per strategy per profile; total tournaments = count*12')
    parser.add_argument('--seed',type=int,default=1000000)
    parser.add_argument('--split',choices=['train','test'],default='test')
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--seconds',type=float,default=600)
    parser.add_argument('--db',default='benchmark.sqlite')
    parser.add_argument('--report',default='benchmark.md')
    parser.add_argument('--export',default=None,help='Optional raw completed-run JSON for audit')
    parser.add_argument('--buy-in',type=float,default=100)
    parser.add_argument('--fee',type=float,default=10)
    parser.add_argument('--payouts',default='.5,.3,.2',help='Descending prize-pool fractions summing to one')
    args=parser.parse_args()
    try: fractions=tuple(float(v) for v in args.payouts.split(','))
    except ValueError: parser.error('Invalid payouts')
    if (args.count<1 or args.samples<2 or not math.isfinite(args.seconds) or args.seconds<=0
        or not math.isfinite(args.buy_in) or args.buy_in<=0 or not math.isfinite(args.fee) or args.fee<0
        or not 1<=len(fractions)<=9 or any(not math.isfinite(v) or v<0 for v in fractions)
        or abs(sum(fractions)-1)>1e-9 or any(a<b for a,b in zip(fractions,fractions[1:]))):
        parser.error('Invalid experiment configuration')
    if args.seed<0 or (args.split=='test' and args.seed<1000000) or (args.split=='train' and args.seed+args.count>1000000):
        parser.error('Train seeds: [0,1000000); test seeds: >=1000000')
    source_hash=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    config=json.dumps(dict(source=source_hash,samples=args.samples,split=args.split,buy_in=args.buy_in,
                           fee=args.fee,payouts=fractions,players=9,version='0.4'),sort_keys=True)
    deadline=perf_counter()+args.seconds; stopped=False
    with connect(args.db) as db:
        # Interleave candidates/profiles per seed so partial runs remain comparable.
        for seed in range(args.seed,args.seed+args.count):
            for profile in ('tag','lag','passive'):
                for name in STRATEGIES:
                    seat=seed%9
                    if db.execute('SELECT 1 FROM benchmark_runs WHERE config=? AND strategy=? AND profile=? AND seed=? AND seat=?',(config,name,profile,seed,seat)).fetchone(): continue
                    if perf_counter()>=deadline: stopped=True; break
                    factory={'fold':ConservativeBaseline,'call':CallingBaseline,
                             'math':lambda:MathematicalBaseline(seed,args.samples),
                             'advanced':lambda:AdvancedTournamentStrategy(seed,args.samples)}
                    hero=factory[name]()
                    players=[ProfileStrategy(profile,seed*10+i) for i in range(8)]
                    players.insert(seat,hero)
                    traces=[]; times=[]; icm_used=0
                    def sink(o,d,elapsed,analysis):
                        nonlocal icm_used
                        if perf_counter()>=deadline: raise TimeoutError('Benchmark decision budget exhausted')
                        if o.seat==seat:
                            times.append(elapsed); icm_used+=bool(analysis.get('icm_used'))
                            traces.append(trace(o,d,elapsed,analysis))
                    try:
                        result=tournament(players,seed,payouts=tuple(v*9*args.buy_in for v in fractions),decision_sink=sink,deadline=deadline)
                    except TimeoutError: stopped=True; break
                    place=result.places[seat]
                    prize=fractions[place-1]*9*args.buy_in if place<=len(fractions) else 0
                    hero_rows=[row for key,row in result.telemetry.items() if int(key.split(':')[0])==seat]
                    hands=sum(r['hands'] for r in hero_rows)
                    payload=dict(tournament=asdict(result),place=place,itm=place<=len(fractions),
                                 roi=(prize-args.buy_in-args.fee)/(args.buy_in+args.fee),
                                 chip_per_hand=sum(r['chip_delta'] for r in hero_rows)/hands,
                                 decision_seconds=times,icm_decisions=icm_used)
                    cursor=db.execute('INSERT INTO benchmark_runs(config,strategy,profile,seed,seat,result) VALUES (?,?,?,?,?,?)',
                                      (config,name,profile,seed,seat,json.dumps(payload)))
                    db.executemany('INSERT INTO decision_traces(run_id,risk,payload) VALUES (?,?,?)',
                                   [(cursor.lastrowid,t['estimated_swing'],json.dumps(t)) for t in traces])
                    db.commit()
                if stopped: break
            if stopped: break
        Path(args.report).write_text(report(db,config,args.seed,args.count))
        completed=db.execute('SELECT COUNT(*) FROM benchmark_runs WHERE config=? AND seed>=? AND seed<?',(config,args.seed,args.seed+args.count)).fetchone()[0]
        if args.export:
            exported=[dict(strategy=s,profile=p,seed=seed,seat=seat,result=json.loads(r))
                      for s,p,seed,seat,r in db.execute(
                        'SELECT strategy,profile,seed,seat,result FROM benchmark_runs WHERE config=? AND seed>=? AND seed<? ORDER BY seed,profile,strategy',
                        (config,args.seed,args.seed+args.count))]
            Path(args.export).write_text(json.dumps(dict(config=json.loads(config),python=platform.python_version(),
                                                        machine=platform.machine(),rows=exported),indent=2))
    Path(args.report).with_suffix('.review.md').write_text(review(args.db,config=config,seed_range=(args.seed,args.seed+args.count)))
    print(json.dumps(dict(completed=completed,requested=args.count*12,budget_exhausted=stopped,report=args.report,db=args.db)))

if __name__=='__main__': main()
