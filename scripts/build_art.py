"""Rebuild the hand-designed profile artwork: the HamiYami feature card, the curseek and
portfolio covers, the project marquee and the section labels.

Python standard library only. Run it after editing a design below:

    python3 scripts/build_art.py

The phone in the HamiYami card shows scripts/source/hamiyami-phone.jpg, a 320 x 2475 crop of
the public demo's mobile home page. To replace it, keep that size or update `iw, ih` in hamiyami().
"""
import base64
import random
import sys
from collections import deque
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'assets'
PHONE = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'source' / 'hamiyami-phone.jpg'

BG, PANEL, LINE, MUTED, CREAM = '#0B0E14', '#111722', '#29313C', '#939BA8', '#F3EFE5'
INSET, ORANGE, LIME = '#0A0F18', '#FF642D', '#C6FF00'
MONO, SANS = 'Consolas,monospace', 'Arial,Helvetica,sans-serif'
RM = '@media(prefers-reduced-motion:reduce){*{animation:none!important}}'


def text(x, y, s, fill=MUTED, size=12, family=MONO, weight=400, ls=0, extra=''):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{ls}"{extra}>{escape(s)}</text>')


def card(num, title, tagline, accent, css, art, desc='Original conceptual project artwork; source repository linked in README.'):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="580" height="260" viewBox="0 0 580 260" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)} — {escape(tagline)}</title><desc id="d">{escape(desc)}</desc>'
        f'<style>{css}{RM}</style>'
        f'<rect x="0" y="0" width="580" height="260" rx="16" fill="{BG}"/>'
        f'<rect x="1" y="1" width="578" height="258" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        + text(23, 33, f'{num} / PUBLIC REPOSITORY')
        + text(23, 103, title, CREAM, 46, SANS, 900, -1.15)
        + text(24, 138, tagline, accent)
        + art
        + f'<path d="M24 215L556 215" stroke="{LINE}" stroke-width="1" fill="none"/>'
        + text(24, 242, 'VIEW SOURCE')
        + text(532, 245, '↗', accent, 22, SANS, 400, -0.55)
        + '</svg>'
    )


# ───────────────────────── curseek: a real generated maze, one round per loop ─────────────────────────

COLS, ROWS, CELL, OX, OY = 10, 7, 20, 352, 52


def build_maze(seed, extra=6):
    rnd = random.Random(seed)
    passages, seen, stack = set(), {(0, 0)}, [(0, 0)]
    while stack:
        x, y = stack[-1]
        nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= x + dx < COLS and 0 <= y + dy < ROWS and (x + dx, y + dy) not in seen]
        if not nb:
            stack.pop()
            continue
        n = rnd.choice(nb)
        passages.add(frozenset(((x, y), n)))
        seen.add(n)
        stack.append(n)
    cand = [frozenset(((x, y), (x + 1, y))) for x in range(COLS - 1) for y in range(ROWS)]
    cand += [frozenset(((x, y), (x, y + 1))) for x in range(COLS) for y in range(ROWS - 1)]
    cand = sorted((c for c in cand if c not in passages), key=lambda c: sorted(c))
    rnd.shuffle(cand)
    return passages | set(cand[:extra])


def neighbours(p, cell):
    x, y = cell
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (x + dx, y + dy)
        if frozenset((cell, n)) in p:
            yield n


def bfs(p, a, b):
    prev, q = {a: None}, deque([a])
    while q:
        c = q.popleft()
        if c == b:
            break
        for n in neighbours(p, c):
            if n not in prev:
                prev[n] = c
                q.append(n)
    path, c = [], b
    while c is not None:
        path.append(c)
        c = prev[c]
    return path[::-1]


def centre(c):
    return OX + c[0] * CELL + CELL // 2, OY + c[1] * CELL + CELL // 2


# Round timeline, in percent of one loop.
REVEAL_END, DARK, HIDE_START, HIDE_END, SEEK_START, CATCH, GONE = 12, 18, 5, 72, 24, 90, 96


