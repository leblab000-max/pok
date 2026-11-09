"""Independent, larger-sample decision screening; outcomes are not error evidence."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import statistics
from .adaptive import AdaptiveTournamentStrategy
from .strategy import Observation,Decision


class DecisionAnalyzer:
    def __init__(self,samples: int=128,seed: int=9173,threshold_bb: float=.5):
        if samples<2 or threshold_bb<0:raise ValueError('Invalid audit configuration')
        self.samples=samples;self.seed=seed;self.threshold_bb=threshold_bb

    def analyze(self,o: Observation,chosen: Decision,context: dict | None=None) -> dict:
        # This seed depends only on public observation + hero cards, never the hand outcome.
        public=json.dumps(asdict(o),sort_keys=True)
        seed=int.from_bytes(hashlib.sha256((str(self.seed)+public).encode()).digest()[:8],'big')
        evaluator=AdaptiveTournamentStrategy(seed,self.samples)
        context=context or {}
        evaluator.frozen_weights={int(s):w for s,w in context.get('profile_weights',{}).items()}
        evaluator.frozen_stats={int(s):w for s,w in context.get('opponent_stats',{}).items()}
        result=evaluator.evaluate(o,extra_decisions=(chosen,))
        metric=result['metric'];alternatives=result['alternatives']
        index=next(i for i,r in enumerate(alternatives) if r['action']==chosen.action and r['raise_to']==chosen.raise_to)
        best=max(range(len(alternatives)),key=lambda i:alternatives[i][metric])
        regret=alternatives[best][metric]-alternatives[index][metric]
        se=result['paired_standard_errors'][f'{best}:{index}']
        z=statistics.NormalDist().inv_cdf(1-.05/(2*len(alternatives)))
        threshold=self.threshold_bb*o.big_blind if metric=='chip_ev' else .005*sum(o.payouts)
        low=regret-z*se
        depth=o.stack/o.big_blind
        position=o.position/max(1,o.tournament_players-1)
        return dict(observation=asdict(o),chosen=asdict(chosen),alternatives=alternatives,
                    metric=metric,model_regret=regret,paired_se=se,screening_lower_bound=low,
                    threshold=threshold,potentially_costly=low>threshold,audit_samples=2*self.samples,
                    groups=dict(position='early' if position<1/3 else 'middle' if position<2/3 else 'late',
                                depth='short' if depth<10 else 'medium' if depth<30 else 'deep',
                                street={0:'preflop',3:'flop',4:'turn',5:'river'}[len(o.board)],
                                profile=','.join(sorted(set(result['profiles'].values())))),
                    note='Model-relative, selection-adjusted sampling screen. Range/response model uncertainty and future betting omitted; not proven poker mistakes.')

    @staticmethod
    def markdown(records: list[dict]) -> str:
        lines=['# DecisionAnalyzer report','',
               'Independent seeds and larger sample counts. No realized winnings/losses are used to label mistakes.',
               'Rates refer to the deterministically audited subset. Statistical screening controls alternatives within a decision, not all decisions.',
               '', '| Dimension | Group | Audited | Flagged | Rate % | Mean model regret |',
               '|---|---|---:|---:|---:|---:|']
        grouped=defaultdict(list)
        for record in records:
            for dimension,group in record['groups'].items():grouped[dimension,group].append(record)
        for (dimension,group),rows in sorted(grouped.items()):
            flags=sum(r['potentially_costly'] for r in rows)
            # Chip and money utility are never averaged together.
            for metric in sorted(set(r['metric'] for r in rows)):
                subset=[r for r in rows if r['metric']==metric]
                n=sum(r['potentially_costly'] for r in subset)
                lines.append(f"| {dimension} | {group} ({metric}) | {len(subset)} | {n} | {100*n/len(subset):.1f} | {statistics.mean(r['model_regret'] for r in subset):.3f} |")
        lines += ['', '## Highest standardized screening margins','']
        ranked=sorted(records,key=lambda r:(r['screening_lower_bound']-r['threshold'])/max(1e-12,r['threshold']),reverse=True)[:10]
        for r in ranked:
            lines.append(f"- Hand {r['observation']['hand_id']}, {r['groups']}, chosen `{r['chosen']}`: modeled regret {r['model_regret']:.3f} {r['metric']}, SE {r['paired_se']:.3f}, lower bound {r['screening_lower_bound']:.3f}.")
        return '\n'.join(lines)+'\n'
