# League results

Configuration: `{"buy_in": 100, "calibration": "17da834551b4e7bbf0d41d070eb82259ae553bf392abf90a5d87b8dfb336bb6b", "fee": 10, "payouts": [450, 270, 180], "players": 9, "rollout_samples": 8, "samples": 32, "selection": null, "source": "a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c", "split": "train", "version": "0.6"}`

| Profile | Policy | N | ROI % | Place | ITM % | Mean ms | Advanced route % | Rollout calls | Overrides |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tag | math | 18 | 59.1 | 4.44 | 44.4 | 2.32 | 0.0 | 0 | 0 |
| tag | advanced | 18 | 159.1 | 3.22 | 66.7 | 16.22 | 100.0 | 0 | 0 |
| tag | adaptive | 18 | 150.0 | 3.78 | 61.1 | 18.03 | 0.0 | 0 | 0 |
| tag | blend | 18 | 127.3 | 4.11 | 55.6 | 7.77 | 42.0 | 0 | 0 |
| tag | lookahead | 18 | 127.3 | 3.94 | 55.6 | 8.46 | 42.2 | 95 | 12 |
| tag | fixed | 18 | 150.0 | 3.00 | 66.7 | 7.06 | 0.0 | 351 | 36 |
| lag | math | 18 | 45.5 | 3.17 | 50.0 | 1.73 | 0.0 | 0 | 0 |
| lag | advanced | 18 | -22.7 | 4.94 | 27.8 | 16.92 | 100.0 | 0 | 0 |
| lag | adaptive | 18 | -22.7 | 4.72 | 33.3 | 22.43 | 0.0 | 0 | 0 |
| lag | blend | 18 | 45.5 | 3.17 | 50.0 | 1.78 | 0.1 | 0 | 0 |
| lag | lookahead | 18 | 95.5 | 2.78 | 66.7 | 5.67 | 0.1 | 361 | 60 |
| lag | fixed | 18 | 59.1 | 3.06 | 61.1 | 5.05 | 0.0 | 272 | 37 |
| passive | math | 18 | 50.0 | 3.17 | 50.0 | 2.24 | 0.0 | 0 | 0 |
| passive | advanced | 18 | 36.4 | 4.83 | 38.9 | 19.59 | 100.0 | 0 | 0 |
| passive | adaptive | 18 | -13.6 | 5.83 | 27.8 | 26.31 | 0.0 | 0 | 0 |
| passive | blend | 18 | 50.0 | 3.17 | 50.0 | 2.30 | 0.0 | 0 | 0 |
| passive | lookahead | 18 | 77.3 | 2.83 | 61.1 | 6.12 | 0.0 | 351 | 62 |
| passive | fixed | 18 | 122.7 | 2.44 | 66.7 | 5.84 | 0.0 | 380 | 71 |
