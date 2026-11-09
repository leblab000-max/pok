"""10,000 independent seeded hands with varied stacks, seats and legal actions."""
import random
from poker_ai.engine import play_hand
from poker_ai.strategy import Decision

class RandomStrategy:
    def __init__(self,rng): self.rng=rng
    def decide(self,o):
        actions=[Decision('fold'),Decision('call' if o.to_call else 'check')]
        if o.minimum_raise_to is not None:
            actions += [Decision('raise',o.minimum_raise_to),Decision('raise',o.maximum_raise_to)]
        return self.rng.choice(actions)

def main():
    rng=random.Random(20261109)
    for i in range(10000):
        n=rng.randint(2,9); stacks={s:rng.randint(1,2000) for s in range(n)}
        result=play_hand(stacks,rng.randrange(n),{s:RandomStrategy(rng) for s in stacks},rng,rng.choice([2,20,100,1000]),rng.choice([0,1,10]))
        assert sum(result.stacks.values())==sum(stacks.values())
    print('PASS: 10000 hands; seed=20261109; chip conservation and decision validation')
if __name__=='__main__': main()
