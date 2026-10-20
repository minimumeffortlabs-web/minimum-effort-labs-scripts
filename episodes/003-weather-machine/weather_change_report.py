"""Open-Meteo model-derived daily weather -> a reproducible text report; no causal inference."""
import requests
import math
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API_URL = "https://api.open-meteo.com/v1/forecast"
FIELDS = ["temperature_2m_max", "temperature_2m_min",
          "precipitation_sum", "wind_speed_10m_max"]
EXAMPLE = (39.10, -94.58, "America/Chicago")


def fetch_data(params):
    response = requests.get(
        API_URL, params=params,
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return data


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


def analyze(data):
    daily = data["daily"]
    highs = daily["temperature_2m_max"]
    lows = daily["temperature_2m_min"]
    rain = daily["precipitation_sum"]
    wind = daily["wind_speed_10m_max"]
    changes = list(
        temperature_changes(highs)
    )
    days = daily["time"]
    def extreme(values, choose):
        pairs = [(value, day) for value, day in zip(values, days) if value is not None]
        return choose(pairs, key=lambda item: item[0]) if pairs else None
    known_rain = [value for value in rain if value is not None]
    total = math.fsum(known_rain) if len(known_rain) == len(days) else None
    return dict(rows=[dict(date=day,low=lo,high=hi,change=change,rain=pr,wind=ws)
                     for day,lo,hi,change,pr,ws in zip(days,lows,highs,changes,rain,wind)],
                warmest=extreme(highs,max),coldest=extreme(lows,min),highest_wind=extreme(wind,max),
                total_precipitation=total,known_precipitation=math.fsum(known_rain) if known_rain else None,
                coverage={key:sum(value is not None for value in daily[key]) for key in FIELDS})


def save_report(output, report):
    with output.open(
        "x", encoding="utf-8"
    ) as file:
        file.write(report)


def request_params(latitude, longitude, zone_name, days, now, end_date=None):
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be finite and between -90 and 90.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be finite and between -180 and 180.")
    if isinstance(days,bool) or not isinstance(days,int) or not 1 <= days <= 31:
        raise ValueError("Days must be an integer from 1 through 31.")
    if now.utcoffset() is None:
        raise ValueError("Reference time must be timezone-aware.")
    zone = ZoneInfo(zone_name)
    today = now.astimezone(zone).date()
    end = date.fromisoformat(end_date) if end_date else today-timedelta(days=1)
    start = end-timedelta(days=days-1)
    if end >= today or start < today-timedelta(days=92):
        raise ValueError("Choose complete past dates within the forecast API's 92-day recent window.")
    offsets = {datetime.combine(start+timedelta(days=i), time(), zone).utcoffset() for i in range(days+1)}
    offsets.add(now.astimezone(zone).utcoffset())
    if len(offsets) != 1:
        raise ValueError("This provider uses a fixed current offset for daily aggregates. A DST/offset-changing period is not supported; no incomplete calendar days will be silently accepted.")
    return dict(latitude=latitude,longitude=longitude,timezone=zone_name,
                start_date=start.isoformat(),end_date=end.isoformat(),daily=",".join(FIELDS),
                temperature_unit="celsius",precipitation_unit="mm",wind_speed_unit="kmh",timeformat="iso8601")


def validate_data(data, params, reference_time):
    if not isinstance(data,dict) or data.get("error"):
        raise ValueError("API did not return a valid weather object.")
    daily, units = data.get("daily"), data.get("daily_units")
    if not isinstance(daily,dict) or not isinstance(units,dict):
        raise ValueError("Missing daily arrays or units.")
    start, end = map(date.fromisoformat,(params["start_date"],params["end_date"]))
    expected = [(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
    if daily.get("time") != expected:
        raise ValueError("API dates are missing, out of order, duplicated, or include an unexpected/partial day.")
    zone = ZoneInfo(params["timezone"])
    if end >= reference_time.astimezone(zone).date():
        raise ValueError("A current or future partial day cannot be analyzed as complete.")
    if data.get("timezone") != params["timezone"]:
        raise ValueError("API timezone does not match the requested timezone.")
    expected_offset = int(reference_time.astimezone(zone).utcoffset().total_seconds())
    if data.get("utc_offset_seconds") != expected_offset:
        raise ValueError("Provider daily-boundary offset does not match the requested local clock.")
    expected_units = dict(temperature_2m_max="\u00b0C",temperature_2m_min="\u00b0C",precipitation_sum="mm",wind_speed_10m_max="km/h")
    for field in FIELDS:
        values = daily.get(field)
        if not isinstance(values,list) or len(values) != len(expected):
            raise ValueError(f"Missing or inconsistent daily array: {field}")
        if units.get(field) != expected_units[field]:
            raise ValueError(f"Unexpected units for {field}.")
        for value in values:
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)):
                raise ValueError(f"Invalid numeric daily value: {field}")
            if value is not None and field in ["precipitation_sum","wind_speed_10m_max"] and value < 0:
                raise ValueError(f"Negative precipitation or wind: {field}")
    for lo,hi in zip(daily["temperature_2m_min"],daily["temperature_2m_max"]):
        if lo is not None and hi is not None and lo > hi:
            raise ValueError("Daily minimum is greater than its maximum.")
    return data


def format_report(capture):
    data, params = capture["response"],capture["params"]
    reference = datetime.fromisoformat(capture["retrieved_at"])
    if reference.utcoffset() is None:
        raise ValueError("Capture retrieval timestamp must include a timezone.")
    validate_data(data,params,reference)
    result = analyze(data)
    def number(value,signed=False):
        return "NA" if value is None else format(value,"+.1f" if signed else ".1f")
    rows = ["MINIMUM EFFORT LABS \u2014 WEATHER CHANGE REPORT",
            f"Requested coordinates: {params['latitude']}, {params['longitude']}",
            f"Provider grid coordinates: {data.get('latitude')}, {data.get('longitude')}",
            f"Timezone: {params['timezone']}; daily UTC offset: {data['utc_offset_seconds']} seconds",
            f"Period: {params['start_date']} to {params['end_date']}",
            f"Retrieved (UTC): {capture['retrieved_at']}",
            f"Capture kind: {capture['kind']}",
            "Source: Open-Meteo Forecast API, https://open-meteo.com/ (CC BY 4.0)",
            "Method: model-derived daily aggregates, not direct station observations.",
            "Units: temperature C; precipitation mm; maximum wind km/h.",
            "Precipitation includes rain, showers and snow water equivalent.",
            "Date        Min C   Max C  Change C   Precip mm   Wind km/h"]
    for row in result["rows"]:
        rows.append(f"{row['date']} {number(row['low']):>6} {number(row['high']):>7} {number(row['change'],True):>9} {number(row['rain']):>11} {number(row['wind']):>11}")
    rows += ["", "Change C compares consecutive daily maxima; first day is NA."]
    for label,key,field,unit in [("Warmest daily maximum","warmest",FIELDS[0],"C"),("Coldest daily minimum","coldest",FIELDS[1],"C"),("Highest reported daily maximum wind","highest_wind",FIELDS[3],"km/h")]:
        best=result[key];description="NA" if best is None else f"{best[0]:.1f} {unit} on {best[1]}"
        rows.append(f"{label}: {description} ({result['coverage'][field]}/{len(result['rows'])} days available)")
    total=result['total_precipitation'];known=result['known_precipitation']
    rows.append(f"Period precipitation total: {number(total)} mm")
    if total is None:
        rows.append(f"Incomplete precipitation: known-day sum {number(known)} mm; {result['coverage'][FIELDS[2]]}/{len(result['rows'])} days available. No missing values treated as zero.")
    missing=[f"{row['date']}: {', '.join(k for k in ['low','high','rain','wind'] if row[k] is None)}" for row in result['rows'] if any(row[k] is None for k in ['low','high','rain','wind'])]
    rows += ["Missing data: "+("; ".join(missing) if missing else "none in requested daily arrays."),
             "Weather changes alone do not establish causation or prove machine effectiveness.",
             "Administrative status: Report complete. Machine effectiveness: Not established."]
    return "\n".join(rows)+"\n"


def main():
    import argparse,json,sys
    parser=argparse.ArgumentParser(description="Report recent completed weather days; no causal claims.")
    parser.add_argument("--latitude",type=float);parser.add_argument("--longitude",type=float)
    parser.add_argument("--timezone");parser.add_argument("--days",type=int)
    parser.add_argument("--end-date",help="Optional completed date YYYY-MM-DD for reproducibility; recent 92 days only.")
    parser.add_argument("--output",default="weather_report.txt")
    parser.add_argument("--record-json",help="Save a new provenance envelope for offline replay.")
    parser.add_argument("--replay",help="Replay an explicitly identified saved capture; no network request.")
    args=parser.parse_args();output=Path(args.output)
    try:
        if output.exists() or (args.record_json and (Path(args.record_json).exists() or Path(args.record_json).resolve()==output.resolve())):
            raise ValueError("Choose new, separate output and capture filenames.")
        if args.replay:
            capture=json.loads(Path(args.replay).read_text(encoding="utf-8"))
            if capture.get("kind") not in ["recorded-live-api","synthetic-test-fixture"]:
                raise ValueError("Replay must explicitly identify its provenance kind.")
            params=capture["params"]
            for name in ["latitude","longitude","timezone"]:
                if getattr(args,name) is not None and getattr(args,name)!=params[name]:
                    raise ValueError("Replay location must match the recorded request.")
            start,end=map(date.fromisoformat,(params["start_date"],params["end_date"]))
            if args.days is not None and args.days!=(end-start).days+1:
                raise ValueError("Replay day count differs from the capture.")
            if args.end_date and args.end_date!=params["end_date"]:
                raise ValueError("Replay end date differs from the capture.")
            request_params(params['latitude'],params['longitude'],params['timezone'],(end-start).days+1,datetime.fromisoformat(capture['retrieved_at']),params['end_date'])
            print("Replaying "+capture["kind"]+" captured "+capture["retrieved_at"])
        else:
            now=datetime.now(timezone.utc)
            params=request_params(args.latitude if args.latitude is not None else EXAMPLE[0],args.longitude if args.longitude is not None else EXAMPLE[1],args.timezone or EXAMPLE[2],args.days if args.days is not None else 5,now,args.end_date)
            print("Retrieving Open-Meteo model-based weather data...")
            data=fetch_data(params);retrieved=datetime.now(timezone.utc)
            if now.astimezone(ZoneInfo(params['timezone'])).date()!=retrieved.astimezone(ZoneInfo(params['timezone'])).date():
                raise ValueError("Local day changed during retrieval; rerun to select the latest completed days.")
            capture=dict(kind="recorded-live-api",retrieved_at=retrieved.isoformat(),params=params,api_url=API_URL,response=data)
        text=format_report(capture)
        save_report(output,text)
        if args.record_json:
            with Path(args.record_json).open("x",encoding="utf-8") as f:json.dump(capture,f,indent=2)
        print(f"Report period: {params['start_date']} to {params['end_date']}")
        print(f"Days analyzed: {len(capture['response']['daily']['time'])}")
        print(f"Saved: {output.name}")
        print("Machine effectiveness: Not established.")
        return 0
    except (OSError,ValueError,KeyError,TypeError,ZoneInfoNotFoundError,requests.RequestException) as exc:
        print(f"ERROR: {exc}",file=sys.stderr);return 2


if __name__=="__main__":
    raise SystemExit(main())
