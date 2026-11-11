"""Rebuild the hand-designed profile artwork. Every block of the README is a dark image, so the
profile looks the same in GitHub's light and dark themes: intro, buttons, project and work
cards, the edbub banner, the side-project strip, toolkit, footer, marquee and section labels.

Python standard library only. Run it after editing a design below:

    python3 scripts/build_art.py

The phone in the HamiYami card shows scripts/source/hamiyami-phone.jpg, a 320 x 2475 crop of
the public demo's mobile home page. To replace it, keep that size or update `iw, ih` in hamiyami().
"""
import base64
import random
import re
import sys
import textwrap
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'assets'
PHONE = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'source' / 'hamiyami-phone.jpg'
SOURCE = HERE / 'source'      # artwork that other blocks nest: the work covers and the skill icons

BG, PANEL, LINE, MUTED, CREAM = '#0B0E14', '#111722', '#29313C', '#939BA8', '#F3EFE5'
INSET, ORANGE, LIME = '#0A0F18', '#FF642D', '#C6FF00'
MONO, SANS = 'Consolas,monospace', 'Arial,Helvetica,sans-serif'
RM = '@media(prefers-reduced-motion:reduce){*{animation:none!important}}'


def text(x, y, s, fill=MUTED, size=12, family=MONO, weight=400, ls=0, extra=''):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{ls}"{extra}>{escape(s)}</text>')


def card(label, title, tagline, accent, css, art, desc, footer='VIEW SOURCE'):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="580" height="260" viewBox="0 0 580 260" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)} — {escape(tagline)}</title><desc id="d">{escape(desc)}</desc>'
        f'<style>{css}{RM}</style>'
        f'<rect x="0" y="0" width="580" height="260" rx="16" fill="{BG}"/>'
        f'<rect x="1" y="1" width="578" height="258" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        + text(23, 33, label, MUTED, 13)
        + text(23, 103, title, CREAM, 46, SANS, 900, -1.15)
        + text(24, 138, tagline, accent, 13)
        + art
        + f'<path d="M24 215L556 215" stroke="{LINE}" stroke-width="1" fill="none"/>'
        + text(24, 242, footer, MUTED, 13)
        + text(532, 245, '↗', accent, 22, SANS, 400, -0.55)
        + '</svg>'
    )


# ───────────────────────── edbub: third place, on the podium ─────────────────────────

