# Poker AI v0.4 benchmark

Configuration: `{"buy_in": 100, "fee": 10, "payouts": [0.5, 0.3, 0.2], "players": 9, "samples": 32, "source": "3b4316caccf1c868ade481304862004eec8a5a0f45d8dd3c5b313a1494c165c9", "split": "test", "version": "0.4"}`

Confidence intervals are exploratory normal 95% intervals over independent tournaments, not decisions. Small samples cannot establish superiority.
Chip EV is realized net chip delta per hero hand; final tournament chip totals are not proof of action EV.

| Opponents | Hero | N | Chip/hand | Place | ITM % | ROI % | ROI SE pp | ROI 95% CI % | Mean decision ms | P95 ms | ICM decisions |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| tag | fold | 9 | -18.77 | 4.22 | 33.3 | -36.4 | 32.8 | [-100.6, 27.9] | 0.00 | 0.00 | 0 |
| tag | call | 9 | -17.05 | 7.11 | 11.1 | -54.5 | 45.5 | [-143.6, 34.5] | 0.00 | 0.00 | 0 |
| tag | math | 9 | 27.66 | 2.78 | 66.7 | 109.1 | 59.6 | [-7.8, 225.9] | 3.39 | 6.87 | 0 |
| tag | advanced | 9 | 56.06 | 4.00 | 55.6 | 127.3 | 71.9 | [-13.6, 268.1] | 43.58 | 97.08 | 21 |
| lag | fold | 9 | -25.52 | 2.56 | 100.0 | 100.0 | 14.4 | [71.8, 128.2] | 0.00 | 0.00 | 0 |
| lag | call | 9 | -271.26 | 6.00 | 33.3 | 0.0 | 52.4 | [-102.7, 102.7] | 0.00 | 0.00 | 0 |
| lag | math | 9 | -57.22 | 3.67 | 55.6 | -9.1 | 28.7 | [-65.4, 47.3] | 2.67 | 5.94 | 0 |
| lag | advanced | 9 | -300.43 | 5.67 | 22.2 | -63.6 | 24.1 | [-110.8, -16.5] | 148.99 | 178.50 | 3 |
| passive | fold | 9 | -21.93 | 3.44 | 66.7 | 9.1 | 27.3 | [-44.4, 62.5] | 0.00 | 0.00 | 0 |
| passive | call | 9 | -6.86 | 5.00 | 33.3 | 18.2 | 61.2 | [-101.7, 138.0] | 0.00 | 0.00 | 0 |
| passive | math | 9 | 15.73 | 3.67 | 44.4 | 36.4 | 59.4 | [-80.1, 152.9] | 4.04 | 9.64 | 0 |
| passive | advanced | 9 | -77.79 | 4.33 | 44.4 | 63.6 | 66.8 | [-67.3, 194.6] | 48.60 | 111.12 | 29 |

## Paired advanced minus legacy comparisons

Common seeds and hero-seat rotation; differing actions change later game trajectories.
Bonferroni normal intervals cover 9 comparisons. Gate requires >=100 pairs per comparison and positive lower bound; never promotes a policy.

| Opponents | Reference | Pairs | ROI difference pp | Adjusted interval pp | Gate |
|---|---|---:|---:|---|---|
| tag | fold | 9 | 163.6 | [-36.4, 363.7] | insufficient evidence |
| tag | call | 9 | 181.8 | [-17.5, 381.1] | insufficient evidence |
| tag | math | 9 | 18.2 | [-237.7, 274.0] | insufficient evidence |
| lag | fold | 9 | -163.6 | [-256.3, -71.0] | insufficient evidence |
| lag | call | 9 | -63.6 | [-162.1, 34.8] | insufficient evidence |
| lag | math | 9 | -54.5 | [-130.2, 21.1] | insufficient evidence |
| passive | fold | 9 | 54.5 | [-122.8, 231.9] | insufficient evidence |
| passive | call | 9 | 45.5 | [-235.3, 326.2] | insufficient evidence |
| passive | math | 9 | 27.3 | [-250.6, 305.1] | insufficient evidence |

## Other metric uncertainty

Mean, standard error and 95% CI (chip/hand, place, ITM fraction) follow. ITM normal intervals may extend beyond [0,1].

