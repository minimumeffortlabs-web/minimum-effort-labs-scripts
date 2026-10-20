# Episode 003 — The Weather Machine: full Python lesson

## Learning objectives
Use requests with explicit errors/timeouts, validate JSON arrays, compute changes
with generators, preserve missingness, and replay a provenance-labelled capture.

## The problem
MEL wants evidence its weather machine works. This program can summarize weather,
but cannot establish that the machine caused it. In ordinary work, the same skills
turn structured API data into a reproducible report for later inspection.

## Python concepts
`requests.get` sends an HTTPS request with query parameters. `raise_for_status`
rejects unsuccessful HTTP status codes; `json` parses the response into dictionaries
and lists. ISO dates and IANA `ZoneInfo` select completed local days. `None` means
unknown, not zero. A generator remembers the previous daily high with little state.

## Code walkthrough
These excerpts come directly from the runnable source:

```python
def fetch_data(params):
    response = requests.get(
        API_URL, params=params,
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return data
```

The 15-second timeout and status check prevent an HTTP error page being silently
treated as a report. JSON parsing can also fail. The CLI catches request errors.

```python
def temperature_changes(highs):
    previous = None
    for high in highs:
        delta = None
        if (
            high is not None
            and previous is not None
        ):
            delta = high - previous
        yield delta
        previous = high
```

The first difference is unknown. If either adjacent high is missing, the result
is `None`; updating `previous` every iteration avoids bridging an unknown day.

```python
def save_report(output, report):
    with output.open(
        "x", encoding="utf-8"
    ) as file:
        file.write(report)
```

UTF-8 preserves report text; exclusive creation prevents replacement of an existing
report. `analyze()` pairs dates and values only after `validate_data()` has checked
aligned arrays, expected units, dates, numeric values and timezone boundaries.
`format_report()` includes attribution, retrieval time, coverage and limitations.

## How the solution works
Live mode builds a bounded date request -> fetches JSON -> records provenance ->
validates -> analyzes -> formats -> saves. Replay reads the stored envelope and
validates against its historical retrieval time rather than today's date. It
never calls the network. Both modes use the same calculation/report functions.

## Running the example
After installing README dependencies, run the offline sample:

```sh
python weather_change_report.py --replay sample/recorded_weather_capture.json --output weather_report.txt
python -m unittest discover -s tests -v
```

For a current query use the separate live command in README. No API account is
configured by this package. Check provider terms/eligibility for your use before
live requests; testing the supplied replay does not consume API quota.

## Understanding the results
The CLI starts with `Replaying recorded-live-api captured` and the exact retrieval
timestamp, then reports October 15–19, 2026 and five days. Output matches
sample/expected_report.txt byte for byte. Daily highs are 22.4, 11.6, 16.1, 20.0,
18.5 C. The first change is NA, the next is -10.8 C. Summary extremes and coverage
are computed from the arrays. Precipitation includes rain, showers and snow water
equivalent; unavailable values stay unknown. Model-derived daily aggregates are
not independent station observations or a controlled experiment.

## Exercises
1. Call `temperature_changes([20, None, 23, 21])` in a small experiment.
   Hint: expect three unknown comparisons before the final -2.
2. Copy the fixture and label it synthetic-test-fixture before experimenting with
   values. Hint: never edit or relabel recorded data as fresh evidence.
3. Add a coverage percentage to an experimental report. Hint: divide available
   values by dates, keeping all-missing coverage explicit.

## Limitations
Recent 92-day window, 1–31 completed dates; not an archival climate analysis tool.
Ranges crossing a UTC-offset change are rejected because the provider applies a
fixed current offset. Missing highs interrupt consecutive comparisons. A missing
precipitation day makes the full-period total unknown; a known-day sum is labelled.
No retries/cache are invented. If recording the optional capture fails after the
text report is written, inspect that output before retrying with new names.
Data: Open-Meteo, CC BY 4.0; retain attribution. API access conditions and code
licensing are distinct; see README and sample notes. No causal conclusion follows.

## Further learning
Explore HTTP status codes, JSON schemas, IANA timezones, missing-data semantics,
mocked network tests, reproducibility and observational-versus-causal reasoning.


[Back to setup and commands](README.md).
