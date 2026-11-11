"""Render the control room: a year of contributions, public by project, private as counts only.

Its numbers are GitHub's own contribution calendar, so the total matches the
"contributions in the last year" figure on the profile. Three public sources, no token needed:

- The contribution calendar gives the total per day, private contributions included
  (the profile shares those counts).
- The commit search API gives public commits by this account in any public repository.
- The profile's day view gives the number of private contributions on a given day.

Private repository names and commit messages are never requested, shown or stored.
If GITHUB_TOKEN is set it only raises the search rate limit. Python standard library only.
"""
import argparse
import collections
import datetime as dt
from html import escape, unescape
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER = 'Farazhaghgoo'
API = 'https://api.github.com'
WEB = 'https://github.com'
FEED_PER_REPO = 3          # newest commits shown per public repository
FEED_PRIVATE_WEEKS = 6     # newest weeks of private work shown, as masked rows
FEED_ROWS = 16             # rows in the scrolling feed, newest first
RECHECK_DAYS = 7           # older days are final; their private counts are reused from the last snapshot
LIGHT_DAYS = 14            # a project's status light is on if it had work this recently
UA = 'profile-control-room-renderer'

BG, BAR, PANEL, LINE, MUTED, CREAM = '#0B0E14', '#161B24', '#111722', '#29313C', '#939BA8', '#F3EFE5'
PUBLIC, PRIVATE, AMBER, TEAL = '#FF642D', '#C6FF00', '#FFC857', '#7CE0C3'
MONO = 'Consolas,monospace'
# Each project keeps the accent colour of its cover; anything new cycles through the fallback list.
REPO_COLORS = {'hamiYami': '#FF7A5C', 'EXAMassist': '#7CE0C3', 'vibeassist': '#F29BD4', 'curseek': '#FF5C7A',
               'portfolio': '#FFC857', 'whomst': '#FF642D', 'financeApp': '#E6FF7A', 'VeloCity': '#90DFFF', 'CVai': '#B8A6FF'}
FALLBACK = ['#9DB5FF', '#FF9B5E', '#9DB58F', '#F3EFE5']
# Product names for repositories whose name differs from what the profile calls them.
DISPLAY = {'EXAMassist': 'UniExamer', 'vibeassist': 'VibeAssist', 'hamiYami': 'HamiYami'}
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
# Heat ramps for GitHub's activity levels 1–4: days that were mostly public, and mostly private.
RAMP_PUBLIC = ['#5A2A1A', '#9C3F1F', '#E0552A', '#FF8A55']
RAMP_PRIVATE = ['#3C4A12', '#6E8A0F', '#A8D400', '#D8FF5A']


# ───────────────────────── data ─────────────────────────

class Calendar(HTMLParser):
    """GitHub's public contribution calendar: date, level and count for every day of the last year."""

    def __init__(self):
        super().__init__()
        self.cells, self.tips, self.tip = {}, {}, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date'):
            level = int(a['data-level'])
            if not 0 <= level <= 4:
                raise ValueError('Unexpected activity level')
            self.cells[a['id']] = {'date': dt.date.fromisoformat(a['data-date']).isoformat(), 'level': level}
        elif tag == 'tool-tip' and a.get('for'):
            self.tip = a['for']
            self.tips[self.tip] = ''

    def handle_data(self, data):
        if self.tip is not None:
            self.tips[self.tip] += data

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.tip = None

    def days(self):
        result = []
        for key, cell in self.cells.items():
            match = re.match(r'(No|[\d,]+) contributions? on ', self.tips.get(key, '').strip())
            if not match:
                raise ValueError('GitHub tooltip format changed; preserving previous image')
            count = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
            if (count == 0) != (cell['level'] == 0):
                raise ValueError('Calendar level/count mismatch')
            result.append({**cell, 'count': count})
        result.sort(key=lambda d: d['date'])
        if not 350 <= len(result) <= 380:
            raise ValueError('Incomplete public calendar; preserving previous image')
        dates = [dt.date.fromisoformat(d['date']) for d in result]
        if len(set(dates)) != len(dates) or (dates[-1] - dates[0]).days != len(dates) - 1:
            raise ValueError('Non-contiguous calendar; preserving previous image')
        return result