def edbub():
    W, H = 1200, 240
    bronze, deep, light, ink = '#E0975A', '#8A4F27', '#F6C79A', '#2A1608'
    rnd = random.Random(7)
    confetti = ''
    for k in range(34):
        x = rnd.uniform(600, 1180)
        col = rnd.choice([bronze, light, CREAM, ORANGE, LIME, '#7CE0C3', '#F29BD4'])
        dur = rnd.uniform(3.6, 6.8)
        confetti += (f'<g transform="translate({x:.1f},-24)"><rect class="c" style="animation-duration:{dur:.2f}s;animation-delay:-{rnd.uniform(0, dur):.2f}s" '
                     f'width="{rnd.choice([5, 6, 7])}" height="{rnd.choice([9, 11, 13])}" rx="1.5" fill="{col}"/></g>')
    css = (
        f'@keyframes fall{{0%{{transform:translateY(0) rotate(0deg)}}100%{{transform:translateY({H + 40}px) rotate(540deg)}}}}'
        '.c{transform-box:fill-box;transform-origin:center;animation:fall linear infinite}'
        '@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-8px)}}.bob{animation:bob 2.6s ease-in-out infinite alternate}'
        '@keyframes shine{0%,50%{transform:translateX(-110px)}72%,100%{transform:translateX(110px)}}.shine{animation:shine 4.2s ease-in-out infinite}'
        '@keyframes glow{50%{opacity:.2}}.glow{animation:glow 2.4s ease-in-out infinite}'
        '@keyframes tw{0%,100%{opacity:0;transform:scale(.4)}50%{opacity:1;transform:scale(1)}}'
        '.tw{transform-box:fill-box;transform-origin:center;opacity:0;animation:tw 2.2s ease-in-out infinite}'
    )
    base = 214
    blocks = [('2', 650, 64, False), ('1', 766, 92, False), ('3', 882, 46, True)]
    podium = f'<path d="M620 {base}H1012" stroke="{LINE}" stroke-width="1.5" fill="none"/>'
    for label, x, h, ours in blocks:
        fill = 'url(#bz)' if ours else '#161D28'
        podium += f'<rect x="{x}" y="{base - h}" width="110" height="{h}" rx="6" fill="{fill}" stroke="{light if ours else LINE}"/>'
        if ours:
            podium += f'<rect class="glow" x="{x - 6}" y="{base - h - 6}" width="122" height="{h + 6}" rx="10" fill="none" stroke="{bronze}" stroke-width="2"/>'
        podium += text(x + 55, base - h / 2 + 11, label, ink if ours else MUTED, 30, SANS, 900, extra=' text-anchor="middle"')
    sparks = ''.join(
        f'<path class="tw" style="animation-delay:{d}s" d="M{sx} {sy - 7}L{sx + 2} {sy - 2}L{sx + 7} {sy}L{sx + 2} {sy + 2}L{sx} {sy + 7}L{sx - 2} {sy + 2}L{sx - 7} {sy}L{sx - 2} {sy - 2}Z" fill="{light}"/>'
        for sx, sy, d in [(872, 150, 0), (1000, 140, .7), (940, 128, 1.4)])
    mx, my = 1100, 112
    medal = (
        f'<g class="bob"><path d="M{mx - 30} 22L{mx - 8} {my - 40}L{mx + 4} {my - 40}L{mx - 14} 22Z" fill="#B23A2E"/>'
        f'<path d="M{mx + 30} 22L{mx + 8} {my - 40}L{mx - 4} {my - 40}L{mx + 14} 22Z" fill="#D9503F"/>'
        f'<clipPath id="md"><circle cx="{mx}" cy="{my}" r="46"/></clipPath>'
        f'<circle cx="{mx}" cy="{my}" r="46" fill="url(#bz)" stroke="{light}" stroke-width="3"/>'
        f'<circle cx="{mx}" cy="{my}" r="36" fill="none" stroke="{light}" stroke-opacity=".55" stroke-width="1.5"/>'
        + text(mx - 6, my + 18, '3', ink, 52, SANS, 900, extra=' text-anchor="middle"')
        + text(mx + 16, my - 4, 'RD', ink, 14, SANS, 900)
        + f'<g clip-path="url(#md)"><rect class="shine" x="{mx - 14}" y="{my - 60}" width="28" height="120" fill="#fff" fill-opacity=".45" transform="rotate(20 {mx} {my})"/></g></g>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
        '<title id="t">edbub — 3rd place at a hackathon, built with friends</title>'
        '<desc id="d">A podium with the third-place block lit in bronze, a bronze medal and falling confetti. The project repository is private.</desc>'
        f'<style>{css}{RM}</style>'
        f'<defs><linearGradient id="bz" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{light}"/><stop offset=".45" stop-color="{bronze}"/><stop offset="1" stop-color="{deep}"/></linearGradient>'
        f'<radialGradient id="bh"><stop stop-color="{bronze}" stop-opacity=".22"/><stop offset="1" stop-color="{bronze}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="cc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath></defs>'
        f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>'
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        '<g clip-path="url(#cc)">'
        f'<circle cx="960" cy="150" r="300" fill="url(#bh)"/>'
        + text(44, 54, '04 / HACKATHON / BUILT WITH FRIENDS', MUTED, 15)
        + text(38, 142, 'edbub', CREAM, 92, SANS, 900, -2.3)
        + text(44, 190, '3RD PLACE', bronze, 32, SANS, 900, 3)
        + text(44, 220, 'TEAM PROJECT  /  PRIVATE REPOSITORY', MUTED, 13)
        + confetti + podium + sparks + medal
        + '</g></svg>'
    )
    (OUT / 'edbub.svg').write_text(svg, encoding='utf-8')


