# 使い方: python -I build.py <ソースdir> <出力:ローカル完全版html> <出力:公開用html>
# ソースdir に body.html / regions.json / coast.json を置く。Open-Meteo から本日分の
# スナップショット（ポイント7日分 + 地図3日分）を取得して埋め込む。
import json, sys, io, urllib.request, datetime, re, time
sd = sys.argv[1]; out_local = sys.argv[2]; out_art = sys.argv[3]
body = io.open(sd + '/body.html', encoding='utf-8').read()
regions = json.load(io.open(sd + '/regions.json', encoding='utf-8'))
coast = io.open(sd + '/coast.json', encoding='utf-8').read()
spots = re.findall(r"lat:([\d.]+),lon:([\d.]+)", body)
lat = ','.join(s[0] for s in spots); lon = ','.join(s[1] for s in spots)
MV='wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height,wind_wave_direction'
WV='wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code,temperature_2m'
def get(u):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(u, timeout=120) as r: return json.load(r)
        except Exception as e:
            wait = 65 if '429' in str(e) else 5
            print('retry', attempt, e, 'wait', wait); time.sleep(wait)
    raise SystemExit('fetch failed: ' + u[:80])
# 埋め込む地図地域（残りはアプリが起動時に取得）。全地域にすると制限待ちで10分ほどかかる。
SNAP_REGIONS = sys.argv[4].split(',') if len(sys.argv) > 4 else ['jp', 'kanto', 'tokai', 'okinawa']
mu=f'https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly={MV}&timezone=Asia%2FTokyo&forecast_days=7'
wu=f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={WV}&wind_speed_unit=ms&timezone=Asia%2FTokyo&forecast_days=7'
snap = {'fetchedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
        'marine': get(mu), 'weather': get(wu), 'map': {}}
def grid_n(r):
    return [int((r['lat'][1]-r['lat'][0])/r['step']+1e-6)+1, int((r['lon'][1]-r['lon'][0])/r['step']+1e-6)+1]
def pack(r, marine, weather):
    n = grid_n(r); times = next(x['hourly']['time'] for x in marine if x.get('hourly'))
    nt = len(times); o = {'id': r['id'], 't': times, 'n': n, 'wh': [], 'wd': [], 'wp': [], 'ws': [], 'wdir': []}
    def put(arr, src, k, mul):
        for t in range(nt):
            v = src[k][t] if src and k in src else None
            arr.append(-1 if v is None else int(round(v*mul)))
    for c in range(n[0]*n[1]):
        m = marine[c].get('hourly') if c < len(marine) else None; w = weather[c].get('hourly') if c < len(weather) else None
        put(o['wh'], m, 'wave_height', 10); put(o['wd'], m, 'wave_direction', 1); put(o['wp'], m, 'wave_period', 10)
        put(o['ws'], w, 'wind_speed_10m', 10); put(o['wdir'], w, 'wind_direction_10m', 1)
    return o
for r in regions:
    if r['id'] not in SNAP_REGIONS: continue
    n = grid_n(r); lats=[]; lons=[]
    for i in range(n[0]):
        for j in range(n[1]):
            lats.append(f"{r['lat'][0]+i*r['step']:.2f}"); lons.append(f"{r['lon'][0]+j*r['step']:.2f}")
    q = f"latitude={','.join(lats)}&longitude={','.join(lons)}&timezone=Asia%2FTokyo&forecast_days=3&temporal_resolution=hourly_3"
    m = get(f'https://marine-api.open-meteo.com/v1/marine?{q}&hourly=wave_height,wave_direction,wave_period')
    w = get(f'https://api.open-meteo.com/v1/forecast?{q}&hourly=wind_speed_10m,wind_direction_10m&wind_speed_unit=ms')
    if isinstance(m, dict): m = [m]
    if isinstance(w, dict): w = [w]
    snap['map'][r['id']] = pack(r, m, w)
    print('map', r['id'], n, len(m), len(w))
# 潮汐スナップショット: 気象庁 潮位表（本日から45日分、使用地点のみ）
TIDE_CODES = sorted(set(re.findall(r"tide:'([A-Z0-9]{2})'", body)))
def parse_tide(txt):
    days = {}
    for ln in txt.split('\n'):
        if len(ln) < 80: continue
        h = [int(ln[i*3:i*3+3]) for i in range(24)]
        d = '20' + ln[72:74] + '-' + ln[74:76] + '-' + ln[76:78]
        def ev(seg):
            out = []
            for k in range(4):
                tm = seg[k*7:k*7+4]; cm = seg[k*7+4:k*7+7]
                if tm.strip() in ('9999', ''): continue
                try: out.append([int(tm[:2])*60 + int(tm[2:4]), int(cm)])
                except ValueError: pass
            return out
        days[d] = {'h': h, 'hi': ev(ln[80:108]), 'lo': ev(ln[108:136])}
    return days
today = datetime.date.today(); last = today + datetime.timedelta(days=45)
years = sorted(set([today.year, last.year]))
snap['tide'] = {}
for code in TIDE_CODES:
    days = {}
    for y in years:
        try:
            with urllib.request.urlopen(f'https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/{y}/{code}.txt', timeout=60) as r:
                days.update(parse_tide(r.read().decode('utf-8', 'replace')))
        except Exception as e:
            print('tide', code, y, 'skip', e)
    snap['tide'][code] = {k: v for k, v in days.items() if str(today - datetime.timedelta(days=1)) <= k <= str(last)}
    print('tide', code, len(snap['tide'][code]), 'days')
js = json.dumps(snap, separators=(',',':'), ensure_ascii=False).replace('</', '<\/')
page = (body.replace('__SNAPSHOT__', js).replace('__COAST__', coast)
            .replace('__REGIONS__', json.dumps(regions, separators=(',',':'), ensure_ascii=False)))
io.open(out_art, 'w', encoding='utf-8').write(page)
local = ('<!DOCTYPE html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
         '<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="theme-color" content="#0b6fb8">\n'
         '<style>[hidden]{display:none!important}</style>\n</head>\n<body>\n' + page + '\n</body>\n</html>\n')
io.open(out_local, 'w', encoding='utf-8').write(local)
print('spots', len(spots), 'bytes', len(page.encode('utf-8')))