def fetch(url, headers):
    for attempt in (1, 2, 3, 4):
        try:
            with urlopen(Request(url, headers={'User-Agent': UA, **headers}), timeout=30) as response:
                return response.read().decode('utf-8')
        except HTTPError as error:
            if attempt == 4 or error.code not in (403, 429, 500, 502, 503):
                raise
            time.sleep(25 * attempt)


def api(path):
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    else:
        time.sleep(6.5)      # the unauthenticated search limit is 10 requests a minute
    return json.loads(fetch(API + path, headers))


def private_on(day):
    """Private contributions on one day, read from the profile's public day view."""
    page = fetch(f'{WEB}/{USER}?tab=overview&from={day}&to={day}', {'Accept': 'text/html', 'X-Requested-With': 'XMLHttpRequest'})
    text = unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', page)))
    if 'Contribution activity' not in text:
        raise ValueError('Activity view changed; preserving previous image')
    match = re.search(r'([\d,]+) contributions? in private repositor', text)
    return int(match[1].replace(',', '')) if match else 0


def collect(today, previous):
    # 1. Official totals per day: the profile's own contribution calendar.
    parser = Calendar()
    parser.feed(fetch(f'{WEB}/users/{USER}/contributions', {'Accept': 'text/html'}))
    calendar = parser.days()
    window = [d['date'] for d in calendar]

    # 2. Public commits by this account, in 30-day slices so no slice can hit the search cap.
    commits = []
    for start in range(0, len(window), 30):
        chunk = window[start:start + 30]
        query = quote(f'author:{USER} author-date:{chunk[0]}..{chunk[-1]}')
        for page in range(1, 11):
            for attempt in range(4):      # search sometimes times out and says so; ask again
                result = api(f'/search/commits?q={query}&sort=author-date&order=desc&per_page=100&page={page}')
                if not result.get('incomplete_results'):
                    break
                time.sleep(10)
            else:
                raise ValueError('Commit search stayed incomplete; preserving previous image')
            for item in result['items']:
                repo = item['repository']
                # Never keep anything from a private repository, and leave this profile repository out.
                if repo.get('private') or repo['full_name'] == f'{USER}/{USER}':
                    continue
                when = item['commit']['author']['date']
                commits.append({'date': when[:10], 'when': dt.datetime.fromisoformat(re.sub(r'\.\d+', '', when).replace('Z', '+00:00')),
                                'repo': repo['name'], 'merge': len(item['parents']) > 1,
                                'message': item['commit']['message'].strip().split('\n')[0]})
            if len(result['items']) < 100:
                break
    inside = set(window)
    commits = [c for c in commits if c['date'] in inside]
    public_by_day = collections.Counter(c['date'] for c in commits)

    # 3. Private contributions per day. Only days the public commits do not fully explain are looked up.
    known = {d['date']: d for d in (previous or {}).get('days', [])}
    final_before = (today - dt.timedelta(days=RECHECK_DAYS)).isoformat()
    days, lookups = [], 0
    for cell in calendar:
        day, total = cell['date'], cell['count']
        if total == 0 or total == public_by_day[day]:
            private = 0
        elif day < final_before and day in known and known[day]['total'] == total:
            private = known[day]['private']
        else:
            private = min(total, private_on(day))
            lookups += 1
            time.sleep(0.4)
        days.append({'date': day, 'level': cell['level'], 'total': total, 'private': private})
    total, private = sum(d['total'] for d in days), sum(d['private'] for d in days)
    if previous and previous.get('private', 0) >= 10 and private == 0:
        raise ValueError('Private counts vanished; preserving previous image')

    repos = collections.Counter(c['repo'] for c in commits).most_common(6)
    last = {}
    for c in commits:
        last[c['repo']] = max(last.get(c['repo'], ''), c['date'])
    feed, shown = [], collections.Counter()
    for c in sorted(commits, key=lambda c: c['when'], reverse=True):
        if not c['merge'] and shown[c['repo']] < FEED_PER_REPO:
            shown[c['repo']] += 1
            feed.append({'date': c['date'], 'repo': c['repo'], 'message': c['message']})
    # Private work is grouped by week (Monday to Sunday): one masked row per week that had any.
    weeks = {}
    for d in days:
        if d['private']:
            date = dt.date.fromisoformat(d['date'])
            week = weeks.setdefault((date - dt.timedelta(days=date.weekday())).isoformat(), {'from': d['date'], 'private': 0})
            week['date'] = d['date']
            week['private'] += d['private']
    feed += [weeks[k] for k in sorted(weeks)][-FEED_PRIVATE_WEEKS:]
    feed.sort(key=lambda r: (r['date'], 'private' not in r), reverse=True)
    feed = feed[:FEED_ROWS]

    streak = run = 0
    for d in days:
        run = run + 1 if d['total'] else 0
        streak = max(streak, run)
    best = max(days, key=lambda d: (d['total'], d['date']))
    print(f'{len(commits)} public commits found, {lookups} day views read.')
    return {'from': window[0], 'to': window[-1], 'total': total, 'public': total - private, 'private': private,
            'active': sum(1 for d in days if d['total']), 'streak': streak, 'best': {'date': best['date'], 'total': best['total']},
            'repos': [{'name': n, 'commits': c, 'last': last[n]} for n, c in repos], 'feed': feed, 'days': days}