# ───────────────────────── HamiYami: feature card with the real mobile page scrolling ─────────────────────────

def hamiyami():
    tomato, cream, charcoal = '#FF7A5C', '#FFF8EF', '#28251F'
    W, H = 1200, 492
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
        chips += (f'<rect x="{cx}" y="384" width="{cw}" height="30" rx="6" fill="none" stroke="{LINE}"/>'
                  + text(cx + cw / 2, 403, label, MUTED, 12, extra=' text-anchor="middle"'))
        cx += cw + 8

    tx, ty = 1066, 250             # ticket centre
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
        + ''.join(text(44, 274 + i * 28, line, SOFT, 20, SANS) for i, line in enumerate(textwrap.wrap(
            'A weekly menu by pickup day, reservations with pickup codes and calendar export, a cook workspace '
            'with a day-by-day prep view, and a scrollytelling story page. Every meal, cook and number in it is '
            'fictional, and the demo says so.', 60)))
        + chips
        + f'<path d="M44 440H704" stroke="{LINE}" fill="none"/>'
        + text(44, 470, 'PRELAUNCH DEMO  /  117 UNIT + 51 BROWSER TESTS', MUTED, 14)
        + text(704, 470, 'OPEN LIVE  ↗', tomato, 14, weight=700, extra=' text-anchor="end"')
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


# ───────────────────────── shared pieces for the all-dark layout ─────────────────────────

SOFT = '#C9CED6'     # body copy on dark panels


def wrap(s, chars):
    return textwrap.wrap(s, chars)


def frame(W, H, title, desc, css, body, defs=''):
    """A dark card: the outer shape every block of the profile shares."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f'<style>{css}{RM}</style>'
        f'<defs><clipPath id="cc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>{defs}</defs>'
        f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>'
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        f'<g clip-path="url(#cc)">{body}</g></svg>'
    )


def embed(path, x, y, w, view):
    """Nest another of the profile's SVGs, cropped to `view` (x, y, width, height of its own canvas)."""
    s = path.read_text(encoding='utf-8')
    s = re.sub(r'<title[^>]*>.*?</title>|<desc[^>]*>.*?</desc>', '', s, flags=re.S)
    inner = s[s.index('>', s.index('<svg')) + 1:s.rindex('</svg>')]
    vx, vy, vw, vh = view
    h = w * vh / vw
    return f'<svg x="{x}" y="{y:.1f}" width="{w}" height="{h:.1f}" viewBox="{vx} {vy} {vw} {vh}">{inner}</svg>', h


def pill(label, filename, accent=ORANGE, dot=None):
    """A small dark button, the same family as the GitHub and LinkedIn buttons."""
    w = round(len(label) * 7.9) + (64 if dot else 48)
    x = 15
    body = ''
    if dot:
        body += f'<circle cx="21" cy="20" r="4" fill="{dot}"/>'
        x = 35
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="40" viewBox="0 0 {w} 40" role="img" aria-labelledby="t">'
        f'<title id="t">{escape(label)}</title>'
        f'<rect width="{w}" height="40" rx="8" fill="{BG}"/><rect x=".5" y=".5" width="{w - 1}" height="39" rx="7.5" fill="none" stroke="{LINE}"/>'
        + body + text(x, 26, label, CREAM, 13, weight=600)
        + text(w - 27, 26, '↗', accent, 17, SANS)
        + '</svg>'
    )
    (OUT / filename).write_text(svg, encoding='utf-8')


# ───────────────────────── intro, buttons, strips ─────────────────────────

