"""Freeze one of three predeclared candidates using training data only."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default='reports/v06/train/results.json')
    p.add_argument('--output',default='reports/v06/selection.json')
    args=p.parse_args();data=json.loads(Path(args.results).read_text());rows=data['rows'];config=data['config']
    if config['split']!='train' or any(r['seed']>=1000000 for r in rows):raise ValueError('Training-only selection')
    source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path('poker_ai').glob('*.py')))).hexdigest()
    if source!=config['source']:raise ValueError('Source changed after training; rerun training before freezing')
    candidates={}
    for name in ('blend','lookahead','fixed'):
        subsets={p:[r for r in rows if r['strategy']==name and r['profile']==p] for p in ('tag','lag','passive')}
        if any(len(v)!=18 for v in subsets.values()):raise ValueError('Need 18 training seeds per candidate/profile')
        means={p:statistics.mean(r['result']['roi'] for r in subset) for p,subset in subsets.items()}
        # A fixed, predeclared robustness penalty discourages a single-profile spike.
        score=statistics.mean(means.values())-.25*statistics.pstdev(means.values())
        candidates[name]=dict(profile_roi=means,score=score)
    chosen=max(candidates,key=lambda name:candidates[name]['score'])
    result=dict(version='0.6',split='train',source=source,selected=chosen,candidates=candidates,
                training_seeds=[min(r['seed'] for r in rows),max(r['seed'] for r in rows)],
                samples=config['samples'],calibration=config['calibration'],
                rule='Equal-profile mean ROI minus .25 * profile-mean population SD; candidates fixed before viewing training scores.')
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
