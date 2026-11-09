"""Summarize a completed/partial v0.5 experiment without altering any strategy."""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
from poker_ai.decision_analyzer import DecisionAnalyzer


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='v05-benchmark.sqlite');p.add_argument('--out',default='reports/v05')
    args=p.parse_args();out=Path(args.out);data=json.loads((out/'results.json').read_text())
    source=hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path('poker_ai').glob('*.py')))).hexdigest()
    if source!=data['config']['source']:raise ValueError('Current source differs from reported experiment')
    rows=data['rows'];identity=json.dumps(data['config'],sort_keys=True)
    seeds=[r['seed'] for r in rows]
    if not seeds:raise ValueError('No completed data to summarize')
    lines=['# v0.5 measured summary','',f"Completed tournaments: {len(rows)}. Seeds: {min(seeds)}–{max(seeds)}.",'',
           '| Policy | N | ROI TAG % | ROI LAG % | ROI Passive % | Mean decision ms | P95 ms | Audited | Model-flagged % |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in ('call','math','advanced','adaptive'):
        subset=[r for r in rows if r['strategy']==name]
        times=[t for r in subset for t in r['result']['decision_seconds']]
        rois=[100*statistics.mean(r['result']['roi'] for r in subset if r['profile']==profile) for profile in ('tag','lag','passive')]
        audited=sum(r['result']['audited'] for r in subset);flagged=sum(r['result']['flagged'] for r in subset)
        lines.append(f"| {name} | {len(subset)} | {rois[0]:.1f} | {rois[1]:.1f} | {rois[2]:.1f} | {1000*statistics.mean(times):.2f} | {1000*sorted(times)[int(.95*len(times))]:.2f} | {audited} | {100*flagged/max(1,audited):.1f} |")
    lines+=['','Intervals, paired comparisons and limits are in BENCHMARK.md; LAG-specific tables are in LAG.md. '
            'Model flags are independent-sample screening disagreements, not proven mistakes or true game-theoretic regret. '
            'No general superiority or real-money profitability follows from artificial populations.','']
    before=out/'profile-before.json';after=out/'profile-after.json'
    if before.exists() and after.exists():
        b=json.loads(before.read_text());a=json.loads(after.read_text())
        equal=a['analyses']==b['analyses']
        lines+=['## Frozen-spot performance','',
                f"48 fixed public spots, 32 equity samples, 3 timing passes. Before mean/P95: {b['mean_ms']:.3f}/{b['p95_ms']:.3f} ms; after: {a['mean_ms']:.3f}/{a['p95_ms']:.3f} ms.",
                f"Mean reduction: {100*(1-a['mean_ms']/b['mean_ms']):.1f}%. Full numeric diagnostics identical: {equal}.",
                'This repeatable cache workload is distinct from live-tournament latency; neither guarantees VPS timing.','']
        if not equal:raise ValueError('Optimization changed frozen numeric results')
    (out/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    audits=[]
    with sqlite3.connect(args.db) as db:
        for (payload,) in db.execute('SELECT t.payload FROM decision_traces t JOIN benchmark_runs b ON b.id=t.run_id WHERE b.config=? AND b.profile=? AND b.seed>=? AND b.seed<=? ORDER BY t.id',(identity,'lag',min(seeds),max(seeds))):
            row=json.loads(payload)
            if 'independent_audit' in row:audits.append(row['independent_audit'])
        diagnostics=defaultdict(lambda:dict(contexts=0,ready=0,correct=0))
        seen=set();responses=defaultdict(lambda:[0,0])
        for run_id,policy,profile,hero,payload in db.execute(
                'SELECT b.id,b.strategy,b.profile,b.seat,t.payload FROM decision_traces t JOIN benchmark_runs b ON b.id=t.run_id WHERE b.config=? AND b.seed>=? AND b.seed<=? ORDER BY t.id',
                (identity,min(seeds),max(seeds))):
            record=json.loads(payload);context=record['analysis']
            if policy=='adaptive':
                for seat,stats in context.get('opponent_stats',{}).items():
                    row=diagnostics[profile];row['contexts']+=1
                    if stats['ready']:
                        row['ready']+=1
                        weights=context['profile_weights'][seat]
                        row['correct']+=max(weights,key=weights.get)==profile
            for event in record['observation']['public_actions']:
                key=(run_id,event['hand_id'],event['action_id'])
                if key in seen or event['seat']==hero:continue
                seen.add(key)
                if event['raises_before']>=1 and event['to_call']>0:
                    responses[profile][1]+=1;responses[profile][0]+=event['action']=='raise'
        diag_lines=['# Public opponent diagnostics','',
                    'Snapshot counts are correlated and selected by survival; these are descriptive diagnostics, not independent classification trials.',
                    'True synthetic profile labels are used only for evaluation, never as playing-strategy input.','',
                    '| Actual profile | Opponent contexts | Ready contexts % | Classification correct among ready % | Observed wager responses | Raise responses % |',
                    '|---|---:|---:|---:|---:|---:|']
        for profile in ('tag','lag','passive'):
            row=diagnostics[profile];raises,n=responses[profile]
            diag_lines.append(f"| {profile} | {row['contexts']} | {100*row['ready']/max(1,row['contexts']):.1f} | {100*row['correct']/max(1,row['ready']):.1f} | {n} | {100*raises/max(1,n):.1f} |")
        diag_lines += ['','Observed wager responses are deduplicated public events present in stored snapshots, not a complete census. '
                       'They include opponents responding to each other. Raise responses are branches omitted by the current fold/call EV model. '
                       'Low ready-context coverage limits any claim that strategy performance comes from learned adaptation.']
        (out/'OPPONENT_DIAGNOSTICS.md').write_text('\n'.join(diag_lines)+'\n')
        integrity=db.execute('PRAGMA quick_check').fetchone()[0]
    (out/'LAG_DECISIONS.md').write_text('# Actual LAG population: decision groups\n\n'+DecisionAnalyzer.markdown(audits))
    print(json.dumps(dict(tournaments=len(rows),lag_audits=len(audits),sqlite_quick_check=integrity)))

if __name__=='__main__':main()