def intro():
    W, H = 1200, 200
    css = ('@keyframes beam{to{transform:translateX(1560px)}}.beam{animation:beam 6s linear infinite}')
    body = (
        f'<rect class="beam" x="-360" y="1" width="360" height="3" fill="url(#ib)"/>'
        f'<text x="600" y="80" text-anchor="middle" font-family="{SANS}" font-size="32" fill="{CREAM}" letter-spacing="-0.4">'
        f'I’m <tspan font-weight="900">Faraz</tspan>, a developer and product builder in <tspan font-weight="900" fill="{ORANGE}">Turin, Italy</tspan>.</text>'
        + text(600, 128, 'Industrial interfaces by day. Independent experiments whenever an idea won’t leave me alone.', SOFT, 22, SANS, extra=' text-anchor="middle"')
        + text(600, 164, 'I care about the system underneath, the interaction on top, and the details in between.', SOFT, 22, SANS, extra=' text-anchor="middle"')
    )
    defs = f'<linearGradient id="ib"><stop stop-color="{ORANGE}" stop-opacity="0"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/></linearGradient>'
    (OUT / 'intro.svg').write_text(frame(W, H, 'I’m Faraz, a developer and product builder in Turin, Italy.',
                                         'Industrial interfaces by day. Independent experiments whenever an idea won’t leave me alone. '
                                         'I care about the system underneath, the interaction on top, and the details in between.',
                                         css, body, defs), encoding='utf-8')


def buttons():
    for label, name in [('01 / INREBUS', 'nav-inrebus'), ('02 / PROJECTS', 'nav-projects'),
                        ('03 / CONTROL ROOM', 'nav-control'), ('04 / TOOLKIT', 'nav-toolkit')]:
        pill(label, f'{name}.svg')
    for label, name, dot in [('HAMIYAMI / CODE', 'code-hamiyami', '#FF7A5C'), ('UNIEXAMER / CODE', 'code-uniexamer', '#7CE0C3'),
                             ('VIBEASSIST / CODE', 'code-vibeassist', '#F29BD4'), ('AMIRAK-CODE / GITHUB', 'code-amirak', CREAM)]:
        pill(label, f'{name}.svg', dot=dot)


def fun():
    W, H = 1200, 72
    names = [('curseek', '#FF5C7A'), ('portfolio', '#FFC857'), ('Whomst', ORANGE), ('Ledger', '#E6FF7A'), ('VeloCity', '#90DFFF'), ('CVai', '#B8A6FF')]
    body = text(32, 44, 'ALSO BUILT, JUST FOR FUN', MUTED, 16, ls=2)
    x = 330
    for i, (n, c) in enumerate(names):
        if i:
            body += text(x - 22, 44, '·', LINE, 22)
        body += text(x, 44, n, c, 20, weight=700)
        x += round(len(n) * 11) + 44
    body += text(1166, 45, '↗', ORANGE, 20, SANS, extra=' text-anchor="end"')
    (OUT / 'fun.svg').write_text(frame(W, H, 'Also built, just for fun: curseek, portfolio, Whomst, Ledger, VeloCity and CVai',
                                       'Side projects; the link opens the repository list.', '', body), encoding='utf-8')


def footer():
    W, H = 1200, 220
    css = '@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(6px,-6px)}}.nudge{animation:nudge 2.4s ease-in-out infinite}'
    body = (
        text(32, 58, 'THE NEXT THING STARTS WITH A CONVERSATION.', ORANGE, 17)
        + text(30, 122, 'Build something worth using.', CREAM, 52, SANS, 700, -1.3)
        + f'<g class="nudge"><path d="M1080 126L1140 66M1092 66H1140V114" fill="none" stroke="{ORANGE}" stroke-width="4"/></g>'
        + f'<path d="M32 160H1168" stroke="{LINE}" fill="none"/>'
        + text(32, 194, 'FARAZ HAGHGOO  /  TURIN, ITALY', MUTED, 16, ls=1)
        + text(1168, 194, 'SAY HELLO ON LINKEDIN  ↗', CREAM, 16, weight=700, extra=' text-anchor="end"')
    )
    (OUT / 'footer.svg').write_text(frame(W, H, 'Build something worth using. The next thing starts with a conversation.',
                                          'Faraz Haghgoo, Turin, Italy. The link opens LinkedIn.', css, body), encoding='utf-8')


# ───────────────────────── professional work ─────────────────────────

