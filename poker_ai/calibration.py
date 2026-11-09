"""Fit public-stat profile centroids using training-only simulated tournaments."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from .advanced import ProfileStrategy
from .engine import tournament
from .opponents import OpponentModel
from .strategy import CallingBaseline


class PublicObserver(CallingBaseline):
    def __init__(self):self.model=OpponentModel()
    def start_hand(self,hand_id,seats):self.model.start_hand(hand_id,seats)
    def observe(self,event):self.model.observe(event)


def calibrate(count: int=30,seed: int=100) -> dict:
    if count<1 or seed<0 or seed+count>=1000000:raise ValueError('Use training seeds below 1000000')
    centroids={};records=[]
    for profile in ('tag','lag','passive'):
        totals={k:[0,0] for k in ('vpip','pfr','aggression')}
        for trial in range(seed,seed+count):
            observer=PublicObserver();players=[observer]+[ProfileStrategy(profile,trial*10+s) for s in range(8)]
            tournament(players,trial)
            for seat in range(1,9):
                snapshot=observer.model.snapshot(seat)
                for k in totals:
                    totals[k][0]+=snapshot[k]['successes'];totals[k][1]+=snapshot[k]['observations']
                records.append(dict(profile=profile,seed=trial,seat=seat,statistics=snapshot))
        # Weak Beta(1,1) regularization, no tournament outcomes used as targets.
        centroids[profile]={k:(success+1)/(n+2) for k,(success,n) in totals.items()}
    return dict(version=1,split='train',seed=seed,count=count,centroids=centroids,records=records,
                note='Public action-rate centroids for synthetic policies, not GTO ranges or real-population calibration.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--count',type=int,default=30);p.add_argument('--seed',type=int,default=100)
    p.add_argument('--output',default='calibration.json')
    args=p.parse_args();result=calibrate(args.count,args.seed)
    result['source']=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['centroids'],indent=2))

if __name__=='__main__':main()
