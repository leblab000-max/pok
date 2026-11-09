# Poker AI v0.5 benchmark

Configuration: `{"audit_samples": 128, "audit_stride": 32, "buy_in": 100, "calibration": "17da834551b4e7bbf0d41d070eb82259ae553bf392abf90a5d87b8dfb336bb6b", "fee": 10, "payouts": [450, 270, 180], "players": 9, "samples": 32, "source": "6bbf57dcb9de8961b9ef205605e41b450ec096d7ff8c1ab7a670cf9ebc805f62", "split": "test", "trace_stride": 4, "version": "0.5"}`

Independent new seed window; whole tournaments are the sampling unit. Common seeds and seats do not imply identical later game histories.
ROI intervals are percentile bootstrap 95% intervals (4000 resamples). Small/toy populations do not establish real-world strength.
Potentially-costly rates use a deterministic subset audited by a separate larger-sample response-tree evaluator; these are not proven mistakes.

| Opponents | Policy | N | Chip/hand | Place | ITM % | ROI % | ROI SE pp | ROI bootstrap CI % | Mean ms | P95 ms | Audits | Flagged % | Adapt ready % |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| tag | call | 108 | -35.27 | 7.77 | 4.6 | -86.4 | 6.3 | [-97.0, -72.7] | 0.00 | 0.00 | 461 | 23.4 | 0.0 |
| tag | math | 108 | 8.36 | 4.61 | 43.5 | 34.8 | 16.4 | [3.8, 66.7] | 4.49 | 10.45 | 343 | 12.0 | 0.0 |
| tag | advanced | 108 | 63.18 | 2.83 | 72.2 | 182.6 | 17.6 | [147.7, 215.9] | 34.79 | 82.35 | 291 | 3.4 | 0.0 |
| tag | adaptive | 108 | -10.07 | 4.06 | 56.5 | 125.8 | 19.4 | [87.9, 163.6] | 46.08 | 108.92 | 225 | 0.9 | 21.0 |
| lag | call | 108 | -652.29 | 6.51 | 17.6 | -47.7 | 11.5 | [-69.7, -24.2] | 0.00 | 0.00 | 235 | 20.9 | 0.0 |
| lag | math | 108 | -39.44 | 3.17 | 68.5 | 72.7 | 14.0 | [44.7, 100.0] | 3.61 | 7.87 | 325 | 19.4 | 0.0 |
| lag | advanced | 108 | -352.92 | 5.05 | 30.6 | -23.5 | 12.1 | [-46.2, 0.0] | 33.45 | 77.65 | 193 | 3.6 | 0.0 |
| lag | adaptive | 108 | -387.69 | 5.13 | 29.6 | -15.9 | 13.9 | [-40.9, 12.9] | 40.52 | 99.70 | 159 | 0.0 | 2.1 |
| passive | call | 108 | -48.34 | 6.33 | 19.4 | -57.6 | 9.1 | [-74.2, -38.6] | 0.00 | 0.00 | 430 | 19.8 | 0.0 |
| passive | math | 108 | 20.69 | 3.24 | 55.6 | 69.7 | 16.5 | [37.9, 102.3] | 4.54 | 9.59 | 371 | 15.9 | 0.0 |
| passive | advanced | 108 | -145.03 | 5.38 | 31.5 | -6.1 | 14.6 | [-34.1, 23.5] | 44.97 | 111.73 | 215 | 5.1 | 0.0 |
| passive | adaptive | 108 | -152.74 | 6.33 | 18.5 | -34.1 | 13.9 | [-59.1, -6.1] | 53.88 | 126.95 | 162 | 0.6 | 10.7 |

## Paired Adaptive minus reference

Seed-paired percentile bootstrap intervals use Bonferroni alpha=.05/9 for nine comparisons. Minimum gate: 100 pairs and positive adjusted lower bound. No automatic promotion.

| Profile | Reference | Pairs | Mean ROI difference pp | Adjusted bootstrap CI pp | Gate |
|---|---|---:|---:|---|---|
| tag | call | 108 | 212.1 | [159.8, 264.4] | positive synthetic-population screen |
| tag | math | 108 | 90.9 | [21.2, 159.1] | positive synthetic-population screen |
| tag | advanced | 108 | -56.8 | [-119.7, 7.6] | not established |
| lag | call | 108 | 31.8 | [-6.1, 72.7] | not established |
| lag | math | 108 | -88.6 | [-136.4, -35.6] | not established |
| lag | advanced | 108 | 7.6 | [-34.1, 49.2] | not established |
| passive | call | 108 | 23.5 | [-22.7, 72.0] | not established |
| passive | math | 108 | -103.8 | [-159.1, -47.0] | not established |
| passive | advanced | 108 | -28.0 | [-78.8, 25.8] | not established |

## Other metric uncertainty

Mean/SE/normal 95% intervals per tournament; ROI inference above uses bootstrap. ITM normal bounds may exceed [0,1].

