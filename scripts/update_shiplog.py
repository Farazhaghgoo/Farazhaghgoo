"""Render the ship log from public GitHub data: latest commits, 90-day totals and languages.

Python standard library only. No token is required; if GITHUB_TOKEN is set it is used
only to raise the API rate limit. Private repositories are never requested.
"""
import argparse
import datetime as dt
from html import escape
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

USER = 'Farazhaghgoo'
API = 'https://api.github.com'
WINDOW_DAYS = 90
ROWS = 10          # commits shown in the log
PER_REPO = 4       # at most this many per repository, so one busy day does not fill the log
MAX_REPOS = 6      # most recently pushed repositories that are read for commits
MESSAGE_CHARS = 60

BG, BAR, LINE, MUTED, CREAM, ORANGE = '#0B0E14', '#161B24', '#29313C', '#939BA8', '#F3EFE5', '#FF642D'
MONO, SANS = 'Consolas,monospace', 'Arial,Helvetica,sans-serif'
# Each project keeps the accent colour of its cover; anything new cycles through the fallback list.
REPO_COLORS = {'hamiYami': '#FF7A5C', 'curseek': '#FF5C7A', 'portfolio': '#FFC857', 'whomst': '#FF642D',
               'financeApp': '#C6FF00', 'VeloCity': '#90DFFF', 'CVai': '#B8A6FF'}
FALLBACK = ['#7CE0C3', '#F3EFE5', '#FF9B5E', '#9DB58F']
LANG_COLORS = {'TypeScript': '#4C9BE8', 'JavaScript': '#F1E05A', 'CSS': '#B8A6FF', 'HTML': '#FF7A5C',
               'Python': '#7CE0C3', 'PLpgSQL': '#90DFFF', 'Dockerfile': '#939BA8'}
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