# ───────────────────────── drawing ─────────────────────────

SEGMENTS = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd',
            '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}
CYCLE = 14          # seconds: the readouts boot, count up, hold, blink off and start again
BOOT = (4, 24)      # percent of the cycle in which the readouts count up
HOLD_END = 95       # percent of the cycle after which the readouts blink off


def clip(s, n):
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def stamp(day, start=None):
    d = dt.date.fromisoformat(day)
    if start and start != day:
        a = dt.date.fromisoformat(start)
        return f'{MONTHS[a.month - 1]} {a.day:02d}–{d.day:02d}' if a.month == d.month else f'{MONTHS[a.month - 1]} {a.day:02d}–{MONTHS[d.month - 1]} {d.day:02d}'
    return f'{MONTHS[d.month - 1]} {d.day:02d}'


def segment_shapes(w, h, t):
    """The seven segments of one digit in a w x h box, as point lists."""
    g, r, m = t * 0.18, t / 2, h / 2

    def hor(cy):
        x1, x2 = r + g, w - r - g
        return [(x1, cy), (x1 + r, cy - r), (x2 - r, cy - r), (x2, cy), (x2 - r, cy + r), (x1 + r, cy + r)]

    def ver(cx, y1, y2):
        return [(cx, y1), (cx + r, y1 + r), (cx + r, y2 - r), (cx, y2), (cx - r, y2 - r), (cx - r, y1 + r)]

    return {'a': hor(r), 'g': hor(m), 'd': hor(h - r), 'f': ver(r, r + g, m - g), 'b': ver(w - r, r + g, m - g),
            'e': ver(r, m + g, h - r - g), 'c': ver(w - r, m + g, h - r - g)}


def digits_width(n, h):
    return n * h * 0.56 + (n - 1) * h * 0.16


def seven_seg(uid, x, y, value, places, h, color, css):
    """A seven-segment readout. Each digit counts up from 0 to its value while the panel boots."""
    s = str(value).rjust(places)
    w, t, gap = h * 0.56, h * 0.12, h * 0.16
    shapes = segment_shapes(w, h, t)

    def path(letters, ox):
        return ''.join('M' + 'L'.join(f'{px + ox:.1f} {py:.1f}' for px, py in shapes[c]) + 'Z' for c in letters)

    ghosts, lit = '', ''
    start, end = BOOT
    for i, ch in enumerate(s):
        ox = i * (w + gap)
        ghosts += path('abcdefg', ox)
        if ch == ' ':
            continue
        final = int(ch)
        for k in range(final + 1):
            name = f'{uid}{i}x{k}'
            a = start + (end - start) * k / (final + 1)
            b = start + (end - start) * (k + 1) / (final + 1)
            if k == final:
                css.append(f'@keyframes {name}{{0%,{a:.2f}%{{opacity:0}}{a + .01:.2f}%,{HOLD_END}%{{opacity:1}}{HOLD_END + .01}%,100%{{opacity:0}}}}'
                           f'.{name}{{animation:{name} {CYCLE}s linear infinite}}')
            else:
                css.append(f'@keyframes {name}{{0%,{a:.2f}%{{opacity:0}}{a + .01:.2f}%,{b:.2f}%{{opacity:1}}{b + .01:.2f}%,100%{{opacity:0}}}}'
                           f'.{name}{{opacity:0;animation:{name} {CYCLE}s linear infinite}}')
            lit += f'<path class="{name}" d="{path(SEGMENTS[str(k)], ox)}"/>'
    return (f'<g transform="translate({x:.1f},{y:.1f}) skewX(-6)"><path d="{ghosts}" fill="{color}" fill-opacity=".07"/>'
            f'<g fill="{color}" filter="url(#glow)">{lit}</g></g>')