def pos_at(path, t, t0, t1):
    """Cell-space position along a path at time t (constant speed between t0 and t1)."""
    if t <= t0:
        return path[0]
    if t >= t1:
        return path[-1]
    f = (t - t0) / (t1 - t0) * (len(path) - 1)
    i = int(f)
    a, b = path[i], path[min(i + 1, len(path) - 1)]
    return a[0] + (b[0] - a[0]) * (f - i), a[1] + (b[1] - a[1]) * (f - i)


def pick_round():
    """Find a maze where the hider ends in a dead end and the seeker only arrives at the very end."""
    cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    best = None
    for seed in range(1, 400):
        p = build_maze(seed)
        dead = [c for c in cells if len(list(neighbours(p, c))) == 1]
        rnd = random.Random(seed * 7)
        for _ in range(40):
            h0, h1, s0 = rnd.choice(cells), rnd.choice(dead), rnd.choice(cells)
            hp, sp = bfs(p, h0, h1), bfs(p, s0, h1)
            if not (13 <= len(hp) <= 20 and 16 <= len(sp) <= 26):
                continue
            if abs(h0[0] - s0[0]) + abs(h0[1] - s0[1]) < 6:
                continue
            gap = min(
                abs(a[0] - b[0]) + abs(a[1] - b[1])
                for t in range(0, CATCH - 6)
                for a, b in [(pos_at(hp, t, HIDE_START, HIDE_END), pos_at(sp, t, SEEK_START, CATCH))]
            )
            if gap < 2.2:
                continue
            # Prefer a round that uses the whole board.
            spread = len({c[0] for c in hp + sp}) + len({c[1] for c in hp + sp})
            score = spread * 10 + len(hp) + len(sp)
            if best is None or score > best[0]:
                best = (score, p, hp, sp, seed)
    return best[1:]


def move_frames(name, path, t0, t1):
    n = len(path) - 1
    rows = []
    x, y = centre(path[0])
    if t0 > 0:
        rows.append(f'0%{{transform:translate({x}px,{y}px)}}')
    for i, c in enumerate(path):
        x, y = centre(c)
        rows.append(f'{t0 + (t1 - t0) * i / n:.2f}%{{transform:translate({x}px,{y}px)}}')
    rows.append(f'100%{{transform:translate({x}px,{y}px)}}')
    return f'@keyframes {name}{{' + ''.join(rows) + '}'