def get(path):
    headers = {'User-Agent': 'profile-shiplog-renderer', 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urlopen(Request(API + path, headers=headers), timeout=30) as response:
        return json.load(response)


def collect(now):
    since = now - dt.timedelta(days=WINDOW_DAYS)
    repos = [r for r in get(f'/users/{USER}/repos?per_page=100&sort=pushed')
             if not r['fork'] and not r['private'] and r['name'] != USER]
    if not repos:
        raise ValueError('No public repositories returned; preserving previous image')

    commits, totals = [], {}
    for repo in repos[:MAX_REPOS]:
        name, seen = repo['name'], []
        for page in range(1, 6):
            try:
                batch = get(f'/repos/{USER}/{name}/commits?per_page=100&page={page}')
            except HTTPError as error:
                if error.code == 409:      # empty repository
                    break
                raise
            for c in batch:
                author = c['commit']['author']
                if len(c['parents']) > 1 or (c.get('author') or {}).get('type') == 'Bot' or author['name'].endswith('[bot]'):
                    continue
                when = dt.datetime.fromisoformat(author['date'].replace('Z', '+00:00'))
                seen.append({'date': when.date().isoformat(), 'when': when, 'repo': name,
                             'message': c['commit']['message'].strip().split('\n')[0]})
            if len(batch) < 100 or (seen and seen[-1]['when'] < since):
                break
        recent = sum(1 for c in seen if c['when'] >= since)
        if recent:
            totals[name] = recent
        commits += sorted(seen, key=lambda c: c['when'], reverse=True)[:PER_REPO]
    if not commits:
        raise ValueError('No public commits returned; preserving previous image')
    commits.sort(key=lambda c: c['when'], reverse=True)
    log = [{k: c[k] for k in ('date', 'repo', 'message')} for c in commits[:ROWS]]

    languages = {}
    for repo in repos:
        for lang, size in get(f'/repos/{USER}/{repo["name"]}/languages').items():
            languages[lang] = languages.get(lang, 0) + size
    return {'window_days': WINDOW_DAYS, 'log': log,
            'totals': dict(sorted(totals.items(), key=lambda kv: -kv[1])),
            'languages': dict(sorted(languages.items(), key=lambda kv: -kv[1]))}


def color_for(repo, order):
    return REPO_COLORS.get(repo) or FALLBACK[order.index(repo) % len(FALLBACK)]


def clip(s, n):
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def render(data, snapshot):
    W, H = 1200, 456

    def t(x, y, s, size=15, color=MUTED, family=MONO, weight=400, extra=''):
        return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" '
                f'font-weight="{weight}"{extra}>{escape(str(s))}</text>')

    log, totals, languages = data['log'], data['totals'], data['languages']
    order = list(dict.fromkeys(list(totals) + [c['repo'] for c in log]))
    summary = '; '.join(f"{c['date']} {c['repo']}: {c['message']}" for c in log)
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
         f'<title id="t">Ship log: latest public commits by {USER}</title><desc id="d">{escape(summary)}</desc>'
         '<style>'
         '@keyframes row{0%{opacity:0;transform:translateX(-10px)}2%{opacity:1;transform:none}90%{opacity:1}95%,100%{opacity:0}}'
         '@keyframes grow{0%{transform:scaleX(0)}7%,90%{transform:scaleX(1)}96%,100%{transform:scaleX(0)}}'
         '@keyframes blink{50%{opacity:0}}'
         '.r{animation:row 20s linear infinite backwards}.b{animation:grow 20s cubic-bezier(.2,.7,.2,1) infinite backwards}'
         '.k{animation:blink 1.1s steps(1) infinite}'
         '@media(prefers-reduced-motion:reduce){*{animation:none!important}}'
         '</style>'
         f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>'
         f'<rect width="{W}" height="48" rx="16" fill="{BAR}"/><rect y="24" width="{W}" height="24" fill="{BAR}"/>'
         '<circle cx="25" cy="24" r="5" fill="#FF642D"/><circle cx="45" cy="24" r="5" fill="#EEBD53"/><circle cx="65" cy="24" r="5" fill="#92B96A"/>')
    s += t(92, 30, 'faraz@torino: ~/building', 16) + t(W - 30, 30, 'SHIP LOG / PUBLIC', 15, extra=' text-anchor="end"')

    # Left: the log itself.
    s += t(30, 92, '$', 15, ORANGE) + t(48, 92, 'shiplog --public --latest', 15)
    for i, c in enumerate(log):
        y = 124 + i * 27
        d = dt.date.fromisoformat(c['date'])
        s += (f'<g class="r" style="animation-delay:{0.4 + i * 0.28:.2f}s">'
              + t(30, y, f'{MONTHS[d.month - 1]} {d.day:02d}')
              + t(100, y, clip(c['repo'], 13), 15, color_for(c['repo'], order), weight=700)
              + t(232, y, clip(c['message'], MESSAGE_CHARS), 15, CREAM) + '</g>')
    y = 124 + len(log) * 27
    s += t(30, y, '$', 15, ORANGE) + f'<rect class="k" x="48" y="{y - 14}" width="9" height="17" fill="{CREAM}"/>'
    s += f'<path d="M815 68V396" stroke="{LINE}" fill="none"/>'

    # Right: totals for the window, then languages across all public repositories.
    total = sum(totals.values())
    s += t(840, 92, f'COMMITS / LAST {data["window_days"]} DAYS', 12)
    s += t(838, 142, total, 46, CREAM, SANS, 900)
    s += t(840 + len(str(total)) * 26 + 14, 142, f'ACROSS {len(totals)} REPO{"" if len(totals) == 1 else "S"}', 12)
    shown = list(totals.items())[:5]
    step = 32 if len(shown) >= 5 else 38 if len(shown) == 4 else 44
    peak = max((n for _, n in shown), default=1)
    for i, (repo, n) in enumerate(shown):
        y = 180 + i * step
        col = color_for(repo, order)
        s += t(840, y, clip(repo, 22), 13, col, weight=700) + t(1170, y, n, 13, CREAM, extra=' text-anchor="end"')
        s += f'<rect x="840" y="{y + 9}" width="330" height="6" rx="3" fill="#18202B"/>'
        s += (f'<g transform="translate(840,{y + 9})"><rect class="b" style="animation-delay:{0.6 + i * 0.2:.1f}s" '
              f'width="{max(6, round(330 * n / peak))}" height="6" rx="3" fill="{col}"/></g>')
    if not shown:
        s += t(840, 180, 'Quiet in public lately.', 13) + t(840, 202, 'Private work continues.', 13)

    size = sum(languages.values()) or 1
    s += t(840, 350, 'PUBLIC CODE BY LANGUAGE', 12)
    x = 840.0
    s += '<clipPath id="lc"><rect x="840" y="360" width="330" height="8" rx="4"/></clipPath><g clip-path="url(#lc)">'
    for i, (lang, n) in enumerate(languages.items()):
        w = 330 * n / size
        s += f'<rect x="{x:.1f}" y="360" width="{w + 0.5:.1f}" height="8" fill="{LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])}"/>'
        x += w
    s += '</g>'
    x = 840
    for i, (lang, n) in enumerate(list(languages.items())[:3]):
        label = f'{lang} {100 * n / size:.0f}%'
        s += f'<rect x="{x}" y="383" width="9" height="9" rx="2" fill="{LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])}"/>'
        s += t(x + 15, 392, label, 11)
        x += 15 + round(len(label) * 6.7) + 16

    s += f'<path d="M30 414H{W - 30}" stroke="{LINE}" fill="none"/>'
    s += t(30, 437, f'SNAPSHOT / {snapshot}  ·  PUBLIC REPOSITORIES ONLY', 12)
    s += t(W - 30, 437, 'SOURCE / GITHUB REST API', 12, extra=' text-anchor="end"')
    return s + '</svg>'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, help='Render from an existing shiplog.json instead of calling the API')
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'assets')
    args = p.parse_args()
    target = args.output_dir / 'shiplog.json'
    now = dt.datetime.now(dt.timezone.utc)
    if args.input:
        stored = json.loads(args.input.read_text(encoding='utf-8'))
        data, snapshot = {k: stored[k] for k in ('window_days', 'log', 'totals', 'languages')}, stored['snapshot']
    else:
        data, snapshot = collect(now), now.date().isoformat()
        if target.exists():
            previous = json.loads(target.read_text(encoding='utf-8'))
            if all(previous.get(k) == v for k, v in data.items()):
                print('Ship log unchanged; keeping the previous snapshot.')
                return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'shiplog.svg').write_text(render(data, snapshot), encoding='utf-8')
    payload = {'source': f'{API}/users/{USER}/repos', 'snapshot': snapshot,
               'scope': 'Public repositories only; not total professional activity', **data}
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Rendered {len(data["log"])} commits; {sum(data["totals"].values())} in the last {data["window_days"]} days.')


if __name__ == '__main__':
    main()