def work_cards():
    cards = [
        ('work-hmi', '01 / INREBUS', 'Industrial HMI / Digital Twin',
         'Making complex industrial systems understandable through human–machine interfaces and technical visualization.',
         'INTERFACE ENGINEERING · INTERACTION · SYSTEMS'),
        ('work-inrebus', '02 / INREBUS', 'inRebus / Digital experience',
         'Developing the company’s web experience through responsive interfaces, visual identity and purposeful motion.',
         'REACT · TYPESCRIPT · VITE · GSAP'),
    ]
    W, H = 1200, 330
    for name, label, title, desc, tags in cards:
        art, ah = embed(SOURCE / f'{name}.svg', 652, 0, 516, (12, 98, 556, 196))
        art = art.replace('y="0.0"', f'y="{(H - ah) / 2:.1f}"', 1)
        css = re.search(r'<style>(.*?)</style>', (SOURCE / f'{name}.svg').read_text(encoding='utf-8'), flags=re.S)
        body = (text(44, 56, label, MUTED, 15)
                + '<rect x="190" y="36" width="150" height="28" rx="6" fill="#322219"/>' + text(205, 56, 'PRIVATE WORK', '#FF9A6A', 14)
                + text(42, 116, title, CREAM, 40, SANS, 700, -0.8))
        for i, line in enumerate(wrap(desc, 52)):
            body += text(44, 162 + i * 30, line, SOFT, 22, SANS)
        body += (text(44, 268, tags, ORANGE, 16, ls=1)
                 + text(44, 300, 'PROFESSIONAL  /  PRIVATE REPOSITORY  /  CONCEPTUAL COVER', MUTED, 14) + art)
        (OUT / f'{name}-card.svg').write_text(
            frame(W, H, f'{title} — private professional work at inRebus', f'{desc} Conceptual cover artwork; source code remains private.',
                  css[1] if css else '', body), encoding='utf-8')


# ───────────────────────── the wide project cards ─────────────────────────

def wide_card(filename, label, title, tagline, accent, desc, stack, link, css, art, extra='', alt=''):
    W, H = 1200, 352
    body = (text(44, 56, label, MUTED, 15) + text(1156, 56, link + '  ↗', accent, 15, weight=700, extra=' text-anchor="end"')
            + text(40, 128, title, CREAM, 64, SANS, 900, -1.6)
            + text(44, 166, tagline, accent, 16, ls=1) + extra)
    for i, line in enumerate(wrap(desc, 54)):
        body += text(44, 210 + i * 29, line, SOFT, 21, SANS)
    body += text(44, 332, stack, MUTED, 14) + art
    (OUT / filename).write_text(frame(W, H, f'{title} — {tagline.lower()}', alt or desc, css, body), encoding='utf-8')


