"""Idempotently copy completed benchmark transactions from an independent shard.

No source data are deleted. Run after the shard writer stops. Unique experiment,
policy, opponent, seed and seat keys prevent duplicate tournament/audit insertion.
"""
import argparse
from poker_ai.benchmark import connect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('target');p.add_argument('shard')
    args=p.parse_args();copied=skipped=0
    with connect(args.target) as db:
        db.execute('ATTACH DATABASE ? AS shard',(args.shard,))
        rows=db.execute('SELECT id,config,strategy,profile,seed,seat,result FROM shard.benchmark_runs ORDER BY id').fetchall()
        for old_id,config,strategy,profile,seed,seat,result in rows:
            existing=db.execute('SELECT id FROM benchmark_runs WHERE config=? AND strategy=? AND profile=? AND seed=? AND seat=?',
                                (config,strategy,profile,seed,seat)).fetchone()
            if existing:skipped+=1;continue
            cursor=db.execute('INSERT INTO benchmark_runs(config,strategy,profile,seed,seat,result) VALUES (?,?,?,?,?,?)',
                              (config,strategy,profile,seed,seat,result))
            traces=db.execute('SELECT risk,payload FROM shard.decision_traces WHERE run_id=? ORDER BY id',(old_id,)).fetchall()
            db.executemany('INSERT INTO decision_traces(run_id,risk,payload) VALUES (?,?,?)',[(cursor.lastrowid,risk,payload) for risk,payload in traces])
            db.commit();copied+=1
    print(dict(copied=copied,skipped=skipped))

if __name__=='__main__':main()
