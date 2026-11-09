"""Paired held-out evaluation gate. Never automatically installs a candidate."""
import argparse
import json
import math
import statistics
from poker_ai.engine import tournament
from poker_ai.strategy import MathematicalBaseline, CallingBaseline, ConservativeBaseline

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start-seed',type=int,default=1000000)
    p.add_argument('--count',type=int,default=100)
    args=p.parse_args()
    if args.count<2 or args.start_seed<1000000: p.error('Use >=2 held-out seeds, starting at 1000000')
    differences=[]
    for seed in range(args.start_seed,args.start_seed+args.count):
        values=[]
        for candidate in (False,True):
            players=[CallingBaseline() if i%2 else ConservativeBaseline() for i in range(8)]
            seat=seed%9
            players.insert(seat,MathematicalBaseline(seed,8) if candidate else CallingBaseline())
            result=tournament(players,seed)
            values.append(({1:450,2:270,3:180}.get(result.places[seat],0)-110)/110)
        differences.append(values[1]-values[0])
    mean=statistics.mean(differences)
    half=1.96*statistics.stdev(differences)/math.sqrt(args.count)
    print(json.dumps(dict(seeds=[args.start_seed,args.start_seed+args.count-1],pairs=args.count,
                         mean_roi_difference=mean,approx_95_ci=[mean-half,mean+half],
                         gate_passed=args.count>=100 and mean-half>0,
                         note='Exploratory paired normal interval. Freeze candidate before holdout; account for repeated testing. No automatic promotion.'),indent=2))
if __name__=='__main__': main()