def uniexamer():
    teal = '#7CE0C3'
    x0, y0, w, h = 0, 0, 224, 176
    rows, widths, T = [66, 92, 118, 144], [96, 122, 84, 108], '9s'
    css = (
        f'@keyframes timer{{to{{stroke-dashoffset:69.12}}}}.timer{{animation:timer {T} linear infinite}}'
        '@keyframes hop{0%,14%{transform:translateY(0)}20%,36%{transform:translateY(26px)}42%,100%{transform:translateY(52px)}}'
        f'.hop{{transform:translateY(52px);animation:hop {T} cubic-bezier(.6,0,.2,1) infinite}}'
        '@keyframes pick{0%,44%{opacity:0}48%,94%{opacity:1}98%,100%{opacity:0}}'
        f'.pick{{animation:pick {T} ease-out infinite}}'
        '@keyframes cyc{0%,17%{opacity:1}20%,100%{opacity:0}}.ex{opacity:0;animation:cyc 10s linear infinite}.ex0{opacity:1}'
    )
    art = (
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="10" fill="{INSET}" stroke="{LINE}"/>'
        + text(x0 + 14, y0 + 24, 'Q 07 / 20', MUTED, 12)
        + f'<g transform="translate({x0 + w - 22},{y0 + 19}) rotate(-90)"><circle r="11" fill="none" stroke="#1D2531" stroke-width="3"/>'
          f'<circle class="timer" r="11" fill="none" stroke="{teal}" stroke-width="3" stroke-dasharray="69.12" stroke-linecap="round"/></g>'
        + f'<rect x="{x0 + 14}" y="{y0 + 36}" width="172" height="6" rx="3" fill="#3A4350"/>'
        + f'<rect x="{x0 + 14}" y="{y0 + 48}" width="118" height="6" rx="3" fill="#3A4350"/>'
    )
    for i, (ry, bw) in enumerate(zip(rows, widths)):
        art += (f'<rect x="{x0 + 12}" y="{ry}" width="{w - 24}" height="22" rx="6" fill="#121A26" stroke="{LINE}"/>'
                f'<circle cx="{x0 + 26}" cy="{ry + 11}" r="7" fill="none" stroke="{MUTED}" stroke-width="1.2"/>'
                + text(x0 + 26, ry + 14.5, 'ABCD'[i], MUTED, 10, extra=' text-anchor="middle"')
                + f'<rect x="{x0 + 42}" y="{ry + 8.5}" width="{bw}" height="5" rx="2.5" fill="#3A4350"/>')
    art += (
        f'<g class="hop"><rect x="{x0 + 12}" y="{rows[0]}" width="{w - 24}" height="22" rx="6" fill="{teal}" fill-opacity=".1" stroke="{teal}" stroke-width="1.5"/></g>'
        f'<g class="pick"><circle cx="{x0 + 26}" cy="{rows[2] + 11}" r="7" fill="{teal}"/>'
        + text(x0 + 26, rows[2] + 14.5, 'C', BG, 10, weight=700, extra=' text-anchor="middle"')
        + f'<path d="M{x0 + w - 36} {rows[2] + 11}l4 4l8-8" fill="none" stroke="{teal}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>'
    )
    extra = text(470, 92, 'PRACTICE FOR', MUTED, 15, ls=1)
    for k, name in enumerate(['BOCCONI', 'SAT', 'GMAT', 'TOLC-I', 'LSAT']):
        extra += text(470, 128, name, teal, 32, SANS, 900, 0.5, f' class="ex ex{k}" style="animation-delay:{2 * k}s"')
    wide_card('uniexamer.svg', '02 / WITH AMIRAK-CODE', 'UniExamer', 'EXAM PRACTICE / EVERY RULE SOURCED', teal,
              'Practice for university admission tests: Bocconi, SAT, ACT, LSAT, GMAT, GRE, PoliTo TIL and CISIA TOLC. '
              'Every rule about how an exam works is checked against the test maker’s own pages, with the source and the date.',
              'NEXT.JS · TYPESCRIPT · SUPABASE · STRIPE · CLAUDE · CLOUDFLARE WORKERS', 'UNIEXAMER.COM', css,
              f'<g transform="translate(842,78) scale(1.4)">{art}</g>', extra)