def curseek():
    p, hp, sp, seed = pick_round()
    rose, gold, violet = '#FF5C7A', '#FFC857', '#B8A6FF'
    walls = []
    for x in range(COLS):
        for y in range(ROWS):
            if x + 1 < COLS and frozenset(((x, y), (x + 1, y))) not in p:
                walls.append(f'M{OX + (x + 1) * CELL} {OY + y * CELL}v{CELL}')
            if y + 1 < ROWS and frozenset(((x, y), (x, y + 1))) not in p:
                walls.append(f'M{OX + x * CELL} {OY + (y + 1) * CELL}h{CELL}')
    walls.append(f'M{OX} {OY}h{COLS * CELL}v{ROWS * CELL}h-{COLS * CELL}Z')
    d = ''.join(walls)

    used = set(hp) | set(sp)
    rnd = random.Random(seed)
    free = sorted(c for c in ((x, y) for x in range(COLS) for y in range(ROWS)) if c not in (hp[0], sp[0], hp[-1]))
    rnd.shuffle(free)
    near = [c for c in free if c in used][:3] + [c for c in free if c not in used][:2]
    coins = ''.join(f'<circle cx="{centre(c)[0]}" cy="{centre(c)[1]}" r="2.6" fill="{gold}"/>' for c in near[:4])
    ox_, oy_ = centre(near[4])
    orb = f'<circle cx="{ox_}" cy="{oy_}" r="3.4" fill="{violet}"/>'
    loot = coins + orb

    hx, hy = centre(hp[len(hp) // 2])
    sx, sy = centre(sp[len(sp) // 3])
    ex, ey = centre(hp[-1])
    T = '18s'
    css = (
        move_frames('hide', hp, HIDE_START, HIDE_END) + move_frames('seek', sp, SEEK_START, CATCH)
        + f'@keyframes vis{{0%{{opacity:0}}3%,{GONE}%{{opacity:1}}99%,100%{{opacity:0}}}}'
        + f'@keyframes rev{{0%,{REVEAL_END}%{{opacity:.9}}{DARK}%,{GONE}%{{opacity:.09}}100%{{opacity:.9}}}}'
        + f'@keyframes clock{{0%,{DARK}%{{transform:scaleX(1)}}{CATCH}%,100%{{transform:scaleX(0)}}}}'
        + f'@keyframes ring{{0%,{CATCH - 1}%{{opacity:0;transform:scale(.4)}}{CATCH}%{{opacity:1;transform:scale(.6)}}{GONE}%,100%{{opacity:0;transform:scale(3.2)}}}}'
        + f'@keyframes p1{{0%,{REVEAL_END}%{{opacity:1}}{REVEAL_END + 1}%,100%{{opacity:0}}}}'
        + f'@keyframes p2{{0%,{REVEAL_END}%{{opacity:0}}{REVEAL_END + 1}%,{CATCH - 1}%{{opacity:1}}{CATCH}%,100%{{opacity:0}}}}'
        + f'@keyframes p3{{0%,{CATCH - 1}%{{opacity:0}}{CATCH}%,{GONE}%{{opacity:1}}100%{{opacity:0}}}}'
        + f'.h{{transform:translate({hx}px,{hy}px);animation:hide {T} linear infinite}}'
        + f'.s{{transform:translate({sx}px,{sy}px);animation:seek {T} linear infinite}}'
        + f'.v{{animation:vis {T} linear infinite}}'
        + f'.rev{{opacity:.09;animation:rev {T} linear infinite}}'
        + f'.clock{{transform:scaleX(.62);animation:clock {T} linear infinite}}'
        + f'.ring{{opacity:0;animation:ring {T} ease-out infinite}}'
        + f'.p1{{opacity:0;animation:p1 {T} linear infinite}}.p2{{animation:p2 {T} linear infinite}}.p3{{opacity:0;animation:p3 {T} linear infinite}}'
    )
    box = (OX - 6, OY - 6, COLS * CELL + 12, ROWS * CELL + 12)
    mask_rect = f'maskUnits="userSpaceOnUse" x="{box[0]}" y="{box[1]}" width="{box[2]}" height="{box[3]}"'
    art = (
        '<defs>'
        '<radialGradient id="l"><stop stop-color="#fff"/><stop offset=".5" stop-color="#fff" stop-opacity=".8"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="gh"><stop stop-color="{CREAM}" stop-opacity=".2"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="gs"><stop stop-color="{rose}" stop-opacity=".3"/><stop offset="1" stop-color="{rose}" stop-opacity="0"/></radialGradient>'
        f'<mask id="mh" {mask_rect}><g class="v"><g class="h"><circle r="40" fill="url(#l)"/></g></g></mask>'
        f'<mask id="ms" {mask_rect}><g class="v"><g class="s"><circle r="34" fill="url(#l)"/></g></g></mask>'
        f'<clipPath id="box"><rect x="{box[0]}" y="{box[1]}" width="{box[2]}" height="{box[3]}" rx="6"/></clipPath>'
        '</defs>'
        f'<rect x="{box[0]}" y="{box[1]}" width="{box[2]}" height="{box[3]}" rx="6" fill="#070A10" stroke="{LINE}"/>'
        '<g clip-path="url(#box)">'
        f'<g class="v"><g class="h"><circle r="40" fill="url(#gh)"/></g><g class="s"><circle r="34" fill="url(#gs)"/></g></g>'
        f'<g class="rev"><path d="{d}" fill="none" stroke="{CREAM}" stroke-width="1.5" stroke-linecap="square"/>{loot}</g>'
        f'<g mask="url(#mh)"><path d="{d}" fill="none" stroke="{CREAM}" stroke-width="1.6" stroke-linecap="square"/>{loot}</g>'
        f'<g mask="url(#ms)"><path d="{d}" fill="none" stroke="{rose}" stroke-width="1.6" stroke-linecap="square"/>{loot}</g>'
        f'<g transform="translate({ex},{ey})"><circle class="ring" r="7" fill="none" stroke="{rose}" stroke-width="1.6"/></g>'
        '<g class="v">'
        f'<g class="h"><path d="M-3.5-5L5 1.2L1 2L3.2 6L1.4 7L-.8 3L-3.5 5.6Z" fill="{CREAM}" stroke="#070A10" stroke-width=".8" stroke-linejoin="round"/></g>'
        f'<g class="s"><circle r="5.2" fill="none" stroke="{rose}" stroke-width="1.6"/><path d="M-8.5 0h5M3.5 0h5M0-8.5v5M0 3.5v5" stroke="{rose}" stroke-width="1.6" fill="none"/><circle r="1.2" fill="{rose}"/></g>'
        '</g></g>'
        # HUD on the left: phase label and the hunt clock.
        + text(24, 176, 'REVEAL / 3 S', CREAM, 11, extra=' class="p1"')
        + text(24, 176, 'HUNT / LIGHTS OUT', rose, 11, extra=' class="p2"')
        + text(24, 176, 'CAUGHT', rose, 11, extra=' class="p3"')
        + f'<rect x="24" y="186" width="150" height="3" rx="1.5" fill="#1D2531"/>'
        + f'<g transform="translate(24,186)"><rect class="clock" width="150" height="3" rx="1.5" fill="{rose}"/></g>'
    )
    svg = card('02', 'curseek', 'MULTIPLAYER HIDE-AND-SEEK', rose, css, art,
               'Original conceptual artwork: a generated maze, a hider cursor with a small light and a red seeker. Source repository linked in README.')
    (OUT / 'curseek.svg').write_text(svg, encoding='utf-8')
    return seed, len(hp), len(sp)


# ───────────────────────── portfolio: the command line and its three shapes ─────────────────────────

def portfolio():
    amber = '#FFC857'
    x0, y0, w, h = 350, 48, 208, 150
    rows = ['Systems', 'Interfaces', 'Experiments']
    css = (
        '@keyframes type{0%,8%{transform:translateX(0)}32%,92%{transform:translateX(54px)}100%{transform:translateX(0)}}'
        '@keyframes blink{50%{opacity:0}}'
        '@keyframes pick{0%,30%{transform:translateY(0)}33.4%,63%{transform:translateY(24px)}66.7%,96%{transform:translateY(48px)}100%{transform:translateY(0)}}'
        '@keyframes sig{0%,100%{opacity:.25}12%,40%{opacity:1}}'
        '@keyframes turn{to{transform:rotate(360deg)}}'
        '.type{transform:translateX(54px);animation:type 9s steps(6,end) infinite}'
        '.caret{animation:blink 1s steps(1) infinite}'
        '.pick{animation:pick 9s cubic-bezier(.7,0,.2,1) infinite}'
        '.sig{animation:sig 7s ease-in-out infinite}'
        '.turn{animation:turn 14s linear infinite}'
    )
    art = (
        f'<clipPath id="win"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="8"/></clipPath>'
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="8" fill="{INSET}" stroke="{LINE}"/>'
        '<g clip-path="url(#win)">'
        # Command line: a "/" keycap, then `whoami` typed one character at a time.
        f'<rect x="{x0 + 12}" y="{y0 + 11}" width="20" height="20" rx="4" fill="#1A2230" stroke="{LINE}"/>'
        + text(x0 + 22, y0 + 26, '/', MUTED, 13, extra=' text-anchor="middle"')
        + text(x0 + 42, y0 + 26, 'whoami', CREAM, 15, extra=' textLength="54" lengthAdjust="spacingAndGlyphs"')
        + f'<g class="type"><rect x="{x0 + 42}" y="{y0 + 10}" width="70" height="22" fill="{INSET}"/>'
          f'<rect class="caret" x="{x0 + 44}" y="{y0 + 13}" width="7" height="16" fill="{amber}"/></g>'
        + f'<path d="M{x0} {y0 + 42}h{w}" stroke="{LINE}" fill="none"/>'
        # Results: the three territories of the site, with a moving selection.
        + f'<g class="pick"><rect x="{x0 + 8}" y="{y0 + 50}" width="{w - 16}" height="20" rx="4" fill="{amber}" fill-opacity=".13"/>'
          f'<rect x="{x0 + 8}" y="{y0 + 50}" width="2.5" height="20" rx="1" fill="{amber}"/></g>'
    )
    for i, name in enumerate(rows):
        y = y0 + 64 + i * 24
        art += text(x0 + 20, y, f'0{i + 1}', MUTED, 11) + text(x0 + 44, y, name, CREAM, 13, SANS, 700)
    sx, sy = x0 + w - 24, y0 + 60
    art += (
        f'<circle cx="{sx}" cy="{sy}" r="5" fill="none" stroke="{amber}" stroke-width="1.5"/>'
        f'<g transform="translate({sx},{sy + 24})"><rect class="turn" x="-4.5" y="-4.5" width="9" height="9" fill="none" stroke="{amber}" stroke-width="1.5"/></g>'
        f'<path d="M{sx} {sy + 42.5}l5.5 9.5h-11Z" fill="none" stroke="{amber}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<path d="M{x0} {y0 + 124}h{w}" stroke="{LINE}" fill="none"/>'
    )
    for i in range(7):
        art += f'<circle class="sig" style="animation-delay:{i * 0.45:.2f}s" cx="{x0 + 22 + i * 11}" cy="{y0 + 137}" r="2.6" fill="{amber}"/>'
    art += text(x0 + w - 14, y0 + 141, '7 SIGNALS', MUTED, 10, extra=' text-anchor="end"') + '</g>'
    art += text(24, 176, 'LAYER 1 / READ IN 20 S', MUTED, 11) + text(24, 194, 'LAYER 2 / EXPLORE', amber, 11)
    svg = card('03', 'Portfolio', 'PORTFOLIO / ARCHIVE / LAB', amber, css, art,
               'Original conceptual artwork: a command line typing whoami above three selectable rows. Source repository linked in README.')
    (OUT / 'portfolio.svg').write_text(svg, encoding='utf-8')


# ───────────────────────── HamiYami: feature card with the real mobile page scrolling ─────────────────────────

def hamiyami():
    tomato, cream, charcoal = '#FF7A5C', '#FFF8EF', '#28251F'
    W, H = 1200, 380
    img = base64.b64encode(PHONE.read_bytes()).decode('ascii')
    iw, ih = 320, 2475
    sw = 204                       # screen width in card units
    sh = round(sw * ih / iw)       # full page height in card units
    px, py = 752, 34               # phone body
    view = H - (py + 12)           # visible screen height before the card edge
    travel = sh - view
    css = (
        f'@keyframes scroll{{0%,5%{{transform:translateY(0)}}95%,100%{{transform:translateY(-{travel}px)}}}}'
        '@keyframes pulse{50%{opacity:.3}}'
        '@keyframes float{from{transform:translateY(0)}to{transform:translateY(-8px)}}'
        '@keyframes dash{to{stroke-dashoffset:-36}}'
        '@keyframes steam{0%{opacity:0;transform:translateY(6px)}40%{opacity:.9}100%{opacity:0;transform:translateY(-12px)}}'
        '.scroll{animation:scroll 30s ease-in-out infinite alternate}'
        '.pulse{animation:pulse 2.4s ease-in-out infinite}'
        '.float{animation:float 4.5s ease-in-out infinite alternate}'
        '.dash{stroke-dasharray:6 6;animation:dash 4s linear infinite}'
        '.steam{opacity:.7;animation:steam 3.6s ease-in-out infinite}'
    )
    chips, cx = '', 44
    for label in ['NEXT.JS 16', 'REACT 19', 'TYPESCRIPT', 'CLOUDFLARE WORKERS', 'IT / EN']:
        cw = round(len(label) * 7.3) + 22
        chips += (f'<rect x="{cx}" y="262" width="{cw}" height="30" rx="6" fill="none" stroke="{LINE}"/>'
                  + text(cx + cw / 2, 281, label, MUTED, 12, extra=' text-anchor="middle"'))
        cx += cw + 8

    tx, ty = 1066, 196             # ticket centre
    ticket = (
        f'<g class="float"><g transform="translate({tx},{ty}) rotate(6)">'
        '<rect x="-80" y="-74" width="168" height="160" rx="16" fill="#000" fill-opacity=".35"/>'
        f'<rect x="-86" y="-82" width="168" height="160" rx="16" fill="{cream}"/>'
        + text(-2, -52, 'CODICE RITIRO', '#5E574C', 11, extra=' text-anchor="middle"')
        + text(-2, -6, 'K7M4', charcoal, 42, SANS, 900, 1, ' text-anchor="middle"')
        + '<path class="dash" d="M-70 14H66" stroke="#D8C6B1" stroke-width="1.5" fill="none"/>'
        + text(-2, 40, 'GIO  19:30–20:00', '#A8331F', 12, weight=700, extra=' text-anchor="middle"')
        + text(-2, 60, '+ CALENDARIO (.ICS)', '#46573F', 10, extra=' text-anchor="middle"')
        + '</g></g>'
    )
    # Steam rising behind the title, from a small bowl mark.
    bx, by = 598, 132
    steam = ''.join(
        f'<path class="steam" style="animation-delay:{i * 1.1:.1f}s" d="M{bx - 14 + i * 14} {by - 22}q-6-8 0-16t0-16" '
        f'fill="none" stroke="{cream}" stroke-opacity=".7" stroke-width="2.4" stroke-linecap="round"/>' for i in range(3))
    bowl = (
        steam
        + f'<path d="M{bx - 34} {by - 10}h68q-2 30-34 30t-34-30Z" fill="{tomato}"/>'
        + f'<path d="M{bx - 40} {by - 10}h80" stroke="{cream}" stroke-width="3" stroke-linecap="round" fill="none"/>'
        + f'<path d="M{bx - 14} {by + 24}h28" stroke="{cream}" stroke-width="3" stroke-linecap="round" fill="none"/>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
        '<title id="t">HamiYami — dinner, cooked nearby, ready for pickup. Live at hamiyami.com</title>'
        '<desc id="d">Feature card. The phone shows a real capture of the public HamiYami demo home page, scrolling. '
        'The pickup ticket is conceptual artwork. All meals, cooks and availability in the demo are fictional.</desc>'
        f'<style>{css}{RM}</style>'
        '<defs>'
        f'<radialGradient id="warm"><stop stop-color="{tomato}" stop-opacity=".22"/><stop offset="1" stop-color="{tomato}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff" stop-opacity=".10"/><stop offset=".35" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="cardclip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>'
        f'<clipPath id="screen"><rect x="{px + 10}" y="{py + 10}" width="{sw}" height="{H}" rx="20"/></clipPath>'
        '</defs>'
        f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="{BG}"/>'
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        '<g clip-path="url(#cardclip)">'
        f'<circle cx="900" cy="210" r="360" fill="url(#warm)"/>'
        # Left column
        + text(44, 57, '01 / LATEST BUILD', MUTED, 14)
        + '<rect x="204" y="35" width="228" height="34" rx="6" fill="#1A2420"/>'
        + f'<circle class="pulse" cx="221" cy="52" r="4" fill="{LIME}"/>'
        + text(235, 57, 'LIVE / HAMIYAMI.COM', CREAM, 14)
        + f'<text x="40" y="150" font-family="{SANS}" font-size="84" font-weight="900" letter-spacing="-2.1">'
          f'<tspan fill="{CREAM}">Hami</tspan><tspan fill="{tomato}">Yami</tspan></text>'
        + bowl
        + text(44, 198, 'Dinner, cooked nearby, ready for pickup.', CREAM, 27, SANS, 400, -0.6)
        + text(44, 232, 'A bilingual marketplace demo for neighbourhood cooks in Italy.', MUTED, 19, SANS, 400, -0.3)
        + chips
        + f'<path d="M44 326H704" stroke="{LINE}" fill="none"/>'
        + text(44, 354, 'PRELAUNCH DEMO  /  FICTIONAL DATA', MUTED, 13)
        + text(704, 354, 'OPEN LIVE  ↗', tomato, 13, weight=700, extra=' text-anchor="end"')
        # Phone
        + f'<rect x="{px}" y="{py}" width="{sw + 20}" height="{H}" rx="30" fill="#05070B" stroke="#3A4350" stroke-width="1.5"/>'
        + f'<g clip-path="url(#screen)"><rect x="{px + 10}" y="{py + 10}" width="{sw}" height="{H}" fill="{cream}"/>'
          f'<g class="scroll"><image href="data:image/jpeg;base64,{img}" x="{px + 10}" y="{py + 10}" width="{sw}" height="{sh}" preserveAspectRatio="none"/></g>'
          f'<rect x="{px + 10}" y="{py + 10}" width="{sw}" height="{H}" fill="url(#glass)"/></g>'
        + f'<rect x="{px + 10 + sw / 2 - 26}" y="{py + 17}" width="52" height="13" rx="6.5" fill="#05070B"/>'
        + ticket
        + '</g></svg>'
    )
    (OUT / 'hamiyami.svg').write_text(svg, encoding='utf-8')
    return len(svg)


# ───────────────────────── marquee and section label ─────────────────────────

def marquee():
    W, H = 1200, 44
    names = [('HAMIYAMI', '#FF7A5C'), ('CURSEEK', '#FF5C7A'), ('PORTFOLIO', '#FFC857'), ('WHOMST', ORANGE),
             ('LEDGER', LIME), ('VELOCITY', '#90DFFF'), ('CVAI', '#B8A6FF')]
    slot = W / len(names)
    seg = ''
    for copy in range(2):
        for i, (n, c) in enumerate(names):
            x = copy * W + i * slot
            seg += text(round(x + slot / 2, 1), 28, n, c, 15, weight=700, ls=3, extra=' text-anchor="middle"')
            seg += f'<rect x="{x - 3:.1f}" y="19" width="6" height="6" fill="{LINE}" transform="rotate(45 {x:.1f} 22)"/>'
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">'
        '<title id="t">HamiYami, curseek, Portfolio, Whomst, Ledger, VeloCity, CVai</title>'
        f'<style>@keyframes roll{{to{{transform:translateX(-{W}px)}}}}.roll{{animation:roll 38s linear infinite}}{RM}</style>'
        f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
        f'<linearGradient id="f"><stop stop-color="{BG}"/><stop offset=".1" stop-color="{BG}" stop-opacity="0"/>'
        f'<stop offset=".9" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>'
        f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{BG}"/><g class="roll">{seg}</g>'
        f'<rect width="{W}" height="{H}" fill="url(#f)"/></g>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="11.5" fill="none" stroke="{LINE}"/></svg>'
    )
    (OUT / 'marquee.svg').write_text(svg, encoding='utf-8')


SECTIONS = [('01', 'BUILDING AT INREBUS', 'professional'), ('02', 'INDEPENDENT EXPERIMENTS', 'projects'),
            ('03', 'THE COMMIT STREAM', 'shiplog'), ('04', 'MY TOOLKIT', 'toolkit'), ('05', 'THE PUBLIC SIGNAL', 'activity')]


def sections():
    """Section labels as dark bars, the same in both GitHub themes, with a dot running along the rule."""
    for num, title, slug in SECTIONS:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="56" viewBox="0 0 800 56" role="img" aria-labelledby="t">'
            f'<title id="t">{num} — {title}</title>'
            f'<style>@keyframes run{{0%{{transform:translateX(0);opacity:0}}8%,88%{{opacity:1}}100%{{transform:translateX(326px);opacity:0}}}}'
            f'.run{{opacity:0;animation:run 4.5s ease-in-out infinite}}{RM}</style>'
            f'<rect x=".5" y=".5" width="799" height="55" rx="12" fill="{BG}" stroke="{LINE}"/>'
            + text(22, 36, num, ORANGE, 21, weight=700)
            + text(76, 36, title, CREAM, 22, SANS, 700, -0.5)
            + f'<path d="M452 28H778" stroke="{LINE}" stroke-width="1" fill="none"/>'
            + f'<circle class="run" cx="452" cy="28" r="3" fill="{ORANGE}"/></svg>'
        )
        (OUT / f'section-{slug}.svg').write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    print('curseek seed/hider/seeker path:', curseek())
    portfolio()
    print('hamiyami bytes:', hamiyami())
    marquee()
    sections()
    print('done')
