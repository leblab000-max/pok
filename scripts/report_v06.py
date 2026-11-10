"""Paired seed-cluster inference for frozen v0.6 confirmation and ablations."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def interval(values,alpha=.05,repeats=10000):
    if len(values)<2:return None
    rng=random.Random(606);n=len(values)
    means=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(repeats))
    return [means[int(alpha/2*repeats)],means[min(repeats-1,int((1-alpha/2)*repeats))]]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default='reports/v06/confirm/results.json')
    p.add_argument('--out',default='reports/v06/confirm/STATISTICS.md')
    p.add_argument('--expected',type=int,default=1296)
    args=p.parse_args();data=json.loads(Path(args.results).read_text());rows=data['rows']
    if data['config']['split']!='test':raise ValueError('Confirmation report requires test data')
    source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path('poker_ai').glob('*.py')))).hexdigest()
    if source!=data['config']['source']:raise ValueError('Current source differs from confirmation source')
    if len(rows)!=args.expected:raise ValueError(f'Incomplete: {len(rows)} / {args.expected}')
    lookup={(r['strategy'],r['profile'],r['seed']):r['result'] for r in rows}
    profiles=sorted({r['profile'] for r in rows});names=sorted({r['strategy'] for r in rows});seeds=sorted({r['seed'] for r in rows})
    if len(lookup)!=len(rows):raise ValueError('Duplicate outcomes')
    if any((n,p,s) not in lookup for n in names for p in profiles for s in seeds):raise ValueError('Unbalanced study')
    for r in rows:
        v=r['result'];assert sum(v['final_stacks'].values())==9000
        assert sorted(v['places'].values())==list(range(1,10))
        assert abs(v['roi']-({1:450,2:270,3:180}.get(v['place'],0)-110)/110)<1e-12
    lines=['# v0.6 independent confirmation','',f'{len(rows)} unique tournaments; {len(seeds)} seed clusters; {len(profiles)} populations.',
           '', 'Intervals resample paired whole seed clusters with all populations kept together. No individual decision is treated as an independent tournament.',
           '', '| Profile | Policy | N | ROI % | ROI 95% bootstrap CI % | Chip/hand | Place | ITM % | Mean/P95 ms | Rollout calls/overrides |',
           '|---|---|---:|---:|---|---:|---:|---:|---|---|']
    for profile in profiles:
        for name in names:
            values=[lookup[name,profile,s] for s in seeds];roi=[v['roi'] for v in values];ci=interval(roi)
            timings=[t for v in values for t in v['decision_seconds']]
            lines.append(f"| {profile} | {name} | {len(values)} | {100*statistics.mean(roi):.1f} | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] | {statistics.mean(v['chip_per_hand'] for v in values):.2f} | {statistics.mean(v['place'] for v in values):.2f} | {100*statistics.mean(v['itm'] for v in values):.1f} | {1000*statistics.mean(timings):.2f}/{1000*sorted(timings)[int(.95*len(timings))]:.2f} | {sum(v['rollout_calls'] for v in values)}/{sum(v['rollout_overrides'] for v in values)} |")
    primary={};lines+=['','## Primary: equal-population average per seed','',
                       'Three predeclared reference comparisons; family alpha .05/3, 10000 bootstrap replicates. These are synthetic-population findings, not real-money profitability.',
                       '', '| Reference | Paired mean ROI gain pp | Adjusted bootstrap interval pp | Positive lower bound |',
                       '|---|---:|---|---|']
    for ref in ('math','advanced','adaptive'):
        differences=[statistics.mean(lookup['candidate',p,s]['roi']-lookup[ref,p,s]['roi'] for p in profiles) for s in seeds]
        ci=interval(differences,alpha=.05/3)
        primary[ref]=dict(mean=statistics.mean(differences),interval=ci,positive=ci[0]>0)
        lines.append(f"| {ref} | {100*statistics.mean(differences):.1f} | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] | {ci[0]>0} |")
    lines+=['','## Exploratory profile/ablation contrasts','',
            'All listed comparisons share family alpha .05/(5 × population count); no automatic promotion.',
            '', '| Profile | Reference | Mean candidate gain pp | Adjusted interval pp |','|---|---|---:|---|']
    contrasts={}
    for profile in profiles:
        contrasts[profile]={}
        for ref in ('math','advanced','adaptive','toggle_adapt','no_rollout'):
            differences=[lookup['candidate',profile,s]['roi']-lookup[ref,profile,s]['roi'] for s in seeds]
            ci=interval(differences,alpha=.05/(5*len(profiles)))
            contrasts[profile][ref]=dict(mean=statistics.mean(differences),interval=ci)
            lines.append(f"| {profile} | {ref} | {100*statistics.mean(differences):.1f} | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] |")
    lines+=['','## Limits','',
            'The candidate was selected on disjoint training seeds. Unknown families, calibration misspecification, determinization, small rollout sample counts and finite surrogate policies remain limitations. '
            'A low Monte Carlo regret or a positive interval here is not a GTO certificate. Ablations identical by construction must not be interpreted as separate independent algorithms. '
            'The experiment is balanced by seat and population; policy actions can change later random game trajectories even with the same seed.']
    Path(args.out).write_text('\n'.join(lines)+'\n')
    Path(args.out).with_suffix('.json').write_text(json.dumps(dict(primary=primary,profiles=contrasts,seed_clusters=len(seeds),tournaments=len(rows)),indent=2)+'\n')
    print(json.dumps(primary,indent=2))

if __name__=='__main__':main()
