# League results

Configuration: `{"buy_in": 100, "calibration": "17da834551b4e7bbf0d41d070eb82259ae553bf392abf90a5d87b8dfb336bb6b", "fee": 10, "payouts": [450, 270, 180], "players": 9, "rollout_samples": 8, "samples": 32, "selection": "a59287b7d0099b4841820694dbc8f9a7125c2aa1f1fbccb889bc2e221d43a34e", "source": "a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c", "split": "test", "version": "0.6"}`

| Profile | Policy | N | ROI % | Place | ITM % | Mean ms | Advanced route % | Rollout calls | Overrides |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tag | math | 72 | -12.5 | 5.12 | 27.8 | 2.50 | 0.0 | 0 | 0 |
| tag | advanced | 72 | 164.8 | 3.11 | 69.4 | 18.36 | 100.0 | 0 | 0 |
| tag | adaptive | 72 | 142.0 | 3.89 | 59.7 | 21.27 | 0.0 | 0 | 0 |
| tag | candidate | 72 | 60.2 | 4.14 | 50.0 | 7.59 | 0.0 | 1218 | 167 |
| tag | toggle_adapt | 72 | 121.6 | 3.92 | 58.3 | 11.25 | 48.6 | 366 | 52 |
| tag | no_rollout | 72 | -12.5 | 5.12 | 27.8 | 2.58 | 0.0 | 0 | 0 |
| lag | math | 72 | 69.3 | 2.99 | 68.1 | 1.98 | 0.0 | 0 | 0 |
| lag | advanced | 72 | -46.6 | 5.00 | 23.6 | 17.74 | 100.0 | 0 | 0 |
| lag | adaptive | 72 | -47.7 | 5.81 | 18.1 | 29.40 | 0.0 | 0 | 0 |
| lag | candidate | 72 | 78.4 | 2.86 | 69.4 | 7.01 | 0.0 | 1437 | 251 |
| lag | toggle_adapt | 72 | 88.6 | 2.82 | 72.2 | 6.66 | 0.0 | 1490 | 271 |
| lag | no_rollout | 72 | 69.3 | 2.99 | 68.1 | 2.03 | 0.0 | 0 | 0 |
| passive | math | 72 | 78.4 | 3.08 | 59.7 | 2.44 | 0.0 | 0 | 0 |
| passive | advanced | 72 | -6.8 | 5.47 | 30.6 | 24.13 | 100.0 | 0 | 0 |
| passive | adaptive | 72 | 5.7 | 5.62 | 30.6 | 28.07 | 0.0 | 0 | 0 |
| passive | candidate | 72 | 111.4 | 2.89 | 62.5 | 6.59 | 0.0 | 1337 | 208 |
| passive | toggle_adapt | 72 | 97.7 | 3.01 | 61.1 | 6.21 | 0.4 | 1335 | 190 |
| passive | no_rollout | 72 | 78.4 | 3.08 | 59.7 | 2.54 | 0.0 | 0 | 0 |