def vibeassist():
    pink = '#F29BD4'
    x0, y0, w, h = 0, 0, 224, 176
    T = '8s'
    pts = [(0, 40), (24, 44), (48, 30), (72, 35), (96, 22), (120, 27), (144, 14), (168, 17), (192, 4)]
    cx, cy = x0 + 16, y0 + 40
    line = 'M' + 'L'.join(f'{cx + a} {cy + b}' for a, b in pts)
    area = line + f'L{cx + 192} {y0 + 90}L{cx} {y0 + 90}Z'
    ex, ey = cx + pts[-1][0], cy + pts[-1][1]
    css = (
        '@keyframes draw{0%{stroke-dashoffset:1;opacity:1}35%,90%{stroke-dashoffset:0;opacity:1}98%,100%{stroke-dashoffset:0;opacity:0}}'
        f'.draw{{animation:draw {T} ease-in-out infinite}}'
        '@keyframes area{0%,28%{opacity:0}45%,90%{opacity:1}98%,100%{opacity:0}}'
        f'.area{{animation:area {T} ease-in-out infinite}}'
        '@keyframes typing{0%,40%{opacity:1}44%,100%{opacity:0}}'
        f'.typing{{opacity:0;animation:typing {T} linear infinite}}'
        '@keyframes answer{0%,42%{opacity:0}48%,90%{opacity:1}98%,100%{opacity:0}}'
        f'.answer{{animation:answer {T} linear infinite}}'
        '@keyframes dot{0%,100%{transform:translateY(0);opacity:.4}50%{transform:translateY(-3px);opacity:1}}'
        '.dot{animation:dot .9s ease-in-out infinite}'
        '@keyframes live{50%{opacity:.25}}.live{animation:live 1.6s ease-in-out infinite}'
    )
    art = (
        f'<defs><linearGradient id="va" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{pink}" stop-opacity=".32"/>'
        f'<stop offset="1" stop-color="{pink}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="10" fill="{INSET}" stroke="{LINE}"/>'
        + text(x0 + 14, y0 + 22, 'REVENUE / 30 D', MUTED, 11)
        + f'<circle class="live" cx="{x0 + w - 46}" cy="{y0 + 18}" r="3.5" fill="{pink}"/>'
        + text(x0 + w - 14, y0 + 22, 'LIVE', pink, 11, extra=' text-anchor="end"')
        + f'<path class="area" d="{area}" fill="url(#va)"/>'
        + f'<path class="draw" d="{line}" pathLength="1" stroke-dasharray="1" fill="none" stroke="{pink}" stroke-width="2.2" stroke-linejoin="round"/>'
        + f'<circle class="area" cx="{ex}" cy="{ey}" r="3.5" fill="{pink}"/>'
        + f'<path d="M{x0 + 12} {y0 + 90}H{x0 + w - 12}" stroke="{LINE}" fill="none"/>'
        + f'<rect x="{x0 + 12}" y="{y0 + 100}" width="{w - 24}" height="64" rx="10" fill="#1A1520" stroke="{pink}" stroke-opacity=".45"/>'
        + f'<circle cx="{x0 + 32}" cy="{y0 + 132}" r="11" fill="{pink}"/>'
        + text(x0 + 32, y0 + 135.5, 'AI', BG, 9, weight=700, extra=' text-anchor="middle"')
        + '<g class="typing">'
        + ''.join(f'<circle class="dot" style="animation-delay:{k * 0.15:.2f}s" cx="{x0 + 56 + k * 11}" cy="{y0 + 132}" r="3" fill="{pink}"/>' for k in range(3))
        + '</g><g class="answer">'
        + ''.join(f'<rect x="{x0 + 52}" y="{y0 + 114 + k * 13}" width="{bw}" height="5" rx="2.5" fill="{col}"/>'
                  for k, (bw, col) in enumerate([(140, pink), (112, '#5A4A58'), (128, '#5A4A58')]))
        + '</g>'
    )
    extra = text(510, 92, 'FOR INDIE APP MAKERS', MUTED, 15, ls=1) + text(510, 124, 'STRIPE · APP STORE · PLAY', pink, 18, weight=700)
    wide_card('vibeassist.svg', '03 / WITH AMIRAK-CODE', 'VibeAssist', 'DASHBOARD + AI ADVISOR', pink,
              'A dashboard, ad tracker and AI business advisor for indie app makers. It brings in revenue from Stripe, '
              'the App Store and Google Play, and answers questions about your own numbers.',
              'REACT · VITE · SUPABASE EDGE FUNCTIONS · STRIPE · CLAUDE · CLOUDFLARE WORKERS', 'VIBEASSIST.ASSIST365.APP', css,
              f'<g transform="translate(842,78) scale(1.4)">{art}</g>', extra)


# ───────────────────────── toolkit ─────────────────────────

