"""Compact evidence summary and explicitly secondary pooled ablations."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib
import json
import sqlite3
import statistics
from scripts.report_v06 import interval


def main():
    root=Path('reports/v06');data=json.loads((root/'confirm/results.json').read_text());rows=data['rows']
    source=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(Path('poker_ai').glob('*.py')))).hexdigest()
    if source!=data['config']['source'] or len(rows)!=1296:raise ValueError('Incomplete or stale confirmation')
    profiles=('tag','lag','passive');names=('math','advanced','adaptive','candidate','toggle_adapt','no_rollout')
    lookup={(r['strategy'],r['profile'],r['seed']):r['result'] for r in rows};seeds=sorted({r['seed'] for r in rows})
    lines=['# v0.6 measured summary','', 'Frozen training winner: fixed mixture + full-hand continuation gate. Cross-hand style adaptation disabled; current-hand range inference remains active.',
           '', '| Policy | Tournaments | ROI TAG % | ROI LAG % | ROI Passive % | Equal-mixture ROI % | Mean/P95 ms |',
           '|---|---:|---:|---:|---:|---:|---|']
    for name in names:
        subset=[r['result'] for r in rows if r['strategy']==name]
        means=[statistics.mean(lookup[name,p,s]['roi'] for s in seeds) for p in profiles]
        times=[t for v in subset for t in v['decision_seconds']]
        lines.append(f"| {name} | {len(subset)} | {100*means[0]:.1f} | {100*means[1]:.1f} | {100*means[2]:.1f} | {100*statistics.mean(means):.1f} | {1000*statistics.mean(times):.2f}/{1000*sorted(times)[int(.95*len(times))]:.2f} |")
    primary=json.loads((root/'confirm/STATISTICS.json').read_text())['primary']
    lines+=['','## Predeclared primary comparisons','', 'Gain is candidate minus reference in ROI percentage points; intervals adjust three paired seed-cluster comparisons.','',
            '| Reference | Gain pp | Adjusted bootstrap interval pp |','|---|---:|---|']
    for name in ('math','advanced','adaptive'):
        v=primary[name];lines.append(f"| {name} | {100*v['mean']:.1f} | [{100*v['interval'][0]:.1f}, {100*v['interval'][1]:.1f}] |")
    fixed=[r['result'] for r in rows if r['strategy']=='candidate']
    calls=sum(r['rollout_calls'] for r in fixed);overrides=sum(r['rollout_overrides'] for r in fixed)
    model_actions=sum(r['simulated_raises'] for r in fixed);future=sum(r['future_streets'] for r in fixed)
    lines+=['',f'Candidate continuation calls: {calls}; actual root overrides: {overrides}; simulated raises: {model_actions}; future-street advances: {future}.',
            '', 'Supported improvement is restricted to this predeclared synthetic mixture. Advanced remains stronger against TAG. '
            'On mixed/pressure diagnostics, superiority over Mathematical is not established. '
            'No-rollout is identical to Mathematical by construction and was independently replayed, not treated as an extra independent algorithm.',
            '',f'Source SHA256: `{source}`.','The source/selection are frozen. No post-holdout parameter changes or automatic promotion.']
    (root/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    for p in profiles:
        for s in seeds:
            a=lookup['math',p,s];b=lookup['no_rollout',p,s]
            for key in ('place','itm','roi','chip_per_hand','hands','places','final_stacks'):
                if a[key]!=b[key]:raise ValueError('No-rollout ablation differs unexpectedly from Mathematical')
    ablations=['# Secondary pooled ablations','',
               'Equal-profile differences averaged within each of 72 seed clusters. These are exploratory, not additional primary claims. '
               'Two contrasts, Bonferroni alpha=.05/2, 10000 replicates. No model is reselected from this report.',
               '', '| Contrast | Mean ROI difference pp | Adjusted interval pp |','|---|---:|---|']
    results={}
    for name,left,right in [('adaptation on minus off','toggle_adapt','candidate'),('continuation on minus off','candidate','no_rollout')]:
        values=[statistics.mean(lookup[left,p,s]['roi']-lookup[right,p,s]['roi'] for p in profiles) for s in seeds]
        ci=interval(values,alpha=.05/2)
        results[name]=dict(mean=statistics.mean(values),interval=ci)
        ablations.append(f"| {name} | {100*statistics.mean(values):.1f} | [{100*ci[0]:.1f}, {100*ci[1]:.1f}] |")
    ablations+=['','The selected fixed candidate uses Mathematical as its base. Consequently no_rollout exactly matches Mathematical on all 216 shared policy/population/seed scenarios. '
                'This verifies the intervention but does not create a new independent baseline. '
                'Normal within-decision rollout bounds at eight samples cover neither model misspecification nor all selection effects. Tournament outcomes are the confirmation evidence.']
    (root/'ABLATION.md').write_text('\n'.join(ablations)+'\n');(root/'ABLATION.json').write_text(json.dumps(results,indent=2)+'\n')
    with sqlite3.connect('v06-confirm.sqlite') as db:
        integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('DB integrity failure')
    print(json.dumps(dict(ablations=results,continuation_calls=calls,overrides=overrides,sqlite=integrity),indent=2))

if __name__=='__main__':main()
