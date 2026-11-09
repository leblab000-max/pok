# DecisionAnalyzer report

Independent seeds and larger sample counts. No realized winnings/losses are used to label mistakes.
Rates refer to the deterministically audited subset. Statistical screening controls alternatives within a decision, not all decisions.

| Dimension | Group | Audited | Flagged | Rate % | Mean model regret |
|---|---|---:|---:|---:|---:|
| depth | deep (chip_ev) | 2154 | 204 | 9.5 | 23.125 |
| depth | deep (money_ev) | 8 | 0 | 0.0 | 0.000 |
| depth | medium (chip_ev) | 819 | 147 | 17.9 | 68.432 |
| depth | medium (money_ev) | 14 | 1 | 7.1 | 1.465 |
| depth | short (chip_ev) | 400 | 83 | 20.8 | 138.463 |
| depth | short (money_ev) | 15 | 1 | 6.7 | 2.482 |
| position | early (chip_ev) | 1258 | 150 | 11.9 | 51.399 |
| position | early (money_ev) | 13 | 0 | 0.0 | 0.000 |
| position | late (chip_ev) | 1190 | 166 | 13.9 | 54.399 |
| position | late (money_ev) | 16 | 1 | 6.2 | 1.238 |
| position | middle (chip_ev) | 925 | 118 | 12.8 | 34.429 |
| position | middle (money_ev) | 8 | 1 | 12.5 | 4.741 |
| profile | lag (chip_ev) | 2 | 0 | 0.0 | 0.000 |
| profile | passive (chip_ev) | 8 | 0 | 0.0 | 1.590 |
| profile | passive (money_ev) | 3 | 0 | 0.0 | 0.000 |
| profile | passive,tag (chip_ev) | 3 | 0 | 0.0 | 15.250 |
| profile | tag (chip_ev) | 3360 | 434 | 12.9 | 47.971 |
| profile | tag (money_ev) | 34 | 2 | 5.9 | 1.698 |
| street | flop (chip_ev) | 402 | 120 | 29.9 | 82.982 |
| street | flop (money_ev) | 6 | 0 | 0.0 | 0.315 |
| street | preflop (chip_ev) | 2242 | 92 | 4.1 | 22.693 |
| street | preflop (money_ev) | 20 | 0 | 0.0 | 0.060 |
| street | river (chip_ev) | 364 | 109 | 29.9 | 98.884 |
| street | river (money_ev) | 6 | 1 | 16.7 | 6.007 |
| street | turn (chip_ev) | 365 | 113 | 31.0 | 112.358 |
| street | turn (money_ev) | 5 | 1 | 20.0 | 3.724 |

## Highest standardized screening margins

- Hand 6, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'call', 'raise_to': None}`: modeled regret 1486.391 chip_ev, SE 50.280, lower bound 1360.805.
- Hand 3, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 1429.312 chip_ev, SE 83.880, lower bound 1228.505.
- Hand 6, {'position': 'late', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'call', 'raise_to': None}`: modeled regret 1220.938 chip_ev, SE 39.125, lower bound 1123.214.
- Hand 5, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'call', 'raise_to': None}`: modeled regret 1197.562 chip_ev, SE 50.738, lower bound 1070.834.
- Hand 11, {'position': 'early', 'depth': 'medium', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 1670.648 chip_ev, SE 74.720, lower bound 1491.769.
- Hand 16, {'position': 'early', 'depth': 'medium', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 360}`: modeled regret 1125.766 chip_ev, SE 15.640, lower bound 1086.702.
- Hand 15, {'position': 'early', 'depth': 'medium', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 534}`: modeled regret 1233.250 chip_ev, SE 59.415, lower bound 1084.848.
- Hand 15, {'position': 'early', 'depth': 'deep', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 240}`: modeled regret 1237.395 chip_ev, SE 88.552, lower bound 1016.217.
- Hand 3, {'position': 'late', 'depth': 'deep', 'street': 'turn', 'profile': 'tag'}, chosen `{'action': 'raise', 'raise_to': 480}`: modeled regret 505.891 chip_ev, SE 14.028, lower bound 470.852.
- Hand 16, {'position': 'early', 'depth': 'deep', 'street': 'river', 'profile': 'tag'}, chosen `{'action': 'check', 'raise_to': None}`: modeled regret 981.922 chip_ev, SE 77.521, lower bound 796.338.