def toolkit():
    W, H = 1200, 404
    icons, ih = embed(SOURCE / 'skill-icons.svg', 48, 34, 1104, (0, 0, 4456, 256))
    items = [('WEB', 'React + Next.js'), ('MOBILE', 'React Native + Expo'), ('DATA', 'PostgreSQL + Supabase'),
             ('MOTION', 'GSAP + Framer Motion'), ('REALTIME', 'Node.js + WebSocket'), ('EDGE', 'Cloudflare Workers'),
             ('TESTING', 'Vitest + Playwright')]
    body = icons
    for i, (k, v) in enumerate(items):
        col, row = divmod(i, 4)
        x, y = 60 + col * 580, 156 + row * 40
        body += text(x, y, k, ORANGE, 17, ls=2) + text(x + 150, y, v, CREAM, 23, SANS)
    body += (f'<path d="M48 318H1152" stroke="{LINE}" fill="none"/>'
             + text(60, 352, 'CURIOUS ABOUT', MUTED, 16, ls=2)
             + text(230, 353, 'AI-native products · human–computer interaction · product architecture', SOFT, 21, SANS)
             + text(60, 386, 'UNDERSTAND → BUILD → REFINE → SHIP → REPEAT', ORANGE, 17, weight=700, ls=2))
    (OUT / 'toolkit.svg').write_text(frame(
        W, H, 'Toolkit: React, Next.js, TypeScript, Tailwind CSS, Node.js, PostgreSQL, Supabase, Prisma, Redis, Cloudflare, Docker, Vite, Vitest, Git and GitHub',
        'Web: React and Next.js. Mobile: React Native and Expo. Data: PostgreSQL and Supabase. Motion: GSAP and Framer Motion. '
        'Realtime: Node.js and WebSocket. Edge: Cloudflare Workers. Testing: Vitest and Playwright. Curious about AI-native products, '
        'human–computer interaction and product architecture. Understand, build, refine, ship, repeat.', '', body), encoding='utf-8')


# ───────────────────────── marquee and section label ─────────────────────────

def marquee():
    W, H = 1200, 44
    names = [('HAMIYAMI', '#FF7A5C'), ('UNIEXAMER', '#7CE0C3'), ('VIBEASSIST', '#F29BD4'), ('EDBUB / 3RD PLACE', '#E0975A'),
             ('INDUSTRIAL HMI', ORANGE), ('DIGITAL TWIN', '#90DFFF')]
    slot = W / len(names)
    seg = ''
    for copy in range(2):
        for i, (n, c) in enumerate(names):
            x = copy * W + i * slot
            seg += text(round(x + slot / 2, 1), 28, n, c, 15, weight=700, ls=2, extra=' text-anchor="middle"')
            seg += f'<rect x="{x - 3:.1f}" y="19" width="6" height="6" fill="{LINE}" transform="rotate(45 {x:.1f} 22)"/>'
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">'
        '<title id="t">HamiYami, UniExamer, VibeAssist, edbub (3rd place), industrial HMI, digital twin</title>'
        f'<style>@keyframes roll{{to{{transform:translateX(-{W}px)}}}}.roll{{animation:roll 38s linear infinite}}{RM}</style>'
        f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
        f'<linearGradient id="f"><stop stop-color="{BG}"/><stop offset=".1" stop-color="{BG}" stop-opacity="0"/>'
        f'<stop offset=".9" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>'
        f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{BG}"/><g class="roll">{seg}</g>'
        f'<rect width="{W}" height="{H}" fill="url(#f)"/></g>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="11.5" fill="none" stroke="{LINE}"/></svg>'
    )
    (OUT / 'marquee.svg').write_text(svg, encoding='utf-8')


SECTIONS = [('01', 'BUILDING AT INREBUS', 'professional'), ('02', "WHAT I'M BUILDING", 'projects'),
            ('03', 'CONTROL ROOM', 'control'), ('04', 'MY TOOLKIT', 'toolkit')]


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
    print('hamiyami bytes:', hamiyami())
    uniexamer()
    vibeassist()
    edbub()
    work_cards()
    intro()
    buttons()
    fun()
    toolkit()
    footer()
    marquee()
    sections()
    print('done')
