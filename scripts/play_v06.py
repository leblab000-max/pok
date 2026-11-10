"""One-command launch of the frozen research candidate (Python 3.12)."""
from pathlib import Path
import os
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root));os.chdir(root)
from poker_ai.league import main

if __name__=='__main__':
    extra=sys.argv[1:]
    sys.argv=[sys.argv[0],'--split','train','--seed','42','--count','1','--profiles','mixed',
              '--policies','candidate','--selection','reports/v06/selection.json',
              '--db','local-candidate.sqlite','--out','runs/local','--seconds','120']+extra
    main()
