"""Decision traces and model-relative review; outcomes are never error labels."""
from dataclasses import asdict
import json
import sqlite3
from .strategy import Observation, Decision


def trace(o: Observation, decision: Decision, elapsed: float, analysis: dict) -> dict:
    alternatives = analysis.get('alternatives',[])
    metric = analysis.get('metric','chip_ev')
    chosen = next((r for r in alternatives if r['action']==decision.action and r['raise_to']==decision.raise_to),None)
    valid = [r[metric] for r in alternatives if r.get(metric) is not None]
    regret = max(valid)-chosen[metric] if valid and chosen is not None and chosen.get(metric) is not None else None
    estimates = [abs(r.get('chip_ev',0)) for r in alternatives]
    return dict(observation=asdict(o),decision=asdict(decision),elapsed=elapsed,analysis=analysis,
                model_regret=regret,estimated_swing=max(estimates,default=0),
                warning='Model-relative screening only; no realized hand outcome used.')


def analyze_alternative_decision(o: Observation, decision: Decision, evaluator) -> dict:
    """Offline audit of any policy against a supplied independent decision model.

    This does not claim the evaluator is ground truth. No observed outcome enters EV.
    """
    from .strategy import validate_decision
    validate_decision(o,decision)
    analysis = evaluator.evaluate(o)
    return trace(o,decision,0.0,analysis)


def review(db_path: str, limit: int = 10, *, config: str | None = None,
           seed_range: tuple[int,int] | None = None) -> str:
    with sqlite3.connect(db_path) as db:
        where = []; parameters = []
        if config is not None: where.append('b.config=?'); parameters.append(config)
        if seed_range is not None:
            where.extend(['b.seed>=?','b.seed<?']); parameters.extend(seed_range)
        condition = ' AND '.join(where) if where else '1=1'
        rows=db.execute('SELECT t.run_id,t.payload FROM decision_traces t JOIN benchmark_runs b ON b.id=t.run_id WHERE '+condition+' ORDER BY t.risk DESC,t.id LIMIT ?',parameters+[limit]).fetchall()
    lines=['# Decision review','',
           'Ranked by estimated alternative chip-EV swing. These are uncertain model estimates, not proven mistakes.',
           'Baseline traces have no counterfactual model. Selected v2 actions maximize their own model, so regret alone cannot validate them.',
           '', '| Run | Hand | Board | Cards | Decision | Model regret | Estimated swing | Equity SE |',
           '|---|---:|---|---|---|---:|---:|---:|']
    for run_id,payload in rows:
        data=json.loads(payload); o=data['observation']; a=data['analysis']
        lines.append(f"| {run_id} | {o['hand_id']} | {' '.join(o['board'])} | {' '.join(o['hole_cards'])} | {data['decision']} | {data['model_regret']} | {data['estimated_swing']:.2f} | {a.get('equity',{}).get('standard_error','n/a')} |")
    return '\n'.join(lines)+'\n'
