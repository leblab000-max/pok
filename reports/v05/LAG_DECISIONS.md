# Actual LAG population: decision groups

# DecisionAnalyzer report

Independent seeds and larger sample counts. No realized winnings/losses are used to label mistakes.
Rates refer to the deterministically audited subset. Statistical screening controls alternatives within a decision, not all decisions.

| Dimension | Group | Audited | Flagged | Rate % | Mean model regret |
|---|---|---:|---:|---:|---:|
| depth | deep (chip_ev) | 701 | 66 | 9.4 | 27.345 |
| depth | deep (money_ev) | 5 | 0 | 0.0 | 0.000 |
| depth | medium (chip_ev) | 148 | 38 | 25.7 | 91.818 |
| depth | medium (money_ev) | 3 | 1 | 33.3 | 6.206 |
| depth | short (chip_ev) | 48 | 13 | 27.1 | 96.955 |
| depth | short (money_ev) | 7 | 1 | 14.3 | 5.319 |
| position | early (chip_ev) | 360 | 51 | 14.2 | 49.674 |
| position | early (money_ev) | 7 | 0 | 0.0 | 0.000 |
| position | late (chip_ev) | 311 | 44 | 14.1 | 44.549 |
| position | late (money_ev) | 6 | 1 | 16.7 | 3.303 |
| position | middle (chip_ev) | 226 | 22 | 9.7 | 25.107 |
| position | middle (money_ev) | 2 | 1 | 50.0 | 18.020 |
| profile | lag (chip_ev) | 2 | 0 | 0.0 | 0.000 |
| profile | passive (chip_ev) | 1 | 0 | 0.0 | 0.000 |
| profile | tag (chip_ev) | 894 | 117 | 13.1 | 41.848 |
| profile | tag (money_ev) | 15 | 2 | 13.3 | 3.724 |
| street | flop (chip_ev) | 86 | 29 | 33.7 | 68.853 |
| street | flop (money_ev) | 2 | 0 | 0.0 | 0.000 |
| street | preflop (chip_ev) | 619 | 18 | 2.9 | 15.613 |
| street | preflop (money_ev) | 7 | 0 | 0.0 | 0.171 |
| street | river (chip_ev) | 101 | 38 | 37.6 | 111.930 |
| street | river (money_ev) | 3 | 1 | 33.3 | 12.013 |
| street | turn (chip_ev) | 91 | 32 | 35.2 | 115.614 |
| street | turn (money_ev) | 3 | 1 | 33.3 | 6.206 |

## Highest standardized screening margins

- Hand 3, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 1429.312 chip_ev, SE 83.880, lower bound 1228.505.
- Hand 3, {'position': 'late', 'depth': 'deep', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 480}`: modeled regret 505.891 chip_ev, SE 14.028, lower bound 470.852.
- Hand 16, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 981.922 chip_ev, SE 77.521, lower bound 796.338.
- Hand 13, {'position': 'middle', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 40}`: modeled regret 678.859 chip_ev, SE 38.005, lower bound 587.875.
- Hand 15, {'position': 'late', 'depth': 'deep', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'call', 'raise_to': None}`: modeled regret 550.906 chip_ev, SE 25.798, lower bound 486.470.
- Hand 7, {'position': 'late', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'call', 'raise_to': None}`: modeled regret 301.375 chip_ev, SE 47.675, lower bound 182.297.
- Hand 12, {'position': 'middle', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 360}`: modeled regret 406.000 chip_ev, SE 30.319, lower bound 330.273.
- Hand 8, {'position': 'early', 'depth': 'deep', 'street': 'flop', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 180.797 chip_ev, SE 11.106, lower bound 154.210.
- Hand 14, {'position': 'early', 'depth': 'medium', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 1588}`: modeled regret 322.805 chip_ev, SE 7.654, lower bound 303.687.
- Hand 26, {'position': 'early', 'depth': 'short', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 240}`: modeled regret 590.781 chip_ev, SE 24.486, lower bound 529.623.
