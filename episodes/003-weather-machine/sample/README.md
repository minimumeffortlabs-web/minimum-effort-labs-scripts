# Recorded weather sample (offline)
This is recorded live Open-Meteo model-derived API data, retrieved
2026-10-20T05:31:11.932425+00:00, for the example Kansas City coordinates
39.10, -94.58 in America/Chicago, covering October 15–19, 2026.
It is neither a fresh query nor synthetic observation data. Grid coordinates
may differ from requested coordinates. No creator/company location is implied.
Run from the episode directory:
`python weather_change_report.py --replay sample/recorded_weather_capture.json --output weather_report.txt`.
The UTF-8 output must match expected_report.txt byte for byte. The first change
is NA; the next daily high drops from 22.4 to 11.6 C (-10.8 C). This is not a
causal estimate. Missing data is not zero. Attribution: Open-Meteo,
https://open-meteo.com/, data CC BY 4.0, https://creativecommons.org/licenses/by/4.0/.
The unmodified recorded JSON and example report are supplied with attribution;
provenance.json omits internal execution paths. Replay needs no network request.
