"""Same frozen public spots, equity samples and RNG seeds for before/after timings."""
import argparse
import cProfile
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import pstats
import sqlite3
import statistics
from time import perf_counter
from poker_ai.strategy import Observation,PublicAction
from poker_ai.advanced import AdvancedTournamentStrategy


def decode(data):
    data=dict(data)
    for key in ('hole_cards','board','folded','payouts','history'):
        data[key]=tuple(data.get(key,()))
    for key in ('stacks','contributions','street_contributions'):
        data[key]=tuple(tuple(v) for v in data.get(key,()))
    data['public_actions']=tuple(PublicAction(**{**v,'board':tuple(v['board'])}) for v in data.get('public_actions',()))
    return Observation(**data)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='v04-benchmark.sqlite')
    p.add_argument('--spots',default='reports/v05/profile-spots.json')
    p.add_argument('--output',default='reports/v05/profile-before.json')
    p.add_argument('--samples',type=int,default=32)
    p.add_argument('--repeat',type=int,default=3)
    args=p.parse_args()
    path=Path(args.spots)
    if not path.exists():
        buckets={0:[],3:[],4:[],5:[]}
        with sqlite3.connect(args.db) as db:
            for (payload,) in db.execute("SELECT t.payload FROM decision_traces t JOIN benchmark_runs b ON b.id=t.run_id WHERE b.strategy='advanced' ORDER BY t.id"):
                o=json.loads(payload)['observation']; bucket=buckets[len(o['board'])]
                if len(bucket)<12 and o not in bucket: bucket.append(o)
                if all(len(b)==12 for b in buckets.values()):break
        path.write_text(json.dumps([o for b in buckets.values() for o in b],indent=2))
    observations=[decode(o) for o in json.loads(path.read_text())]
    timings=[]; analyses=[]
    for repeat in range(args.repeat):
        for i,o in enumerate(observations):
            strategy=AdvancedTournamentStrategy(seed=600+i,samples=args.samples)
            started=perf_counter(); strategy.decide(o); timings.append(perf_counter()-started)
            if repeat==0:analyses.append(strategy.last_analysis)
    profiler=cProfile.Profile()
    def workload():
        for i,o in enumerate(observations):AdvancedTournamentStrategy(600+i,args.samples).decide(o)
    profiler.runcall(workload)
    stats=pstats.Stats(profiler)
    expensive=sorted(stats.stats.items(),key=lambda kv:kv[1][3],reverse=True)[:20]
    result=dict(samples=args.samples,repeat=args.repeat,spots=len(observations),
                source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path('poker_ai').glob('*.py')))).hexdigest(),
                mean_ms=statistics.mean(timings)*1000,p95_ms=sorted(timings)[int(.95*len(timings))]*1000,
                timings=timings,analyses=analyses,
                cumulative_profile=[dict(function=str(k),calls=v[1],seconds=v[3]) for k,v in expensive])
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('timings','analyses','cumulative_profile')}))

if __name__=='__main__':main()
