"""v0.6 seeded policy league: training selection, ablations and untouched holdouts."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from time import perf_counter
from .adaptive import AdaptiveTournamentStrategy
from .advanced import AdvancedTournamentStrategy,ProfileStrategy
from .benchmark import connect
from .portfolio import PortfolioTournamentStrategy
from .strategy import CallingBaseline,MathematicalBaseline,Decision
from .engine import tournament
from .ranges import preflop_strength,hand_class,board_strength


class PressureStrategy(ProfileStrategy):
    """Unseen evaluation family: larger sizes and hand-independent aggression."""
    def __init__(self,seed: int):super().__init__('lag',seed)
    def decide(self,o):
        strength=board_strength(o.hole_cards,o.board) if o.board else preflop_strength(hand_class(o.hole_cards))
        if o.minimum_raise_to is not None and (strength>.65 or self.rng.random()<.30):
            current=dict(o.street_contributions)[o.seat]
            target=min(o.maximum_raise_to,max(o.minimum_raise_to,current+o.to_call+max(o.big_blind,3*o.pot//4)))
            return Decision('raise',target)
        if not o.to_call:return Decision('check')
        return Decision('call' if strength>o.to_call/max(1,o.pot+o.to_call)+.15 else 'fold')


def policy(name: str,seed: int,samples: int,calibration: str | None,selection: dict | None=None):
    if name=='math':return MathematicalBaseline(seed,2*samples)
    if name=='advanced':return AdvancedTournamentStrategy(seed,samples)
    if name=='adaptive':return AdaptiveTournamentStrategy(seed,samples,calibration=calibration)
    if name=='call':return CallingBaseline()
    if name in ('candidate','no_adapt','no_rollout','toggle_adapt'):
        if selection is None:raise ValueError('Frozen training selection required')
        chosen=selection['selected']
        rollouts=8 if chosen in ('lookahead','fixed') else 0
        adapt=chosen!='fixed'
        if name=='no_adapt':adapt=False
        if name=='toggle_adapt':adapt=not adapt
        if name=='no_rollout':rollouts=0
        return PortfolioTournamentStrategy(seed,samples,calibration=calibration,adapt=adapt,rollouts=rollouts)
    if name in ('blend','lookahead','fixed'):
        return PortfolioTournamentStrategy(seed,samples,calibration=calibration,adapt=name!='fixed',rollouts=0 if name=='blend' else 8)
    raise ValueError('Unknown policy '+name)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split',choices=['train','test'],default='train')
    p.add_argument('--seed',type=int,default=10000);p.add_argument('--count',type=int,default=18)
    p.add_argument('--policies',default='math,advanced,adaptive,blend,lookahead,fixed')
    p.add_argument('--profiles',default='tag,lag,passive')
    p.add_argument('--samples',type=int,default=32);p.add_argument('--seconds',type=float,default=600)
    p.add_argument('--calibration',default='reports/v05/calibration.json');p.add_argument('--selection')
    p.add_argument('--db',default='v06-league.sqlite');p.add_argument('--out',default='reports/v06/train')
    args=p.parse_args();names=tuple(args.policies.split(','));profiles=tuple(args.profiles.split(','))
    known={'math','advanced','adaptive','call','blend','lookahead','fixed','candidate','no_adapt','no_rollout','toggle_adapt'}
    if (not names or len(set(names))!=len(names) or not set(names)<=known or not profiles or len(set(profiles))!=len(profiles)
            or not set(profiles)<={'tag','lag','passive','pressure','mixed'} or args.count<1 or not 2<=args.samples<=128
            or args.seconds<=0 or not math.isfinite(args.seconds) or args.seed<0):p.error('Invalid study configuration')
    if (args.split=='train' and args.seed+args.count>1000000) or (args.split=='test' and args.seed<3000000):
        p.error('Training seeds below 1000000; fresh holdouts at least 3000000')
    source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    selected=json.loads(Path(args.selection).read_text()) if args.selection else None
    if selected and (selected.get('split')!='train' or selected.get('source')!=source):p.error('Selection must match current frozen training source')
    if args.split=='test' and any(n in ('blend','lookahead','fixed') for n in names):p.error('Use frozen candidate aliases on holdout')
    config=dict(version='0.6',source=source,split=args.split,samples=args.samples,
                calibration=hashlib.sha256(Path(args.calibration).read_bytes()).hexdigest(),
                selection=hashlib.sha256(Path(args.selection).read_bytes()).hexdigest() if args.selection else None,
                buy_in=100,fee=10,payouts=[450,270,180],players=9,rollout_samples=8)
    identity=json.dumps(config,sort_keys=True);deadline=perf_counter()+args.seconds;stopped=False
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    with connect(args.db) as db:
        for seed in range(args.seed,args.seed+args.count):
            for profile in profiles:
                for name in names:
                    seat=seed%9
                    if db.execute('SELECT 1 FROM benchmark_runs WHERE config=? AND strategy=? AND profile=? AND seed=? AND seat=?',(identity,name,profile,seed,seat)).fetchone():continue
                    if perf_counter()>=deadline:stopped=True;break
                    hero=policy(name,seed,args.samples,args.calibration,selected)
                    players=[]
                    for i in range(8):
                        if profile=='pressure':opponent=PressureStrategy(seed*10+i)
                        else:opponent=ProfileStrategy(('tag','lag','passive')[i%3] if profile=='mixed' else profile,seed*10+i)
                        players.append(opponent)
                    players.insert(seat,hero)
                    times=[];routes={};roll_calls=roll_overrides=sim_raises=future_streets=0;traces=[]
                    def sink(o,d,elapsed,analysis):
                        nonlocal roll_calls,roll_overrides,sim_raises,future_streets
                        if perf_counter()>=deadline:raise TimeoutError('League time budget reached')
                        if o.seat!=seat:return
                        times.append(elapsed);route=analysis.get('route',name);routes[route]=routes.get(route,0)+1
                        roll_calls+=bool(analysis.get('rollout_attempted'));roll_overrides+=bool(analysis.get('rollout_override'))
                        sim_raises+=analysis.get('rollout',{}).get('simulated_raises',0)
                        future_streets+=analysis.get('rollout',{}).get('future_streets',0)
                        if len(times)%32==1:traces.append(dict(observation=asdict(o),decision=asdict(d),analysis=analysis,seconds=elapsed))
                    try:result=tournament(players,seed,decision_sink=sink,deadline=deadline)
                    except TimeoutError:stopped=True;break
                    place=result.places[seat];prize={1:450,2:270,3:180}.get(place,0)
                    telemetry=[v for k,v in result.telemetry.items() if int(k.split(':')[0])==seat]
                    payload=dict(place=place,itm=float(place<=3),roi=(prize-110)/110,
                                 chip_per_hand=sum(v['chip_delta'] for v in telemetry)/sum(v['hands'] for v in telemetry),
                                 hands=result.hands,places=result.places,final_stacks=result.stacks,
                                 decision_seconds=times,routes=routes,rollout_calls=roll_calls,
                                 rollout_overrides=roll_overrides,simulated_raises=sim_raises,future_streets=future_streets)
                    cursor=db.execute('INSERT INTO benchmark_runs(config,strategy,profile,seed,seat,result) VALUES (?,?,?,?,?,?)',
                                      (identity,name,profile,seed,seat,json.dumps(payload)))
                    db.executemany('INSERT INTO decision_traces(run_id,risk,payload) VALUES (?,?,?)',
                                   [(cursor.lastrowid,0,json.dumps(t)) for t in traces]);db.commit()
                if stopped:break
            if stopped:break
        rows=[dict(strategy=n,profile=pr,seed=seed,seat=seat,result=json.loads(r)) for n,pr,seed,seat,r in db.execute(
            'SELECT strategy,profile,seed,seat,result FROM benchmark_runs WHERE config=? AND seed>=? AND seed<? ORDER BY seed,profile,strategy',
            (identity,args.seed,args.seed+args.count)) if n in names and pr in profiles]
    (out/'results.json').write_text(json.dumps(dict(config=config,rows=rows),separators=(',',':'))+'\n')
    lines=['# League results','',f'Configuration: `{identity}`','','| Profile | Policy | N | ROI % | Place | ITM % | Mean ms | Advanced route % | Rollout calls | Overrides |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for profile in profiles:
        for name in names:
            subset=[r['result'] for r in rows if r['profile']==profile and r['strategy']==name]
            if not subset:continue
            times=[t for r in subset for t in r['decision_seconds']]
            advanced=sum(r['routes'].get('advanced',0) for r in subset)
            lines.append(f"| {profile} | {name} | {len(subset)} | {100*statistics.mean(r['roi'] for r in subset):.1f} | {statistics.mean(r['place'] for r in subset):.2f} | {100*statistics.mean(r['itm'] for r in subset):.1f} | {1000*statistics.mean(times) if times else 0:.2f} | {100*advanced/max(1,len(times)):.1f} | {sum(r['rollout_calls'] for r in subset)} | {sum(r['rollout_overrides'] for r in subset)} |")
    (out/'LEAGUE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(completed=len(rows),requested=args.count*len(profiles)*len(names),budget_exhausted=stopped,out=str(out))))

if __name__=='__main__':main()
