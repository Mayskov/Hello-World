import re, math, sys

SRC = sys.argv[1]
OUT = sys.argv[2]
K = 1.8656497
X0, Y0 = 4438.997, 10377.995

svg = open(SRC).read()
paths = re.findall(r'<path[^>]*>', svg)
base = []
for p in paths:
    st = re.search(r'stroke="([^"]*)"', p)
    if not st or st.group(1) == 'rgb(100%, 0%, 0%)':
        continue  # skip red dimension lines
    d = re.search(r' d="([^"]*)"', p).group(1)
    c = st.group(1)
    if c.startswith('rgb(0%, 0%, 0%)'):
        base.append(f'<path d="{d}" class="w"/>')
    elif c.startswith('rgb(38'):
        base.append(f'<path d="{d}" class="h"/>')
    else:
        base.append(f'<path d="{d}" class="win"/>')
walls = f'<g transform="matrix({K},0,0,{-K},{-X0*K},{Y0*K})">' + '\n'.join(base) + '</g>'

out = []
def rect(x, y, w, h, label='', cls='f', fs=100, rot=None, sub='', vert=False):
    t = f' transform="rotate({rot} {x+w/2} {y+h/2})"' if rot else ''
    s = f'<g{t}><rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>'
    if vert:
        s += f'<g transform="rotate(-90 {x+w/2} {y+h/2})">'
    if label:
        lines = label.split('|')
        n = len(lines) + (1 if sub else 0)
        cy = y + h/2 - (n-1)*fs*0.6
        for i, ln in enumerate(lines):
            s += f'<text x="{x+w/2}" y="{cy+i*fs*1.2}" font-size="{fs}" class="lb">{ln}</text>'
        if sub:
            s += f'<text x="{x+w/2}" y="{cy+len(lines)*fs*1.2}" font-size="{fs*0.8}" class="sub">{sub}</text>'
    if vert:
        s += '</g>'
    s += '</g>'
    out.append(s)

def circle(cx, cy, r, cls='f'):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="{cls}"/>')

def door(hx, hy, closed, opn, L):
    ex, ey = hx+closed[0]*L, hy+closed[1]*L
    ox, oy = hx+opn[0]*L, hy+opn[1]*L
    cross = closed[0]*opn[1]-closed[1]*opn[0]
    sweep = 1 if cross > 0 else 0
    out.append(f'<path d="M{ex},{ey} A{L},{L} 0 0 {sweep} {ox},{oy}" class="arc"/>'
               f'<line x1="{hx}" y1="{hy}" x2="{ox}" y2="{oy}" class="leaf"/>')

def text(x, y, s, fs=150, cls='room'):
    out.append(f'<text x="{x}" y="{y}" font-size="{fs}" class="{cls}">{s}</text>')

def dim(x1, y1, x2, y2, label, off=0):
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="clr" marker-start="url(#a)" marker-end="url(#a)"/>')
    mx, my = (x1+x2)/2, (y1+y2)/2
    vert = abs(x1-x2) < abs(y1-y2)
    if vert:
        out.append(f'<text x="{mx+60}" y="{my}" font-size="85" class="clrt" transform="rotate(-90 {mx+60} {my})">{label}</text>')
    else:
        out.append(f'<text x="{mx}" y="{my-40}" font-size="85" class="clrt">{label}</text>')

import math
exec(open('furn.py').read())

# двери в жилые комнаты
door(5440, 3367, (0, -1), (-1, 0), 800)      # детская
door(5636, 3886, (1, 0), (0, 1), 800)        # спальня

# проёмы без дверей
out.append('<line x1="10879" y1="5367" x2="10879" y2="6563" class="arch"/>')
out.append('<line x1="10870" y1="9763" x2="10870" y2="10935" class="arch"/>')

# ---------------- контрольные размеры проходов
dim(3800, 1300, 3800, 3185, '1885')
dim(4000, 4386, 4000, 5232, '846')
dim(4800, 5232, 6612, 5232, '≥1 800 (проход к гардеробной)')
dim(12300, 9119, 12300, 10219, '1100')
dim(14100, 10700, 15026, 10700, '926')
dim(14800, 4360, 14800, 7423, '≈3 060 до ТВ')
dim(8370, 9200, 10475, 9200, '2105')
dim(6200, 3800, 6200, 2297, '1503')
dim(13700, 11660, 13700, 13060, '≈1400')

body = '\n'.join(out)

