# Public opponent diagnostics

Snapshot counts are correlated and selected by survival; these are descriptive diagnostics, not independent classification trials.
True synthetic profile labels are used only for evaluation, never as playing-strategy input.

| Actual profile | Opponent contexts | Ready contexts % | Classification correct among ready % | Observed wager responses | Raise responses % |
|---|---:|---:|---:|---:|---:|
| tag | 4013 | 12.5 | 94.2 | 11580 | 20.2 |
| lag | 1707 | 0.9 | 93.3 | 19924 | 62.8 |
| passive | 2898 | 3.6 | 98.1 | 22118 | 12.1 |

Observed wager responses are deduplicated public events present in stored snapshots, not a complete census. They include opponents responding to each other. Raise responses are branches omitted by the current fold/call EV model. Low ready-context coverage limits any claim that strategy performance comes from learned adaptation.
