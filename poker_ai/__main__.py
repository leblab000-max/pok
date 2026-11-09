"""Offline tournament experiments with transactional, resumable SQLite results."""
import hashlib
from pathlib import Path
import argparse
import json
import math
import sqlite3
import statistics
from dataclasses import asdict
from .engine import tournament
from .advanced import AdvancedTournamentStrategy
from .adaptive import AdaptiveTournamentStrategy
from .strategy import CallingBaseline, ConservativeBaseline, MathematicalBaseline


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tournaments', type=int, default=1)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--db', default='results.sqlite')
    p.add_argument('--strategy', choices=['math','call','fold','advanced','adaptive'], default='math')
    p.add_argument('--samples', type=int, default=24)
    p.add_argument('--calibration',default=None)
    p.add_argument('--buy-in', type=float, default=100)
    p.add_argument('--fee', type=float, default=10)
    args = p.parse_args()
    if args.tournaments < 1 or args.samples < 2 or args.buy_in <= 0 or args.fee < 0: p.error('Invalid experiment parameters')
    source_hash = hashlib.sha256(b''.join(f.read_bytes() for f in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    config = json.dumps(dict(source_hash=source_hash,strategy=args.strategy,samples=args.samples,buy_in=args.buy_in,fee=args.fee,calibration_hash=hashlib.sha256(Path(args.calibration).read_bytes()).hexdigest() if args.calibration else None,version=3),sort_keys=True)
    with sqlite3.connect(args.db) as db:
        db.execute('CREATE TABLE IF NOT EXISTS tournaments (config TEXT, seed INTEGER, result TEXT, PRIMARY KEY(config,seed))')
        for seed in range(args.seed, args.seed+args.tournaments):
            if db.execute('SELECT 1 FROM tournaments WHERE config=? AND seed=?',(config,seed)).fetchone(): continue
            hero = {'adaptive':lambda:AdaptiveTournamentStrategy(seed,args.samples,calibration=args.calibration),'advanced':lambda:AdvancedTournamentStrategy(seed,args.samples),'math':lambda:MathematicalBaseline(seed,args.samples), 'call':CallingBaseline,'fold':ConservativeBaseline}[args.strategy]()
            opponents = [CallingBaseline() if i%2 else ConservativeBaseline() for i in range(8)]
            # Rotate hero seat to reduce position/seat assignment bias.
            seat = seed%9; players = opponents[:]; players.insert(seat,hero)
            r = tournament(players,seed,payouts=(.5*9*args.buy_in,.3*9*args.buy_in,.2*9*args.buy_in))
            data = asdict(r); data['hero_seat'] = seat
            db.execute('INSERT INTO tournaments VALUES (?,?,?)',(config,seed,json.dumps(data)))
            db.commit()  # completed tournament is atomic; restart skips it
        rows = [json.loads(r[0]) for r in db.execute('SELECT result FROM tournaments WHERE config=? AND seed>=? AND seed<? ORDER BY seed',(config,args.seed,args.seed+args.tournaments))]
    places = [r['places'][str(r['hero_seat'])] for r in rows]
    payouts = [.5,.3,.2]
    profits = [(payouts[place-1]*9*args.buy_in if place<=3 else 0)-args.buy_in-args.fee for place in places]
    mean = statistics.mean(profits)
    interval = None if len(profits)<2 else 1.96*statistics.stdev(profits)/math.sqrt(len(profits))
    balance = peak = drawdown = 0.0
    for profit in profits:
        balance += profit; peak=max(peak,balance); drawdown=max(drawdown,peak-balance)
    telemetry = {}
    for r in rows:
        for key, row in r['telemetry'].items():
            seat, position, bucket = key.split(':')
            if int(seat) != r['hero_seat']: continue
            dest = telemetry.setdefault(position+':'+bucket, {'hands':0,'chip_delta':0})
            for metric in dest: dest[metric] += row[metric]
    print(json.dumps(dict(tournaments=len(rows),hands=sum(r['hands'] for r in rows),average_place=statistics.mean(places),
                         itm=sum(p<=3 for p in places)/len(places),roi=mean/(args.buy_in+args.fee),
                         mean_profit=mean,mean_profit_approx_95_ci=None if interval is None else [mean-interval,mean+interval],
                         maximum_drawdown=drawdown,chip_ev_per_hand=sum(v["chip_delta"] for v in telemetry.values())/max(1,sum(v["hands"] for v in telemetry.values())),by_position_stack=telemetry, warning='Exploratory normal CI; no evidence of profitability claimed.'),indent=2))

if __name__ == '__main__': main()