- tag/call: `{"chip_per_hand": {"ci": [-40.12749799172243, -30.413996961820366], "mean": -35.2707474767714, "n": 108, "se": 2.4779339361995056}, "itm": {"ci": [0.006481541854876045, 0.08611105073771655], "mean": 0.046296296296296294, "n": 108, "se": 0.020313650225214412}, "place": {"ci": [7.4106670931269605, 8.126369943910076], "mean": 7.768518518518518, "n": 108, "se": 0.18257725785283563}}`
- tag/math: `{"chip_per_hand": {"ci": [-3.616464429558876, 20.342723261878653], "mean": 8.36312941615989, "n": 108, "se": 6.112037676387126}, "itm": {"ci": [0.34124438103540683, 0.5291259893349636], "mean": 0.4351851851851852, "n": 108, "se": 0.04792898170907059}, "place": {"ci": [4.0685015342708795, 5.153720687951342], "mean": 4.611111111111111, "n": 108, "se": 0.27684162083685293}}`
- tag/advanced: `{"chip_per_hand": {"ci": [27.51581597371979, 98.84367863293284], "mean": 63.17974730332631, "n": 108, "se": 18.195883331431897}, "itm": {"ci": [0.6373533647290677, 0.8070910797153767], "mean": 0.7222222222222222, "n": 108, "se": 0.04330043749650743}, "place": {"ci": [2.278805727752392, 3.387860938914275], "mean": 2.8333333333333335, "n": 108, "se": 0.2829222477453785}}`
- tag/adaptive: `{"chip_per_hand": {"ci": [-62.249874390178235, 42.10219581159967], "mean": -10.073839289289278, "n": 108, "se": 26.620426071882118}, "itm": {"ci": [0.4708740106650364, 0.6587556189645931], "mean": 0.5648148148148148, "n": 108, "se": 0.04792898170907059}, "place": {"ci": [3.3857240576351284, 4.725387053475982], "mean": 4.055555555555555, "n": 108, "se": 0.34175076424511575}}`
- lag/call: `{"chip_per_hand": {"ci": [-735.9014171691721, -568.6829586396542], "mean": -652.2921879044131, "n": 108, "se": 42.65777003304028}, "itm": {"ci": [0.10377993034911791, 0.24807192150273394], "mean": 0.17592592592592593, "n": 108, "se": 0.036809181416738786}, "place": {"ci": [6.015629255492578, 7.002889263025941], "mean": 6.5092592592592595, "n": 108, "se": 0.25185204273810285}}`
- lag/math: `{"chip_per_hand": {"ci": [-77.06757322573998, -1.814326864028338], "mean": -39.440950044884154, "n": 108, "se": 19.197256724926437}, "itm": {"ci": [0.5971825361427956, 0.7731878342275749], "mean": 0.6851851851851852, "n": 108, "se": 0.0448993107359131}, "place": {"ci": [2.8260506872798534, 3.5072826460534796], "mean": 3.1666666666666665, "n": 108, "se": 0.1737836629524557}}`
- lag/advanced: `{"chip_per_hand": {"ci": [-433.6820303630019, -272.1660357575921], "mean": -352.924033060297, "n": 108, "se": 41.20305984831883}, "itm": {"ci": [0.21827288441100587, 0.39283822670010526], "mean": 0.3055555555555556, "n": 108, "se": 0.044531975073749855}, "place": {"ci": [4.576199245128662, 5.516393347463931], "mean": 5.046296296296297, "n": 108, "se": 0.23984543426920138}}`
- lag/adaptive: `{"chip_per_hand": {"ci": [-480.4385322825864, -294.9380959475493], "mean": -387.68831411506784, "n": 108, "se": 47.32153988138701}, "itm": {"ci": [0.2097751604259397, 0.38281743216665287], "mean": 0.2962962962962963, "n": 108, "se": 0.04414343666854928}, "place": {"ci": [4.64033055272786, 5.618928706531399], "mean": 5.12962962962963, "n": 108, "se": 0.249642386174372}}`
- passive/call: `{"chip_per_hand": {"ci": [-56.513626704465764, -40.161419820143394], "mean": -48.33752326230458, "n": 108, "se": 4.1714813480414215}, "itm": {"ci": [0.11945334847670111, 0.26943554041218776], "mean": 0.19444444444444445, "n": 108, "se": 0.03826076324884864}, "place": {"ci": [5.8742442839337174, 6.792422382732949], "mean": 6.333333333333333, "n": 108, "se": 0.23422910683653878}}`
- passive/math: `{"chip_per_hand": {"ci": [4.988207978015467, 36.38629322397189], "mean": 20.68725060099368, "n": 108, "se": 8.009715623968475}, "itm": {"ci": [0.4614020117458279, 0.6497090993652832], "mean": 0.5555555555555556, "n": 108, "se": 0.04803752235190188}, "place": {"ci": [2.8716723264464514, 3.6098091550350304], "mean": 3.240740740740741, "n": 108, "se": 0.18830021137463757}}`
- passive/advanced: `{"chip_per_hand": {"ci": [-203.87269787715857, -86.18642797678561], "mean": -145.0295629269721, "n": 108, "se": 30.02200762764617}, "itm": {"ci": [0.22681216577242513, 0.4028174638572045], "mean": 0.3148148148148148, "n": 108, "se": 0.0448993107359131}, "place": {"ci": [4.845738192717871, 5.913521066541389], "mean": 5.37962962962963, "n": 108, "se": 0.2723935902611013}}`
- passive/adaptive: `{"chip_per_hand": {"ci": [-313.30431843057767, 7.826283032421031], "mean": -152.73901769907832, "n": 108, "se": 81.92107180178539}, "itm": {"ci": [0.11158197423045643, 0.2587883961399139], "mean": 0.18518518518518517, "n": 108, "se": 0.03755265865037181}, "place": {"ci": [5.811226675918531, 6.855439990748135], "mean": 6.333333333333333, "n": 108, "se": 0.2663809476606131}}`

## Limits

Adaptive samples explicit fold/call subsets with exact side pots, but omits response re-raises and future-street betting. Ranges and response-price likelihoods are heuristic. Calibration learns public-stat centroids of these artificial opponents only. Advanced retains its v0.4 decision model as a frozen reference; shared optimizations preserve its numeric outputs. A fixed maximum joint-deal budget is used, not identical wall time: Advanced <=2*samples, Adaptive 2*samples, Mathematical 2*samples. Audit work is outside decision timing. No poker-room integration, spending or background training. Viewed holdouts must not be reused for tuning.
