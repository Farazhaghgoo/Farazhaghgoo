"""Render only public GitHub calendar data. Python standard library, no token required."""
import argparse
import datetime as dt
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tips = {}
        self.tip = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date'):
            date = dt.date.fromisoformat(a['data-date'])
            level = int(a['data-level'])
            if not 0 <= level <= 4:
                raise ValueError('Unexpected activity level')
            self.cells[a['id']] = {'date': date.isoformat(), 'level': level}
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
            label = self.tips.get(key, '').strip()
            match = re.match(r'(No|[\d,]+) contributions? on ', label)
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
        if len(set(dates)) != len(dates) or (dates[-1] - dates[0]).days != len(dates)-1:
            raise ValueError('Non-contiguous calendar; preserving previous image')
        return result

def render(days, snapshot):
    def t(x,y,s,size=14,color='#939BA8'):
        return f'<text x="{x}" y="{y}" fill="{color}" font-family="Consolas,monospace" font-size="{size}">{escape(str(s))}</text>'
    def poly(points,fill,stroke='#0B0E14'):
        return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="{fill}" stroke="{stroke}" stroke-width=".8"/>'
    months=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-labelledby="title"><title id="title">Public GitHub contribution landscape for Farazhaghgoo</title>'
    # A slow ripple travels across the weeks; it changes no data and stops under reduced motion.
    s+='<style>@keyframes ripple{0%,14%,100%{transform:none}7%{transform:translateY(-6px)}}.w{animation:ripple 9s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}.pk{animation:pulse 2.4s ease-in-out infinite}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
    s+='<rect width="1200" height="360" rx="16" fill="#0B0E14"/>'
    s+=t(30,36,'PUBLIC CONTRIBUTION LANDSCAPE',16,'#F3EFE5')+t(916,36,'SNAPSHOT / '+snapshot,12)
    s+=t(30,65,days[0]['date']+' → '+days[-1]['date'],12)
    first=dt.date.fromisoformat(days[0]['date'])
    offset=(first.weekday()+1)%7
    colors=['#242D3A','#633624','#A54625','#E15C2D','#FF9B5E']
    def cell(i):
        week,row=divmod(i+offset,7)
        return week,row,40+week*20+row*10,158+row*13
    open_week=None; labels=''; last_label=-99
    for i,d in enumerate(days):
        week,row,x,y=cell(i)
        if week!=open_week:
            s+=('</g>' if open_week is not None else '')+f'<g class="w" style="animation-delay:{week*70}ms">'
            open_week=week
        date=dt.date.fromisoformat(d['date'])
        if date.day==1 and week-last_label>=3 and week<52:
            labels+=t(100+week*20,257,months[date.month-1],11); last_label=week
        h=2+d['level']*17
        s+='<g><title>'+escape(f"{d['date']}: {d['count']} contributions")+'</title>'
        s+=poly([(x,y-h),(x+17,y-h),(x+17,y),(x,y)],'#542B21' if d['level'] else '#18202B')
        s+=poly([(x+17,y-h),(x+25,y-h-9),(x+25,y-9),(x+17,y)],'#883E24' if d['level'] else '#1D2632')
        s+=poly([(x,y-h),(x+8,y-h-9),(x+25,y-h-9),(x+17,y-h)],colors[d['level']])+'</g>'
    s+='</g>'+labels
    total=sum(d['count'] for d in days)
    active=sum(d['count']>0 for d in days)
    streak=run=0
    for d in days:
        run=run+1 if d['count'] else 0
        streak=max(streak,run)
    if total:
        # Flag the busiest public day; ties go to the most recent one.
        best=max(range(len(days)),key=lambda i:(days[i]['count'],i))
        week,row,x,y=cell(best)
        px=x+12.5; py=y-(2+days[best]['level']*17)-4.5
        date=dt.date.fromisoformat(days[best]['date'])
        s+=f'<path d="M{px} {py-4}V72" stroke="#F3EFE5" stroke-width="1" stroke-dasharray="2 3" fill="none"/><circle class="pk" cx="{px}" cy="{py}" r="3" fill="#F3EFE5"/>'
        label=f"PEAK / {months[date.month-1]} {date.day:02d} / {days[best]['count']}"
        s+=f'<text x="{px+8 if px<1000 else px-8}" y="82" text-anchor="{"start" if px<1000 else "end"}" fill="#F3EFE5" font-family="Consolas,monospace" font-size="12">{escape(label)}</text>'
    s+=t(30,285,f'{total} PUBLICLY VISIBLE CONTRIBUTIONS  /  {active} ACTIVE DAYS  /  LONGEST STREAK {streak}',15,'#F3EFE5')
    s+=t(30,317,'Each column = one week. Height = GitHub activity level.',13)
    s+=t(846,285,'LESS',12)
    for i,c in enumerate(colors):s+=f'<rect x="{897+i*27}" y="270" width="20" height="20" rx="3" fill="{c}"/>'
    s+=t(1040,285,'MORE',12)+t(846,317,'SOURCE / GITHUB PUBLIC CALENDAR',11)
    return s+'</svg>'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input', type=Path, help='Local public calendar HTML for reproducible checks')
    p.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1]/'assets')
    args=p.parse_args()
    if args.input:
        html=args.input.read_text(encoding='utf-8')
    else:
        req=Request('https://github.com/users/Farazhaghgoo/contributions',headers={'User-Agent':'Farazhaghgoo-profile-renderer','Accept':'text/html'})
        with urlopen(req,timeout=30) as response:
            html=response.read().decode('utf-8')
    parser=Calendar(); parser.feed(html); days=parser.days()
    today=dt.datetime.now(dt.timezone.utc).date().isoformat()
    image=render(days,today)
    data={'source':'https://github.com/users/Farazhaghgoo/contributions','snapshot':today,'scope':'Publicly visible contribution calendar; not total professional activity','days':days}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'activity.svg').write_text(image,encoding='utf-8')
    (args.output_dir/'activity.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(f'Rendered {len(days)} days, {sum(d["count"] for d in days)} publicly visible contributions.')

if __name__=='__main__':main()