def render(data, snapshot):
    W, H = 1200, 900
    css = []

    def t(x, y, s, size=20, color=MUTED, weight=400, extra=''):
        return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{MONO}" font-size="{size}" '
                f'font-weight="{weight}"{extra}>{escape(str(s))}</text>')

    def lock(x, y, color, scale=1.0):
        return (f'<g transform="translate({x},{y}) scale({scale})"><path d="M-4.5 -1V-4.5a4.5 4.5 0 0 1 9 0V-1" fill="none" stroke="{color}" stroke-width="2.2"/>'
                f'<rect x="-7" y="-1.5" width="14" height="11" rx="2.5" fill="{color}"/></g>')

    def panel(x, y, w, h, label, color=MUTED):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
        for sx, sy in ((x + 12, y + 12), (x + w - 12, y + 12), (x + 12, y + h - 12), (x + w - 12, y + h - 12)):
            s += f'<circle cx="{sx}" cy="{sy}" r="3" fill="{LINE}"/>'
        return s + t(x + 28, y + 40, label, 20, color, extra=' letter-spacing="2"')

    order = list(dict.fromkeys([r['name'] for r in data['repos']] + [r['repo'] for r in data['feed'] if 'repo' in r]))

    def color_for(repo):
        return REPO_COLORS.get(repo) or FALLBACK[order.index(repo) % len(FALLBACK)]

    def name_of(repo):
        return DISPLAY.get(repo, repo)

    total, public, private, days, feed = data['total'], data['public'], data['private'], data['days'], data['feed']
    today = dt.date.fromisoformat(snapshot)
    body = ''

    # ── Header, with a light running along its lower edge.
    body += (f'<rect width="{W}" height="64" fill="{BAR}"/>'
             + t(28, 42, 'CONTRIBUTIONS / LAST 12 MONTHS', 24, CREAM, 700, ' letter-spacing="1"')
             + t(W - 140, 41, f'UPDATED {stamp(snapshot)}', 20, extra=' text-anchor="end"')
             + f'<circle class="led" cx="{W - 112}" cy="34" r="7" fill="{PRIVATE}"/>'
             + t(W - 96, 41, 'LIVE', 22, PRIVATE, 700)
             + f'<rect y="63" width="{W}" height="2" fill="{LINE}"/><rect class="beam" x="-360" y="62" width="360" height="3" fill="url(#beam)"/>')
    css.append(f'@keyframes beam{{to{{transform:translateX({W + 360}px)}}}}.beam{{animation:beam 5s linear infinite}}'
               '@keyframes led{50%{opacity:.25}}.led{animation:led 1.6s ease-in-out infinite}')

    # ── Panel 1: the year's total, and the public / private split, on seven-segment displays.
    body += panel(24, 84, 580, 260, 'TOTAL', CREAM)
    n = max(3, len(str(total)))
    big = min(160, 330 / (0.72 * n - 0.16))
    body += seven_seg('t', 70, 314 - big, total, n, big, AMBER, css)
    n = max(3, len(str(public)), len(str(private)))
    small = min(62, 140 / (0.72 * n - 0.16))
    body += (t(430, 124, 'PUBLIC', 20, PUBLIC, extra=' letter-spacing="2"') + seven_seg('p', 440, 140, public, n, small, PUBLIC, css)
             + lock(438, 237, PRIVATE) + t(456, 244, 'PRIVATE', 20, PRIVATE, extra=' letter-spacing="2"')
             + seven_seg('q', 440, 258, private, n, small, PRIVATE, css))

    # ── Panel 2: a gauge for active days, and a status light per project.
    body += panel(616, 84, 560, 260, 'ACTIVE DAYS', TEAL)
    cx, cy, R = 752, 268, 100
    frac = data['active'] / len(days)
    px, py = cx - R * math.cos(math.pi * frac), cy - R * math.sin(math.pi * frac)
    body += f'<path d="M{cx - R} {cy}A{R} {R} 0 0 1 {cx + R} {cy}" fill="none" stroke="#1D2531" stroke-width="18"/>'
    body += f'<path class="arc" d="M{cx - R} {cy}A{R} {R} 0 0 1 {px:.1f} {py:.1f}" pathLength="1" stroke-dasharray="1" fill="none" stroke="{TEAL}" stroke-width="18"/>'
    for k in range(11):
        a = math.pi * k / 10
        r1, r2 = R + 16, R + (28 if k % 5 == 0 else 22)
        body += (f'<path d="M{cx - r1 * math.cos(a):.1f} {cy - r1 * math.sin(a):.1f}L{cx - r2 * math.cos(a):.1f} {cy - r2 * math.sin(a):.1f}" '
                 f'stroke="{MUTED}" stroke-width="{2.5 if k % 5 == 0 else 1.5}"/>')
    turn = 180 * frac
    body += (f'<g transform="translate({cx},{cy})"><g class="needle"><path d="M0 -4L-{R - 10} 0L0 4Z" fill="{CREAM}"/></g>'
             f'<circle r="10" fill="{CREAM}"/><circle r="4" fill="{PANEL}"/></g>')
    places = len(str(len(days)))
    body += seven_seg('a', cx - digits_width(places, 40) / 2 - 24, 286, data['active'], places, 40, TEAL, css)
    body += t(cx + 38, 322, f'/{len(days)}', 22)
    css.append(f'@keyframes needle{{0%,{BOOT[0]}%{{transform:rotate(0deg)}}{BOOT[1]}%,{HOLD_END}%{{transform:rotate({turn:.1f}deg)}}100%{{transform:rotate(0deg)}}}}'
               f'.needle{{transform:rotate({turn:.1f}deg);animation:needle {CYCLE}s cubic-bezier(.3,1.35,.5,1) infinite}}'
               f'@keyframes arc{{0%,{BOOT[0]}%{{stroke-dashoffset:1}}{BOOT[1]}%,{HOLD_END}%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:1}}}}'
               f'.arc{{animation:arc {CYCLE}s ease-out infinite}}')

    rows = [(name_of(r['name']).upper(), r['commits'], color_for(r['name']), r['last'], False) for r in data['repos'][:3]]
    if private:
        rows.append(('PRIVATE', private, PRIVATE, max(d['date'] for d in days if d['private']), True))
    rows.sort(key=lambda r: -r[1])
    body += t(904, 124, 'PROJECTS', 20, extra=' letter-spacing="2"')
    for i, (name, count, col, seen, masked) in enumerate(rows[:4]):
        y = 168 + i * 46
        if (today - dt.date.fromisoformat(seen)).days <= LIGHT_DAYS:
            body += (f'<circle class="led" style="animation-delay:{i * 0.3:.1f}s" cx="914" cy="{y - 7}" r="9" fill="{col}"/>'
                     f'<circle cx="914" cy="{y - 7}" r="14" fill="none" stroke="{col}" stroke-opacity=".35" stroke-width="2"/>')
        else:
            body += f'<circle cx="914" cy="{y - 7}" r="9" fill="#232A35" stroke="{col}" stroke-opacity=".45" stroke-width="1.5"/>'
        body += (lock(944, y - 9, col, 1.05) + t(960, y, name, 22, col, 700)) if masked else t(938, y, clip(name, 11), 22, col, 700)
        body += t(1152, y, count, 22, CREAM, 700, ' text-anchor="end"')

    # ── Panel 3: every day of the year, as on the profile's own calendar, coloured by who saw the work.
    body += panel(24, 360, 1152, 250, 'EVERY DAY')
    best = data['best']
    body += (t(250, 400, f'STREAK {data["streak"]}', 20, CREAM) + t(440, 400, f'BEST {stamp(best["date"])} · {best["total"]}', 20, CREAM)
             + f'<rect x="886" y="386" width="16" height="16" rx="3" fill="{RAMP_PUBLIC[2]}"/>' + t(910, 401, 'PUBLIC', 20)
             + f'<rect x="1020" y="386" width="16" height="16" rx="3" fill="{RAMP_PRIVATE[2]}"/>' + t(1044, 401, 'PRIVATE', 20))
    first = dt.date.fromisoformat(days[0]['date'])
    offset = (first.weekday() + 1) % 7          # GitHub's calendar rows start on Sunday
    weeks = (offset + len(days) + 6) // 7
    pitch = min(20.6, 1096 / weeks)
    gx, gy = 52 + (1096 - weeks * pitch) / 2, 448
    cell = pitch - 4
    grid, labelled = '', -9
    for week in range(weeks):
        col = ''
        for row in range(7):
            i = week * 7 + row - offset
            if not 0 <= i < len(days):
                continue
            d = days[i]
            date = dt.date.fromisoformat(d['date'])
            if date.day == 1 and week - labelled >= 3 and week < weeks - 1:
                body += t(round(gx + week * pitch, 1), gy - 12, MONTHS[date.month - 1], 18)
                labelled = week
            if d['level'] == 0:
                fill = '#161D28'
            else:
                ramp = RAMP_PRIVATE if d['private'] * 2 >= d['total'] else RAMP_PUBLIC
                fill = ramp[d['level'] - 1]
            col += (f'<rect x="{gx + week * pitch:.1f}" y="{gy + row * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3" fill="{fill}">'
                    f'<title>{d["date"]}: {d["total"]} contributions, {d["private"]} private</title></rect>')
        grid += f'<g class="wk" style="animation-delay:{week * 0.06:.2f}s">{col}</g>'
    body += grid
    i = len(days) - 1 + offset
    body += (f'<rect class="today" x="{gx + (i // 7) * pitch - 2:.1f}" y="{gy + (i % 7) * pitch - 2:.1f}" width="{cell + 4:.1f}" height="{cell + 4:.1f}" '
             f'rx="4" fill="none" stroke="{CREAM}" stroke-width="2"/>')
    body += f'<rect class="scan" x="-3" y="{gy - 6}" width="4" height="{7 * pitch + 8:.1f}" rx="2" fill="{CREAM}"/>'
    span = (gx, gx + weeks * pitch)
    css.append('@keyframes wk{0%,12%,100%{opacity:1}5%{opacity:.45}}.wk{animation:wk 8s ease-in-out infinite}'
               '@keyframes today{50%{opacity:.2}}.today{animation:today 1.4s ease-in-out infinite}'
               f'@keyframes scan{{0%{{transform:translateX({span[0]:.0f}px);opacity:0}}3%{{opacity:.8}}55%{{transform:translateX({span[1]:.0f}px);opacity:.8}}58%,100%{{transform:translateX({span[1]:.0f}px);opacity:0}}}}'
               '.scan{opacity:0;animation:scan 8s linear infinite}')

    # ── Panel 4: the latest work, scrolling. Public commits carry their message; private weeks are masked.
    body += panel(24, 626, 1152, 250, 'LATEST')
    body += t(1148, 666, 'PRIVATE WORK SHOWN AS COUNTS ONLY', 18, extra=' text-anchor="end"')
    fx, fy, fw, fh, rh = 52, 684, 1096, 176, 46
    rows_svg = ''
    for i, row in enumerate(feed + feed):
        rows_svg += f'<g transform="translate(0,{i * rh})">'
        if 'private' in row:
            n = row['private']
            rows_svg += lock(12, 20, PRIVATE, 1.15) + t(32, 30, 'PRIVATE', 22, PRIVATE, 700)
            x, seed = 230, sum(map(ord, row['date']))
            for k in range(4):
                w = 60 + (seed * (k + 3) * 7) % 110
                rows_svg += f'<rect class="mask" style="animation-delay:{(k * 0.35 + i * 0.2) % 2.8:.2f}s" x="{x}" y="16" width="{w}" height="16" rx="5" fill="{PRIVATE}"/>'
                x += w + 10
            rows_svg += t(x + 12, 30, f'{n} contribution{"" if n == 1 else "s"}', 22, CREAM)
        else:
            col = color_for(row['repo'])
            rows_svg += (f'<circle cx="12" cy="23" r="7" fill="{col}"/>' + t(32, 30, clip(name_of(row['repo']), 12), 22, col, 700)
                         + t(230, 30, clip(row['message'], 58), 22, CREAM))
        rows_svg += t(fw, 30, stamp(row['date'], row.get('from')), 20, extra=' text-anchor="end"')
        rows_svg += f'<path d="M0 45.5H{fw}" stroke="#1A222E" fill="none"/></g>'
    loop = len(feed) * rh
    css.append(f'@keyframes feed{{to{{transform:translateY(-{loop}px)}}}}.feed{{animation:feed {max(10, loop / 22):.1f}s linear infinite}}'
               '@keyframes mask{0%,100%{opacity:.2}50%{opacity:.5}}.mask{opacity:.3;animation:mask 2.8s ease-in-out infinite}')
    body += (f'<clipPath id="fv"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}"/></clipPath>'
             f'<g clip-path="url(#fv)"><g transform="translate({fx},{fy})"><g class="feed">{rows_svg}</g></g>'
             f'<rect x="{fx}" y="{fy}" width="{fw}" height="26" fill="url(#ft)"/><rect x="{fx}" y="{fy + fh - 40}" width="{fw}" height="40" fill="url(#fb)"/></g>')

    latest = '; '.join(f"{r['date']} {name_of(r['repo'])}: {r['message']}" for r in feed if 'repo' in r)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
        f'<title id="t">Control room: {total} contributions in the last year, {public} public and {private} private, on {data["active"]} active days</title>'
        f'<desc id="d">Longest streak {data["streak"]} days; busiest day {best["date"]} with {best["total"]}. Private work is shown as counts only. Projects: '
        + escape(', '.join(f'{r[0].title()} {r[1]}' for r in rows)) + f'. Latest public commits: {escape(latest)}</desc>'
        '<style>' + ''.join(css) + '@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
        '<defs>'
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.5" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<linearGradient id="beam"><stop stop-color="{PUBLIC}" stop-opacity="0"/><stop offset=".5" stop-color="{PUBLIC}"/><stop offset="1" stop-color="{PRIVATE}"/></linearGradient>'
        f'<linearGradient id="ft" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{PANEL}"/><stop offset="1" stop-color="{PANEL}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{PANEL}" stop-opacity="0"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        '</defs>'
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>{body}</g>'
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="15.25" fill="none" stroke="{LINE}" stroke-width="1.5"/></svg>'
    )


