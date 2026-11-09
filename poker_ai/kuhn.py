"""Chance-sampled CFR on Kuhn Poker; exact 64-policy best-response checks.

Two players ante one; cards J,Q,K; one bet of one; p=check/fold, b=bet/call.
Known equilibrium value to player zero is -1/18. No Hold'em training claim.
"""
import argparse
from dataclasses import dataclass, field
from itertools import permutations, product
import json
import random

DEALS = tuple(permutations(range(3),2))


def terminal(cards: tuple[int,int], history: str) -> float | None:
    if history == 'bp': return 1.0
    if history == 'pbp': return -1.0
    if history in ('pp','bb','pbb'):
        return (1 if cards[0]>cards[1] else -1)*(1 if history=='pp' else 2)
    return None


@dataclass
class Node:
    regrets: list[float] = field(default_factory=lambda:[0.0,0.0])
    totals: list[float] = field(default_factory=lambda:[0.0,0.0])

    def policy(self) -> list[float]:
        positive = [max(0,r) for r in self.regrets]
        total = sum(positive)
        return [r/total for r in positive] if total else [.5,.5]

    def average(self) -> list[float]:
        total = sum(self.totals)
        return [t/total for t in self.totals] if total else [.5,.5]


def train(iterations: int = 100000, seed: int = 1) -> dict[str,list[float]]:
    if iterations<1: raise ValueError('Positive iteration count required')
    rng = random.Random(seed)
    nodes: dict[str,Node] = {str(card)+history:Node() for card in range(3) for history in ('','p','b','pb')}
    def cfr(cards: tuple[int,int], history: str, reach: tuple[float,float]) -> float:
        value = terminal(cards,history)
        player = len(history)%2
        if value is not None: return value if player==0 else -value
        key = str(cards[player])+history
        node = nodes.setdefault(key,Node()); policy=node.policy()
        utility=[]
        for action in range(2):
            next_reach=list(reach); next_reach[player] *= policy[action]
            utility.append(-cfr(cards,history+'pb'[action],tuple(next_reach)))
        expected=sum(p*u for p,u in zip(policy,utility))
        for action in range(2):
            node.regrets[action] += reach[1-player]*(utility[action]-expected)
            node.totals[action] += reach[player]*policy[action]
        return expected
    for _ in range(iterations): cfr(rng.choice(DEALS),'',(1.0,1.0))
    return {key:node.average() for key,node in sorted(nodes.items())}


def value(policy: dict[str,list[float]], overrides: dict[str,list[float]] | None = None) -> float:
    overrides = overrides or {}
    def visit(cards: tuple[int,int], history: str) -> float:
        result = terminal(cards,history)
        if result is not None: return result
        player=len(history)%2; key=str(cards[player])+history
        choices=overrides.get(key,policy[key])
        return sum(choices[a]*visit(cards,history+'pb'[a]) for a in range(2))
    return sum(visit(cards,'') for cards in DEALS)/6


def evaluate(policy: dict[str,list[float]]) -> dict:
    best=[]
    for player,histories in [(0,('', 'pb')),(1,('p','b'))]:
        keys=[str(card)+h for card in range(3) for h in histories]
        values=[]
        for actions in product(range(2),repeat=6):
            override={key:([1.0,0.0] if a==0 else [0.0,1.0]) for key,a in zip(keys,actions)}
            values.append(value(policy,override))
        best.append(max(values) if player==0 else min(values))
    result=value(policy)
    return dict(value=result,theoretical_value=-1/18,value_error=abs(result+1/18),
                exploitability=(best[0]-best[1])/2,best_response_values=best,policy=policy,
                method='Chance-sampled CFR; full action traversal; exact pure-policy best responses')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iterations',type=int,default=100000)
    p.add_argument('--seed',type=int,default=1)
    args=p.parse_args()
    result=evaluate(train(args.iterations,args.seed))
    result.update(iterations=args.iterations,seed=args.seed)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
