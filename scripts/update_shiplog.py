"""Render the commit stream: public commits by name, private work as counts only.

Everything here is already public. Three sources, none of which needs a token:

- GitHub's contribution calendar gives the total per day (it includes private
  contributions because the profile shares those counts).
- The commit search API gives public commits by this account in any public repository.
- The profile's day view gives the number of private contributions on a given day.

Private repository names and commit messages are never requested, shown or stored.
If GITHUB_TOKEN is set it only raises the search rate limit. Python standard library only.
"""
import argparse
import collections
import datetime as dt
from html import escape, unescape
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_activity import Calendar  # noqa: E402  (the calendar parser and its sanity checks)

USER = 'Farazhaghgoo'
API = 'https://api.github.com'
WEB = 'https://github.com'
WINDOW_DAYS = 90
FEED_PER_REPO = 3        # newest commits shown per public repository
FEED_PRIVATE_WEEKS = 8   # newest weeks of private work shown, as masked rows
MESSAGE_CHARS = 47
RECHECK_DAYS = 7         # older days are final; their private counts are reused from the last snapshot
UA = 'profile-commit-stream-renderer'

BG, BAR, LINE, MUTED, CREAM = '#0B0E14', '#161B24', '#29313C', '#939BA8', '#F3EFE5'
PUBLIC, PRIVATE = '#FF642D', '#C6FF00'
MONO, SANS = 'Consolas,monospace', 'Arial,Helvetica,sans-serif'
# Each project keeps the accent colour of its cover; anything new cycles through the fallback list.
REPO_COLORS = {'hamiYami': '#FF7A5C', 'curseek': '#FF5C7A', 'portfolio': '#FFC857', 'whomst': '#FF642D',
               'financeApp': '#E6FF7A', 'VeloCity': '#90DFFF', 'CVai': '#B8A6FF',
               'EXAMassist': '#7CE0C3', 'vibeassist': '#F29BD4'}
FALLBACK = ['#9DB5FF', '#FF9B5E', '#9DB58F', '#F3EFE5']
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


def fetch(url, headers):
    for attempt in (1, 2, 3):
        try:
            with urlopen(Request(url, headers={'User-Agent': UA, **headers}), timeout=30) as response:
                return response.read().decode('utf-8')
        except HTTPError as error:
            if attempt == 3 or error.code not in (403, 429, 500, 502, 503):
                raise
            time.sleep(20 * attempt)


def api(path):
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
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
    window = [(today - dt.timedelta(days=WINDOW_DAYS - 1 - n)).isoformat() for n in range(WINDOW_DAYS)]

    # 1. Official totals per day.
    parser = Calendar()
    parser.feed(fetch(f'{WEB}/users/{USER}/contributions', {'Accept': 'text/html'}))
    calendar = {d['date']: d['count'] for d in parser.days()}
    if sum(d in calendar for d in window) < WINDOW_DAYS - 2:
        raise ValueError('Calendar does not cover the window; preserving previous image')

    # 2. Public commits by this account, in 30-day slices so no slice can hit the search cap.
    commits = []
    for start in range(0, WINDOW_DAYS, 30):
        chunk = window[start:start + 30]
        query = quote(f'author:{USER} author-date:{chunk[0]}..{chunk[-1]}')
        for page in range(1, 11):
            result = api(f'/search/commits?q={query}&sort=author-date&order=desc&per_page=100&page={page}')
            if result.get('incomplete_results'):
                raise ValueError('Commit search was incomplete; preserving previous image')
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
    commits = [c for c in commits if c['date'] in set(window)]
    public_by_day = collections.Counter(c['date'] for c in commits)

    # 3. Private contributions per day. Only days the public commits do not fully explain are looked up.
    known = {d['date']: d for d in (previous or {}).get('days', [])}
    final_before = (today - dt.timedelta(days=RECHECK_DAYS)).isoformat()
    days, lookups = [], 0
    for day in window:
        total = calendar.get(day, 0)
        if total == 0 or total == public_by_day[day]:
            private = 0
        elif day < final_before and day in known and known[day]['total'] == total:
            private = known[day]['private']
        else:
            private = min(total, private_on(day))
            lookups += 1
            time.sleep(0.4)
        days.append({'date': day, 'total': total, 'private': private})
    total, private = sum(d['total'] for d in days), sum(d['private'] for d in days)
    if previous and previous.get('private', 0) >= 10 and private == 0:
        raise ValueError('Private counts vanished; preserving previous image')

    repos = collections.Counter(c['repo'] for c in commits).most_common(6)
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
    print(f'{len(commits)} public commits found, {lookups} day views read.')
    return {'window_days': WINDOW_DAYS, 'total': total, 'public': total - private, 'private': private,
            'repos': [{'name': n, 'commits': c} for n, c in repos], 'feed': feed, 'days': days}