# легенда и примечания (пустая область слева внизу)
notes = [
 ('b', 'Расстановка мебели — семья 4 чел. (родители + 2 мальчика)'),
 ('', 'Стены, окна и все размеры помещений перенесены 1:1 из обмерного плана (AutoCAD).'),
 ('', 'Мебель — условные обозначения CAD-блоков (вид сверху) в реальных габаритах, мм. Сетка 1 м.'),
 ('b', 'Принятые нормы и правила'),
 ('', '• основные проходы ≥ 900 мм, второстепенные ≥ 700, перед шкафами ≥ 800;'),
 ('', '• двери жилых комнат открываются внутрь и «к стене», зоны открывания свободны;'),
 ('', '• двери санузлов — наружу (безопасность), входная — наружу (пожарные нормы);'),
 ('', '• кухня: проход у рабочего фронта 1000–1200; треугольник холодильник–мойка–плита;'),
 ('', '• стол: 750–800 мм за стулом; ТВ-дистанция ≈ 3 м (для 65″);'),
 ('', '• унитаз: ≥ 600 перед ним и ≥ 200–250 по бокам; рабочие места со светом слева.'),
 ('b', 'Допущения — уточнить'),
 ('', '• стояки/вентканалы не указаны: назначение ванной, постирочной и места'),
 ('', '  плиты/мойки принято условно — проверить по факту;'),
 ('', '• комната 2,70×2,40 доступна только из спальни → принята гардеробной;'),
 ('', '• проёмы в гостиную и кухню — без дверей (арка), можно поставить раздвижные.'),
]
leg = ['<g>']
y = 8900
leg.append(f'<rect x="200" y="8550" width="6250" height="{len(notes)*215+1700}" class="card"/>')
for kind, s in notes:
    if kind == 'b':
        y += 90
        leg.append(f'<text x="420" y="{y}" font-size="135" class="hd">{s}</text>')
    else:
        leg.append(f'<text x="420" y="{y}" font-size="98" class="nt">{s}</text>')
    y += 205
# цветовая легенда
y += 1080
from sym import place, sofa, bed, wardrobe, shelf, wc, bathtub, hob, armchair
samples=[(sofa,1000,450,'диван'),(armchair,450,450,'кресло'),(bed,650,1000,'кровать'),(wardrobe,800,350,'шкаф'),(shelf,600,300,'стеллаж'),(bathtub,850,400,'ванна'),(wc,300,450,'унитаз'),(hob,500,500,'варочная')]
x=420
for fn,w,h,n in samples:
    leg.append(place(fn,x,y-h-60,w,h))
    leg.append(f'<text x="{x+w/2}" y="{y+90}" font-size="85" class="nt" text-anchor="middle">{n}</text>')
    x+=w+110
leg.append('</g>')

grid = []
for gx in range(0, 18001, 1000):
    grid.append(f'<line x1="{gx}" y1="-200" x2="{gx}" y2="16600" class="g"/>')
for gy in range(0, 16601, 1000):
    grid.append(f'<line x1="-200" y1="{gy}" x2="18000" y2="{gy}" class="g"/>')

# масштабная линейка
scale = '<g>' + ''.join(
    f'<rect x="{800+i*500}" y="15700" width="500" height="80" fill="{"#333" if i%2==0 else "#fff"}" stroke="#333" stroke-width="10"/>'
    for i in range(6)) + '<text x="800" y="15650" font-size="100" class="nt">0</text><text x="3800" y="15650" font-size="100" class="nt">3 м</text></g>'

