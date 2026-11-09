"""Prequential public-stat calibration check on separate training-validation seeds."""
import argparse
import json
from pathlib import Path
import statistics
from poker_ai.engine import tournament
from poker_ai.advanced import ProfileStrategy
from poker_ai.opponents import OpponentModel
from poker_ai.strategy import CallingBaseline


class Validator(CallingBaseline):
    def __init__(self,profile,calibration):
        self.profile=profile
        self.models={'default':OpponentModel(),'calibrated':OpponentModel(calibration=calibration)}
        self.rows={name:dict(style_brier=[],style_correct=[],fold_brier=[]) for name in self.models}
    def start_hand(self,hand_id,seats):
        for name,model in self.models.items():
            for seat in seats:
                if seat==0 or not model.snapshot(seat)['ready']:continue
                weights=model.profile_weights(seat)
                self.rows[name]['style_brier'].append(sum((w-(p==self.profile))**2 for p,w in weights.items()))
                self.rows[name]['style_correct'].append(max(weights,key=weights.get)==self.profile)
            model.start_hand(hand_id,seats)
    def observe(self,event):
        for name,model in self.models.items():
            if event.seat!=0 and event.facing_raise and event.to_call>0:
                probability=model.snapshot(event.seat)['fold_to_raise']['mean']
                self.rows[name]['fold_brier'].append((probability-(event.action=='fold'))**2)
            model.observe(event)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--calibration',default='reports/v05/calibration.json')
    p.add_argument('--seed',type=int,default=500);p.add_argument('--count',type=int,default=10)
    p.add_argument('--output',default='reports/v05/CALIBRATION_VALIDATION.json')
    args=p.parse_args()
    if args.seed<0 or args.count<1 or args.seed+args.count>=1000000:p.error('Use training-validation seeds only')
    result=[]
    for profile in ('tag','lag','passive'):
        aggregate={name:{k:[] for k in ('style_brier','style_correct','fold_brier')} for name in ('default','calibrated')}
        for seed in range(args.seed,args.seed+args.count):
            observer=Validator(profile,args.calibration)
            tournament([observer]+[ProfileStrategy(profile,seed*10+i) for i in range(8)],seed)
            for name in aggregate:
                for k in aggregate[name]:aggregate[name][k].extend(observer.rows[name][k])
        result.append(dict(profile=profile,models={name:{k:dict(n=len(values),mean=statistics.mean(values) if values else None) for k,values in rows.items()} for name,rows in aggregate.items()}))
    Path(args.output).write_text(json.dumps(dict(seed=args.seed,count=args.count,split='train-validation',rows=result,
        note='Prequential predictions before public events; repeated opportunities are correlated, not independent tournament evidence. No ROI tuning.'),indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