# ───────────────────────── entry point ─────────────────────────

KEYS = ('from', 'to', 'total', 'public', 'private', 'active', 'streak', 'best', 'repos', 'feed', 'days')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, help='Render from an existing contributions.json instead of reading GitHub')
    p.add_argument('--seed', type=Path, help='An older snapshot whose private counts can be reused')
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'assets')
    args = p.parse_args()
    target = args.output_dir / 'contributions.json'
    previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else None
    if args.seed:
        previous = json.loads(args.seed.read_text(encoding='utf-8'))
    if args.input:
        stored = json.loads(args.input.read_text(encoding='utf-8'))
        data, snapshot = {k: stored[k] for k in KEYS}, stored['snapshot']
    else:
        today = dt.datetime.now(dt.timezone.utc).date()
        data, snapshot = collect(today, previous), today.isoformat()
        if previous and all(previous.get(k) == data[k] for k in KEYS) and previous.get('snapshot') == snapshot:
            print('Control room unchanged; keeping the previous snapshot.')
            return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'contributions.svg').write_text(render(data, snapshot), encoding='utf-8', newline='\n')
    payload = {'source': [f'{WEB}/users/{USER}/contributions', f'{API}/search/commits', f'{WEB}/{USER}?tab=overview'],
               'snapshot': snapshot,
               'scope': 'GitHub contribution calendar totals; public commits by name; private contributions as daily counts only, as shared on the public profile',
               **data}
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(f'Rendered {data["total"]} contributions: {data["public"]} public, {data["private"]} private, {data["active"]} active days.')


if __name__ == '__main__':
    main()
