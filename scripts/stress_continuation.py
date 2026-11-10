"""Replay random real hand checkpoints under a stateless legal policy.

This checks rule/state fidelity, not strategy strength. The oracle gets its deck
from the real engine seed; acting policies never receive future cards.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import random
from poker_ai.cards import deck,evaluate_seven
from poker_ai.continuation import continuation
from poker_ai.engine import play_hand
from poker_ai.sampling import JointDeal
from poker_ai.strategy import Decision


class ReplayPolicy:
    def decide(self,o):
        if o.minimum_raise_to is not None and (ord(o.hole_cards[0][0])+o.seat)%4==0:
            return Decision('raise',o.minimum_raise_to)
        if o.to_call>5*o.big_blind and ord(o.hole_cards[1][0])%3==0:return Decision('fold')
        return Decision('call' if o.to_call else 'check')


def main():
    rng=random.Random(60603);passed=attempts=0
    while passed<1000:
        attempts+=1;n=rng.randint(2,9);seats=list(range(n));rng.shuffle(seats)
        stacks={s:rng.randint(1,1000) for s in seats};button=rng.randrange(n);seed=rng.randrange(2**32)
        blind=rng.choice((2,10,20,100));ante=rng.choice((0,1,5));observed=[]
        players={s:ReplayPolicy() for s in seats}
        def sink(o,d,t,a):observed.append((o,d))
        actual=play_hand(stacks,button,players,random.Random(seed),blind,ante,decision_sink=sink)
        if not observed:continue
        o,d=rng.choice(observed)
        order=sorted(seats);order=order[order.index(button)+1:]+order[:order.index(button)+1]
        cards=deck();random.Random(seed).shuffle(cards);holes={s:[] for s in seats}
        for _ in range(2):
            for s in order:holes[s].append(cards.pop())
        board=[]
        for count in (3,1,1):cards.pop();board.extend(cards.pop() for _ in range(count))
        opponents=[s for s in sorted(stacks) if s!=o.seat and s not in o.folded]
        deal=JointDeal(tuple(tuple(holes[s]) for s in opponents),tuple(board),
                       tuple(evaluate_seven(holes[s]+board) for s in [o.seat]+opponents),tuple(.5 for _ in opponents))
        simulated=continuation(o,d,deal,{},seed,policies=players,max_actions=4096)
        assert actual.stacks==simulated.stacks,(seed,stacks,o,actual,simulated)
        passed+=1
    print(f'PASS: {passed} random checkpoints exactly match direct engine final stacks; seed=60603')

if __name__=='__main__':main()