- tag/fold: `{"chip_per_hand": {"ci": [-20.15486637895905, -17.393116098302052], "mean": -18.77399123863055, "n": 9, "se": 0.7045281328206635}, "itm": {"ci": [0.006666666666666654, 0.6599999999999999], "mean": 0.3333333333333333, "n": 9, "se": 0.16666666666666666}, "place": {"ci": [3.200753901194009, 5.243690543250436], "mean": 4.222222222222222, "n": 9, "se": 0.5211573066470477}}`
- tag/call: `{"chip_per_hand": {"ci": [-55.21875410384072, 21.123829409800592], "mean": -17.047462347020065, "n": 9, "se": 19.475148855520743}, "itm": {"ci": [-0.10666666666666666, 0.3288888888888889], "mean": 0.1111111111111111, "n": 9, "se": 0.1111111111111111}, "place": {"ci": [5.368888888888889, 8.853333333333333], "mean": 7.111111111111111, "n": 9, "se": 0.8888888888888888}}`
- tag/math: `{"chip_per_hand": {"ci": [-17.092704889306415, 72.41380914132533], "mean": 27.66055212600946, "n": 9, "se": 22.833294395569325}, "itm": {"ci": [0.33999999999999997, 0.9933333333333333], "mean": 0.6666666666666666, "n": 9, "se": 0.16666666666666666}, "place": {"ci": [1.5652424276503507, 3.9903131279052046], "mean": 2.7777777777777777, "n": 9, "se": 0.6186404847588913}}`
- tag/advanced: `{"chip_per_hand": {"ci": [-34.52663993460943, 146.6478557246398], "mean": 56.06060789501519, "n": 9, "se": 46.21798358654317}, "itm": {"ci": [0.2112186547816654, 0.8998924563294457], "mean": 0.5555555555555556, "n": 9, "se": 0.17568209223157663}, "place": {"ci": [1.469650880477821, 6.530349119522179], "mean": 4.0, "n": 9, "se": 1.2909944487358056}}`
- lag/fold: `{"chip_per_hand": {"ci": [-27.399154851106115, -23.640932337889932], "mean": -25.520043594498024, "n": 9, "se": 0.9587302329633124}, "itm": {"ci": [1.0, 1.0], "mean": 1.0, "n": 9, "se": 0.0}, "place": {"ci": [2.211218654781665, 2.8998924563294457], "mean": 2.5555555555555554, "n": 9, "se": 0.17568209223157663}}`
- lag/call: `{"chip_per_hand": {"ci": [-442.70772903328384, -99.80399984744574], "mean": -271.2558644403648, "n": 9, "se": 87.47544111883626}, "itm": {"ci": [0.006666666666666654, 0.6599999999999999], "mean": 0.3333333333333333, "n": 9, "se": 0.16666666666666666}, "place": {"ci": [3.833138470301139, 8.166861529698862], "mean": 6.0, "n": 9, "se": 1.1055415967851332}}`
- lag/math: `{"chip_per_hand": {"ci": [-79.90798022893165, -34.535610827562635], "mean": -57.22179552824714, "n": 9, "se": 11.574584030961484}, "itm": {"ci": [0.2112186547816654, 0.8998924563294457], "mean": 0.5555555555555556, "n": 9, "se": 0.17568209223157663}, "place": {"ci": [3.013333333333333, 4.32], "mean": 3.6666666666666665, "n": 9, "se": 0.3333333333333333}}`
- lag/advanced: `{"chip_per_hand": {"ci": [-499.5971864790364, -101.27108105589778], "mean": -300.4341337674671, "n": 9, "se": 101.61380240386188}, "itm": {"ci": [-0.06587069831592207, 0.5103151427603665], "mean": 0.2222222222222222, "n": 9, "se": 0.1469861839480328}, "place": {"ci": [4.0663333680483245, 7.2669999652850095], "mean": 5.666666666666667, "n": 9, "se": 0.8164965809277259}}`
- passive/fold: `{"chip_per_hand": {"ci": [-23.652199687038873, -20.216794696429446], "mean": -21.93449719173416, "n": 9, "se": 0.8763788241350587}, "itm": {"ci": [0.33999999999999997, 0.9933333333333333], "mean": 0.6666666666666666, "n": 9, "se": 0.16666666666666666}, "place": {"ci": [2.969808781703349, 3.91908010718554], "mean": 3.4444444444444446, "n": 9, "se": 0.2421610524189263}}`
- passive/call: `{"chip_per_hand": {"ci": [-63.61864034908533, 49.89984478014129], "mean": -6.859397784472023, "n": 9, "se": 28.958797226843526}, "itm": {"ci": [0.006666666666666654, 0.6599999999999999], "mean": 0.3333333333333333, "n": 9, "se": 0.16666666666666666}, "place": {"ci": [2.9083127491052694, 7.091687250894731], "mean": 5.0, "n": 9, "se": 1.0671873729054748}}`
- passive/math: `{"chip_per_hand": {"ci": [-43.44358531360733, 74.89507885678081], "mean": 15.72574677158674, "n": 9, "se": 30.188434737343915}, "itm": {"ci": [0.10010754367055424, 0.7887813452183345], "mean": 0.4444444444444444, "n": 9, "se": 0.17568209223157663}, "place": {"ci": [2.3197854956315638, 5.013547837701769], "mean": 3.6666666666666665, "n": 9, "se": 0.6871842709362768}}`
- passive/advanced: `{"chip_per_hand": {"ci": [-228.42791144907454, 72.84008397819134], "mean": -77.79391373544159, "n": 9, "se": 76.85408046613925}, "itm": {"ci": [0.10010754367055424, 0.7887813452183345], "mean": 0.4444444444444444, "n": 9, "se": 0.17568209223157663}, "place": {"ci": [2.166471803634472, 6.500194863032194], "mean": 4.333333333333333, "n": 9, "se": 1.1055415967851332}}`

## Limits

Heuristic opponent policies; uniform initial dealt-card priors; action-likelihood inference is uncalibrated. Few equity samples can select noisy actions. Multiway raises omit mixed responses and future betting. ICM is applied only to terminal heads-up calls and a restricted short-stack preflop push/fold subgame. No positive profitability or general superiority claim. Runtime measurements depend on hardware. Do not reuse a viewed test set for tuning; reserve a new confirmation set.