css = '''
.w{fill:none;stroke:#1d1d1f;stroke-width:9}
.h{fill:none;stroke:#8a8a8a;stroke-width:4}
.win{fill:none;stroke:#2f7fd6;stroke-width:5}
.g{stroke:#e6e9ee;stroke-width:6}
.f{fill:#f3e7d3;stroke:#7a5a2e;stroke-width:12}
.f2{fill:#e2d3b8;stroke:#7a5a2e;stroke-width:8}
.bed{fill:#dce8f7;stroke:#3d5f8c;stroke-width:12}
.pil{fill:#fff;stroke:#3d5f8c;stroke-width:8}
.st{fill:#e7e1f3;stroke:#5a4a86;stroke-width:12}
.kt{fill:#dff0e3;stroke:#2f7a45;stroke-width:12}
.hob{fill:none;stroke:#2f7a45;stroke-width:10}
.wet{fill:#dff1f6;stroke:#24788f;stroke-width:12}
.rug{fill:#f8efe6;stroke:#d8b99a;stroke-width:8;stroke-dasharray:40 30}
.ch{fill:#fff;stroke:#7a5a2e;stroke-width:10}
.pl{fill:#d9eed0;stroke:#4f8a3a;stroke-width:10}
.sl{fill:#fff;stroke:#5a4a86;stroke-width:10}
.arc{fill:none;stroke:#c0392b;stroke-width:9;stroke-dasharray:30 25}
.leaf{stroke:#c0392b;stroke-width:22}
.arch{stroke:#c0392b;stroke-width:12;stroke-dasharray:60 40}
.clr{stroke:#e67e22;stroke-width:9}
.clrt{fill:#c96a12;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;font-weight:bold}
.lb{fill:#2b2b2b;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;dominant-baseline:middle}
.sub{fill:#666;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;dominant-baseline:middle;font-style:italic}
.room{fill:#1d1d1f;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;font-weight:bold;letter-spacing:8}
.rs{fill:#555;font-family:'DejaVu Sans',sans-serif;text-anchor:middle}
.hd{fill:#1d1d1f;font-family:'DejaVu Sans',sans-serif;font-weight:bold}
.nt{fill:#333;font-family:'DejaVu Sans',sans-serif}
.card{fill:#fbfbfc;stroke:#cfd4dc;stroke-width:10}

.up{fill:#efe4d2;stroke:#5b4630;stroke-width:12}
.up2{fill:#e2d2b9;stroke:#5b4630;stroke-width:10}
.cush{fill:#f7efe3;stroke:#8a6f4e;stroke-width:7}
.ghost{fill:none;stroke:#8a6f4e;stroke-width:7;stroke-dasharray:40 30}
.ghostl{stroke:#3d5f8c;stroke-width:7;stroke-dasharray:50 35}
.ghostf{fill:#fbf7f0;stroke:#8a6f4e;stroke-width:8;stroke-dasharray:35 25}
.dot{fill:#8a6f4e}
.wood{fill:#ead8bd;stroke:#6b4f2c;stroke-width:12}
.mat{fill:#fff;stroke:#3d5f8c;stroke-width:10}
.pillow{fill:#f4f7fb;stroke:#3d5f8c;stroke-width:8}
.blanket{fill:#dbe6f4;stroke:#3d5f8c;stroke-width:9}
.fold{fill:#f4f7fb;stroke:#3d5f8c;stroke-width:8}
.d{stroke:#5b4630;stroke-width:9;fill:none}
.dt{stroke:#8a7a66;stroke-width:5;fill:none}
.d0{fill:none;stroke:#4a6f80;stroke-width:7}
.door{stroke:#5a4a86;stroke-width:14}
.rod{stroke:#5a4a86;stroke-width:12}
.store{fill:#ece7f5;stroke:#5a4a86;stroke-width:12}
.tv{fill:#2b2b2b}
.tv2{fill:#6b6b6b}
.lamp{fill:#fff6cf;stroke:#b0902a;stroke-width:8}
.mirror{fill:#cfe6f2;stroke:#4a7d97;stroke-width:6}
.dec{fill:#fff;stroke:#8a7a66;stroke-width:6}
.paper{fill:#fff;stroke:#9a8a76;stroke-width:5}
.seat{fill:#f7efe3;stroke:#6b4f2c;stroke-width:9}
.backarc{fill:none;stroke:#3b3b3b;stroke-width:40;stroke-linecap:round}
.glass{fill:#eef6f8;stroke:#8aa7b0;stroke-width:6}
.grain{stroke:#c9ad86;stroke-width:5}
.pot{fill:#e9f2e2;stroke:#4f8a3a;stroke-width:8}
.leaf{fill:#9ccb7f;stroke:#4f8a3a;stroke-width:5}
.rug{fill:#f6ece0;stroke:#cfae8b;stroke-width:8}
.rug2{fill:none;stroke:#dcc2a5;stroke-width:6;stroke-dasharray:25 20}
.fr{stroke:#cfae8b;stroke-width:4}
.san{fill:#fff;stroke:#24788f;stroke-width:10}
.water{fill:#e3f3f8;stroke:#24788f;stroke-width:8}
.chrome{fill:#c9d3d8;stroke:#5e7480;stroke-width:5}
.tile{fill:#f2f8fa;stroke:#9cc3cf;stroke-width:5}
.glassl{stroke:#4aa3c4;stroke-width:16}
.app{fill:#f4f6f7;stroke:#4d5a61;stroke-width:10}
.app2{fill:#e2e7ea;stroke:#4d5a61;stroke-width:6}
.drum{fill:#dde6ea;stroke:#4d5a61;stroke-width:8}
.counter{fill:#e3efe6;stroke:#2f6b45;stroke-width:10}
.glassdark{fill:#3a3f44;stroke:#222;stroke-width:6}
.burner{fill:none;stroke:#c9cfd4;stroke-width:8}
.slider{fill:#fff;stroke:#5a4a86;stroke-width:10}
.symt{fill:#4d5a61;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;dominant-baseline:middle}
.cap{fill:#444;font-family:'DejaVu Sans',sans-serif;text-anchor:middle;font-style:italic;paint-order:stroke;stroke:#fff;stroke-width:22;stroke-linejoin:round}
.title{fill:#1d1d1f;font-family:'DejaVu Sans',sans-serif;font-weight:bold}
'''
marker = '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e67e22"/></marker></defs>'
doc = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-300 -900 18300 17700" width="1830mm" height="1770mm">
<style>{css}</style>{marker}
<rect x="-300" y="-900" width="18300" height="17700" fill="#fff"/>
{''.join(grid)}
<text x="0" y="-450" font-size="260" class="title">План расстановки мебели</text>
<text x="0" y="-180" font-size="130" class="nt">4-комнатная квартира · масштаб по обмерному плану · размеры в мм</text>
{walls}
{body}
{''.join(leg)}
{scale}
</svg>'''
open(OUT, 'w').write(doc)
print('ok', len(doc))