def clip(s, n):
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def stamp(day, start=None):
    d = dt.date.fromisoformat(day)
    if start and start != day:
        a = dt.date.fromisoformat(start)
        return f'{MONTHS[a.month - 1]} {a.day:02d}–{d.day:02d}' if a.month == d.month else f'{MONTHS[a.month - 1]} {a.day:02d}–{MONTHS[d.month - 1]} {d.day:02d}'
    return f'{MONTHS[d.month - 1]} {d.day:02d}'


def render(data, snapshot):
    W, H = 1200, 664
    css = []

    def t(x, y, s, size=15, color=MUTED, family=MONO, weight=400, extra=''):
        return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" '
                f'font-weight="{weight}"{extra}>{escape(str(s))}</text>')

    def lock(x, y, color, scale=1):
        return (f'<g transform="translate({x},{y}) scale({scale})"><path d="M-4.5 -1V-4.5a4.5 4.5 0 0 1 9 0V-1" fill="none" stroke="{color}" stroke-width="2.2"/>'
                f'<rect x="-7" y="-1.5" width="14" height="11" rx="2.5" fill="{color}"/></g>')

    order = [r['name'] for r in data['repos']] + [r['repo'] for r in data['feed'] if 'repo' in r]

    def color_for(repo):
        return REPO_COLORS.get(repo) or FALLBACK[order.index(repo) % len(FALLBACK)]

    total, public, private, days, feed = data['total'], data['public'], data['private'], data['days'], data['feed']
    body = ''

    # ── Top bar, with a light that keeps travelling along its edge.
    body += (f'<rect width="{W}" height="56" fill="{BAR}"/>'
             '<circle cx="28" cy="28" r="6" fill="#FF642D"/><circle cx="50" cy="28" r="6" fill="#EEBD53"/><circle cx="72" cy="28" r="6" fill="#92B96A"/>'
             + t(100, 34, 'faraz@torino: ~/building', 17)
             + f'<circle class="live" cx="{W - 318}" cy="28" r="5" fill="{PRIVATE}"/>'
             + t(W - 32, 34, 'PUBLIC + PRIVATE / LAST 90 DAYS', 16, CREAM, extra=' text-anchor="end"')
             + f'<rect y="55" width="{W}" height="2" fill="{LINE}"/><rect class="beam" x="-360" y="54" width="360" height="3" fill="url(#beam)"/>')
    css.append('@keyframes live{50%{opacity:.25}}.live{animation:live 1.6s ease-in-out infinite}'
               f'@keyframes beam{{to{{transform:translateX({W + 360}px)}}}}.beam{{animation:beam 5s linear infinite}}')

    # ── Left: the total rolls up like an odometer, then splits into public and private.
    body += t(36, 98, 'SHIPPED / LAST 90 DAYS', 15, extra=' letter-spacing="1"')
    digits, cw, ch, ox, oy = str(total), 68, 104, 30, 112
    body += f'<clipPath id="od"><rect x="{ox}" y="{oy}" width="{len(digits) * cw}" height="{ch}"/></clipPath><g clip-path="url(#od)">'
    for i, digit in enumerate(digits):
        steps = 10 + int(digit)
        strip = ''.join(t(ox + i * cw + cw / 2, oy + 92 + k * ch, k % 10, 118, CREAM, SANS, 900, ' text-anchor="middle"') for k in range(steps + 1))
        css.append(f'@keyframes o{i}{{0%,3%{{transform:translateY(0)}}{20 + i * 5}%,100%{{transform:translateY(-{steps * ch}px)}}}}'
                   f'.o{i}{{transform:translateY(-{steps * ch}px);animation:o{i} 14s cubic-bezier(.16,.84,.3,1) infinite}}')
        body += f'<g class="o{i}">{strip}</g>'
    body += '</g>'
    split = 356 * public / total if total else 356
    body += ('<clipPath id="sp"><rect x="36" y="238" width="356" height="16" rx="8"/></clipPath><g clip-path="url(#sp)">'
             f'<rect x="36" y="238" width="356" height="16" fill="{PRIVATE}"/><rect x="36" y="238" width="{split:.1f}" height="16" fill="{PUBLIC}"/>'
             f'<rect x="{36 + split - 1.5:.1f}" y="238" width="3" height="16" fill="{BG}"/>'
             '<rect class="shine" x="-90" y="238" width="90" height="16" fill="url(#shine)"/></g>')
    css.append('@keyframes shine{0%{transform:translateX(0)}45%,100%{transform:translateX(560px)}}.shine{animation:shine 3.5s ease-in-out infinite}')
    body += (f'<circle cx="43" cy="285" r="6" fill="{PUBLIC}"/>' + t(58, 290, 'PUBLIC', 14)
             + t(34, 330, public, 38, CREAM, SANS, 900)
             + lock(227, 284, PRIVATE) + t(242, 290, 'PRIVATE', 14)
             + t(218, 330, private, 38, CREAM, SANS, 900)
             + f'<path d="M36 348H392" stroke="{LINE}" fill="none"/>')

    # ── Left, lower: where the work went. Private work is one masked line.
    board = [{'name': r['name'], 'count': r['commits']} for r in data['repos']]
    if private:
        board.append({'name': 'private', 'count': private, 'masked': True})
    board = sorted(board, key=lambda r: -r['count'])[:5]
    top = max((r['count'] for r in board), default=1)
    body += t(36, 374, 'WHERE IT WENT', 14, extra=' letter-spacing="1"')
    for i, row in enumerate(board):
        y = 402 + i * 27
        col = PRIVATE if row.get('masked') else color_for(row['name'])
        if row.get('masked'):
            body += lock(43, y - 6, col, 0.9) + t(58, y, 'private', 16, col, weight=700)
        else:
            body += t(36, y, clip(row['name'], 20), 16, col, weight=700)
        body += t(392, y, row['count'], 16, CREAM, weight=700, extra=' text-anchor="end"')
        body += (f'<rect x="36" y="{y + 7}" width="356" height="4" rx="2" fill="#18202B"/><g transform="translate(36,{y + 7})">'
                 f'<rect class="grow" style="animation-delay:{i * 0.18:.2f}s" width="{max(6, round(356 * row["count"] / top))}" height="4" rx="2" fill="{col}"/></g>')
    css.append('@keyframes grow{0%,2%{transform:scaleX(0)}16%,100%{transform:scaleX(1)}}.grow{animation:grow 14s cubic-bezier(.2,.7,.2,1) infinite}')

    # ── Right: the feed never stops scrolling. Public rows carry their message; private rows are masked.
    fx, fy, fw, fh, rh = 432, 112, 732, 400, 40
    body += t(fx, 98, 'LATEST / PER PROJECT', 15, extra=' letter-spacing="1"') + t(fx + fw, 98, f'SNAPSHOT {snapshot}', 13, extra=' text-anchor="end"')
    rows = ''
    for i, row in enumerate(feed + feed):
        y = i * rh
        rows += f'<g transform="translate(0,{y})">'
        if 'private' in row:
            n = row['private']
            rows += lock(10, 17, PRIVATE) + t(28, 26, 'private', 17, PRIVATE, weight=700)
            x, seed = 176, sum(map(ord, row['date']))
            for k in range(4):
                w = 34 + (seed * (k + 3) * 7) % 62
                rows += f'<rect class="mask" style="animation-delay:{(k * 0.35 + i * 0.2) % 2.8:.2f}s" x="{x}" y="14" width="{w}" height="13" rx="4" fill="{PRIVATE}"/>'
                x += w + 8
            rows += t(x + 8, 26, f'{n} contribution{"" if n == 1 else "s"}', 16, CREAM)
        else:
            col = color_for(row['repo'])
            rows += (f'<circle cx="10" cy="20" r="5" fill="{col}"/>' + t(28, 26, clip(row['repo'], 13), 17, col, weight=700)
                     + t(176, 26, clip(row['message'], MESSAGE_CHARS), 17, CREAM))
        rows += t(fw, 26, stamp(row['date'], row.get('from')), 14, extra=' text-anchor="end"') + f'<path d="M0 39.5H{fw}" stroke="#161D28" fill="none"/></g>'
    loop = len(feed) * rh
    css.append(f'@keyframes feed{{to{{transform:translateY(-{loop}px)}}}}.feed{{animation:feed {max(8, loop / 26):.1f}s linear infinite}}'
               '@keyframes mask{0%,100%{opacity:.2}50%{opacity:.5}}.mask{opacity:.3;animation:mask 2.8s ease-in-out infinite}')
    body += (f'<clipPath id="fv"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}"/></clipPath>'
             f'<g clip-path="url(#fv)"><g transform="translate({fx},{fy})"><g class="feed">{rows}</g></g>'
             f'<rect x="{fx}" y="{fy}" width="{fw}" height="34" fill="url(#ft)"/><rect x="{fx}" y="{fy + fh - 44}" width="{fw}" height="44" fill="url(#fb)"/></g>')

    # ── Bottom: one bar per day, public below private, with a scanner sweeping across.
    base, tall, x0, x1 = 632, 62, 36, W - 36
    slot = (x1 - x0) / len(days)
    peak = max((d['total'] for d in days), default=1) or 1
    body += f'<path d="M36 528H{x1}" stroke="{LINE}" fill="none"/>' + t(36, 553, 'DAILY PULSE', 14, extra=' letter-spacing="1"')
    body += (f'<rect x="166" y="543" width="10" height="10" rx="2" fill="{PUBLIC}"/>' + t(182, 553, 'public', 13)
             + f'<rect x="250" y="543" width="10" height="10" rx="2" fill="{PRIVATE}"/>' + t(266, 553, 'private', 13)
             + t(x1, 553, f'{stamp(days[0]["date"])} → {stamp(days[-1]["date"])}', 13, extra=' text-anchor="end"'))
    for i, d in enumerate(days):
        x = x0 + i * slot
        date = dt.date.fromisoformat(d['date'])
        if date.day == 1:
            body += t(round(x, 1), base + 20, MONTHS[date.month - 1], 12)
        if not d['total']:
            body += f'<rect x="{x:.1f}" y="{base - 2}" width="{slot - 3.5:.1f}" height="2" fill="#1B2330"/>'
            continue
        h = max(5, tall * math.sqrt(d['total'] / peak))
        hp = h * d['private'] / d['total']
        bar = f'<rect y="{-(h - hp):.1f}" width="{slot - 3.5:.1f}" height="{h - hp:.1f}" fill="{PUBLIC}"/>' if h - hp > 0.2 else ''
        if hp > 0.2:
            bar += f'<rect y="{-h:.1f}" width="{slot - 3.5:.1f}" height="{hp:.1f}" fill="{PRIVATE}"/>'
        body += (f'<g transform="translate({x:.1f},{base})"><title>{d["date"]}: {d["total"]} contributions, {d["private"]} private</title>'
                 f'<g class="bw" style="animation-delay:{i * 4.2 / len(days):.2f}s">{bar}</g></g>')
    body += f'<rect class="scan" x="-2" y="{base - tall - 6}" width="3" height="{tall + 8}" fill="{CREAM}"/>'
    css.append('@keyframes bw{0%,16%,100%{transform:scaleY(1)}5%{transform:scaleY(1.28)}}.bw{animation:bw 7s ease-in-out infinite}'
               f'@keyframes scan{{0%{{transform:translateX({x0}px);opacity:0}}3%{{opacity:.7}}60%{{transform:translateX({x1}px);opacity:.7}}63%,100%{{transform:translateX({x1}px);opacity:0}}}}'
               '.scan{opacity:0;animation:scan 7s linear infinite}')

    latest = '; '.join(f"{r['date']} {r['repo']}: {r['message']}" for r in feed if 'repo' in r)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
        f'<title id="t">Commit stream: {total} contributions in the last {data["window_days"]} days, {public} public and {private} private</title>'
        f'<desc id="d">Private work is shown as counts only. Latest public commits: {escape(latest)}</desc>'
        '<style>' + ''.join(css) + '@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
        '<defs>'
        f'<linearGradient id="beam"><stop stop-color="{PUBLIC}" stop-opacity="0"/><stop offset=".5" stop-color="{PUBLIC}"/><stop offset="1" stop-color="{PRIVATE}"/></linearGradient>'
        '<linearGradient id="shine"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="ft" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{BG}"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        '</defs>'
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>{body}</g>'
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="15.25" fill="none" stroke="{LINE}" stroke-width="1.5"/></svg>'
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, help='Render from an existing shiplog.json instead of reading GitHub')
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'assets')
    args = p.parse_args()
    target = args.output_dir / 'shiplog.json'
    keys = ('window_days', 'total', 'public', 'private', 'repos', 'feed', 'days')
    previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else None
    if previous and 'days' not in previous:
        previous = None      # snapshot from the older, public-only format
    if args.input:
        stored = json.loads(args.input.read_text(encoding='utf-8'))
        data, snapshot = {k: stored[k] for k in keys}, stored['snapshot']
    else:
        today = dt.datetime.now(dt.timezone.utc).date()
        data, snapshot = collect(today, previous), today.isoformat()
        if previous and all(previous.get(k) == data[k] for k in keys):
            print('Commit stream unchanged; keeping the previous snapshot.')
            return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'shiplog.svg').write_text(render(data, snapshot), encoding='utf-8', newline='\n')
    payload = {'source': [f'{WEB}/users/{USER}/contributions', f'{API}/search/commits', f'{WEB}/{USER}?tab=overview'],
               'snapshot': snapshot,
               'scope': 'Public commits by name; private contributions as daily counts only, as shared on the public profile',
               **data}
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(f'Rendered {data["total"]} contributions: {data["public"]} public, {data["private"]} private; {len(data["feed"])} feed rows.')


if __name__ == '__main__':
    main()
