# League results

Configuration: `{"buy_in": 100, "calibration": "17da834551b4e7bbf0d41d070eb82259ae553bf392abf90a5d87b8dfb336bb6b", "fee": 10, "payouts": [450, 270, 180], "players": 9, "rollout_samples": 8, "samples": 32, "selection": "a59287b7d0099b4841820694dbc8f9a7125c2aa1f1fbccb889bc2e221d43a34e", "source": "a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c", "split": "test", "version": "0.6"}`

| Profile | Policy | N | ROI % | Place | ITM % | Mean ms | Advanced route % | Rollout calls | Overrides |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mixed | math | 18 | 54.5 | 3.67 | 50.0 | 1.85 | 0.0 | 0 | 0 |
| mixed | advanced | 18 | -63.6 | 6.39 | 11.1 | 16.64 | 100.0 | 0 | 0 |
| mixed | adaptive | 18 | -54.5 | 7.11 | 11.1 | 24.27 | 0.0 | 0 | 0 |
| mixed | candidate | 18 | 113.6 | 3.11 | 61.1 | 6.16 | 0.0 | 383 | 65 |
| mixed | toggle_adapt | 18 | 140.9 | 3.00 | 61.1 | 6.06 | 9.8 | 303 | 45 |
| mixed | no_rollout | 18 | 54.5 | 3.67 | 50.0 | 1.94 | 0.0 | 0 | 0 |
| pressure | math | 18 | 104.5 | 2.94 | 61.1 | 1.65 | 0.0 | 0 | 0 |
| pressure | advanced | 18 | -27.3 | 4.33 | 33.3 | 12.18 | 100.0 | 0 | 0 |
| pressure | adaptive | 18 | -9.1 | 5.00 | 33.3 | 16.68 | 0.0 | 0 | 0 |
| pressure | candidate | 18 | 113.6 | 2.89 | 66.7 | 3.34 | 0.0 | 110 | 8 |
| pressure | toggle_adapt | 18 | 104.5 | 2.94 | 61.1 | 2.99 | 0.0 | 100 | 9 |
| pressure | no_rollout | 18 | 104.5 | 2.94 | 61.1 | 1.70 | 0.0 | 0 | 0 |
