"""Библиотека 2D-символов мебели (вид сверху) в стиле CAD-блоков.

Каждый символ рисуется в локальной системе: ширина W вдоль стены,
глубина D от стены (v=0 — спинка/стена, v=D — лицевая сторона).
place() разворачивает символ так, чтобы лицевая сторона смотрела
в нужную сторону: 'down', 'up', 'left', 'right'.
"""
import math

def _frame(x, y, w, h, front):
    if front == 'down':
        return f'translate({x},{y})', w, h
    if front == 'up':
        return f'translate({x+w},{y+h}) rotate(180)', w, h
    if front == 'right':
        return f'translate({x},{y+h}) rotate(-90)', h, w
    if front == 'left':
        return f'translate({x+w},{y}) rotate(90)', h, w
    raise ValueError(front)

def place(fn, x, y, w, h, front='down', **kw):
    t, W, D = _frame(x, y, w, h, front)
    return f'<g transform="{t}">' + fn(W, D, **kw) + '</g>'

def place_rot(fn, cx, cy, w, h, ang, **kw):
    """Символ с центром (cx,cy), повёрнутый на ang градусов (front='down' при ang=0)."""
    return f'<g transform="translate({cx},{cy}) rotate({ang}) translate({-w/2},{-h/2})">' + fn(w, h, **kw) + '</g>'

def R(x, y, w, h, cls, rx=0):
    r = f' rx="{rx}"' if rx else ''
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"{r} class="{cls}"/>'

def L(x1, y1, x2, y2, cls='d'):
    return f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" class="{cls}"/>'

def C(cx, cy, r, cls):
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" class="{cls}"/>'

def E(cx, cy, rx, ry, cls):
    return f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" class="{cls}"/>'

# ---------------------------------------------------------------- мягкая мебель
def sofa(W, D, seats=3):
    arm = min(180, W*0.1); back = D*0.24
    s = R(0, 0, W, D, 'up', 60)
    s += R(0, 0, W, back, 'up2', 50)                    # спинка
    s += R(0, 0, arm, D, 'up2', 50) + R(W-arm, 0, arm, D, 'up2', 50)  # подлокотники
    sw = (W-2*arm)/seats
    for i in range(seats):
        x = arm + i*sw
        s += R(x+12, back+12, sw-24, D-back-30, 'cush', 50)        # подушки сиденья
        s += R(x+20, back*0.25, sw-40, back*0.9, 'cush', 40)       # подушки спинки
    return s

def armchair(W, D):
    return sofa(W, D, 1)

def sofa_bed(W, D):
    s = sofa(W, D, 2)
    # пунктиром — разложенное спальное место
    s += R(W*0.08, D, W*0.84, 1050, 'ghost')
    return s

def bench(W, D):
    s = R(0, 0, W, D, 'up', 50)
    n = max(2, int(W // 250))
    for i in range(n):
        for j in (0.35, 0.65):
            s += C(W*(i+0.5)/n, D*j, 14, 'dot')
    return s

# ---------------------------------------------------------------- кровати
def bed(W, D, pillows=2, head=80):
    s = R(0, 0, W, head, 'wood')                                   # изголовье
    s += R(20, head, W-40, D-head-10, 'mat', 30)                   # матрас
    pw = (W-40-60*(pillows+1))/pillows
    for i in range(pillows):
        s += R(20+60+i*(pw+60), head+70, pw, 330, 'pillow', 70)
    fold = head + 70 + 330 + 140
    s += R(20, fold, W-40, D-head-10-(fold-head), 'blanket', 30)    # одеяло
    s += f'<path d="M20,{fold} L20,{fold+260} L{W*0.28:.0f},{fold} Z" class="fold"/>'
    return s

def bunk(W, D):
    s = bed(W, D, pillows=1, head=60)
    s += L(0, 0, W, D, 'ghostl') + L(W, 0, 0, D, 'ghostl')          # верхний ярус
    # лестница по длинной стороне
    lx = W*0.62
    s += L(lx, D-10, lx, D+110, 'd') + L(lx+380, D-10, lx+380, D+110, 'd')
    for k in range(3):
        s += L(lx, D+10+k*45, lx+380, D+10+k*45, 'dt')
    return s

# ---------------------------------------------------------------- хранение
def wardrobe(W, D, sliding=True):
    s = R(0, 0, W, D, 'store')
    s += L(60, D*0.45, W-60, D*0.45, 'rod')                        # штанга
    step = 140
    n = int((W-200)//step)
    for i in range(n):
        x = 100 + i*step
        s += L(x-55, D*0.45-D*0.28, x+55, D*0.45+D*0.28, 'dt')     # плечики
    if sliding:
        s += L(30, D-35, W/2+40, D-35, 'door') + L(W/2-40, D-75, W-30, D-75, 'door')
    return s

def shelf(W, D, step=400):
    s = R(0, 0, W, D, 'store')
    n = max(1, int(round(W/step)))
    for i in range(1, n):
        s += L(W*i/n, 0, W*i/n, D, 'd')
    for i in range(n):
        s += L(W*i/n, 0, W*(i+1)/n, D, 'dt')
    return s

def dresser(W, D, tv=False):
    s = R(0, 0, W, D, 'wood')
    n = max(2, int(W//450))
    for i in range(1, n):
        s += L(W*i/n, 0, W*i/n, D, 'dt')
    for i in range(n):
        s += L(W*(i+0.5)/n-60, D-40, W*(i+0.5)/n+60, D-40, 'd')    # ручки
    if tv:
        tw = min(W*0.85, 1450)
        s += R((W-tw)/2, D*0.35, tw, 55, 'tv') + R(W/2-160, D*0.35+55, 320, 90, 'tv2')
    return s

def nightstand(W, D):
    s = R(0, 0, W, D, 'wood')
    s += L(W/2-60, D-35, W/2+60, D-35, 'd')
    s += C(W/2, D*0.45, min(W, D)*0.24, 'lamp') + L(W/2-70, D*0.45, W/2+70, D*0.45, 'dt') + L(W/2, D*0.45-70, W/2, D*0.45+70, 'dt')
    return s

def console(W, D):
    s = R(0, 0, W, D, 'wood')
    s += R(W*0.1, -30, W*0.8, 30, 'mirror')                        # зеркало на стене
    s += C(W*0.8, D*0.5, 60, 'dec')
    return s

# ---------------------------------------------------------------- столы и стулья
def desk(W, D, seats=1, lamp=True):
    s = R(0, 0, W, D, 'wood')
    for i in range(seats):
        cx = W*(i+0.5)/seats
        s += R(cx-260, 70, 520, 45, 'tv') + R(cx-60, 115, 120, 60, 'tv2')   # монитор
        s += R(cx-210, D*0.55, 420, 150, 'paper', 15)                       # клавиатура/тетрадь
    if lamp:
        s += C(W-120, 120, 75, 'lamp')
    return s

def dressing_table(W, D):
    s = R(0, 0, W, D, 'wood')
    s += R(W*0.2, -30, W*0.6, 30, 'mirror')
    s += C(W*0.2, D*0.4, 45, 'dec') + C(W*0.3, D*0.35, 30, 'dec')
    return s

def chair(W, D):
    """Стул: сиденье + спинка (спинка у v=0)."""
    s = R(W*0.08, D*0.18, W*0.84, D*0.8, 'seat', 60)
    s += R(0, 0, W, D*0.18, 'wood', 40)
    return s

def office_chair(W, D):
    cx, cy = W/2, D/2
    s = ''
    for k in range(5):
        a = math.radians(90 + k*72)
        s += L(cx, cy, cx+math.cos(a)*W*0.5, cy+math.sin(a)*W*0.5, 'dt')
        s += C(cx+math.cos(a)*W*0.5, cy+math.sin(a)*W*0.5, 22, 'dot')
    s += R(W*0.12, D*0.2, W*0.76, D*0.7, 'seat', 120)
    s += f'<path d="M{W*0.1:.0f},{D*0.28:.0f} Q{W/2:.0f},{-D*0.05:.0f} {W*0.9:.0f},{D*0.28:.0f}" class="backarc"/>'
    return s

def stool(W, D):
    return C(W/2, D/2, W/2, 'seat') + C(W/2, D/2, W*0.32, 'd0')

def coffee_table(W, D):
    return R(0, 0, W, D, 'wood', 30) + R(60, 60, W-120, D-120, 'glass', 20)

def table(W, D):
    return R(0, 0, W, D, 'wood', 30) + L(W*0.08, D/2, W*0.92, D/2, 'grain')

def round_table(W, D):
    return C(W/2, D/2, W/2, 'wood') + C(W/2, D/2, W*0.12, 'dec')

# ---------------------------------------------------------------- ТВ, декор
def tv_unit(W, D):
    s = R(0, 0, W, D, 'wood')
    n = max(2, int(W//600))
    for i in range(1, n):
        s += L(W*i/n, 0, W*i/n, D, 'dt')
    tw = min(W*0.7, 1450)
    s += R((W-tw)/2, 40, tw, 50, 'tv') + R(W/2-180, 90, 360, 110, 'tv2')
    return s

def plant(W, D):
    r = W/2; s = C(r, r, r, 'pot')
    for k in range(8):
        a = math.radians(k*45)
        s += E(r+math.cos(a)*r*0.5, r+math.sin(a)*r*0.5, r*0.45, r*0.18, 'leaf').replace('/>', f' transform="rotate({k*45} {r+math.cos(a)*r*0.5:.0f} {r+math.sin(a)*r*0.5:.0f})"/>')
    return s

def floor_lamp(W, D):
    r = W/2
    return C(r, r, r, 'lamp') + L(r*0.3, r, r*1.7, r, 'dt') + L(r, r*0.3, r, r*1.7, 'dt')

def rug(W, D):
    s = R(0, 0, W, D, 'rug', 20) + R(90, 90, W-180, D-180, 'rug2', 10)
    for i in range(int(W//80)+1):
        x = i*80
        s += L(x, -40, x, 0, 'fr') + L(x, D, x, D+40, 'fr')
    return s

def rug_oval(W, D):
    return E(W/2, D/2, W/2, D/2, 'rug') + E(W/2, D/2, W/2-100, D/2-100, 'rug2')

# ---------------------------------------------------------------- сантехника
def bathtub(W, D):
    s = R(0, 0, W, D, 'san', 40)
    s += R(70, 70, W-140, D-140, 'water', (D-140)/2.2)
    s += C(W-200, D/2, 28, 'd0')                                   # слив
    s += R(W-60, D/2-45, 40, 90, 'chrome')                         # смеситель
    return s

def vanity(W, D, bowls=1):
    s = R(0, 0, W, D, 'san')
    for i in range(bowls):
        cx = W*(i+0.5)/bowls
        s += E(cx, D*0.55, min(W/bowls*0.36, 230), D*0.3, 'water')
        s += C(cx, D*0.55, 18, 'd0') + R(cx-15, 30, 30, 70, 'chrome')
    return s

def wc(W, D):
    s = R(W*0.05, 0, W*0.9, D*0.3, 'san', 20)                      # бачок/инсталляция
    s += E(W/2, D*0.62, W*0.42, D*0.37, 'san')
    s += E(W/2, D*0.62, W*0.28, D*0.25, 'water')
    return s

def shower(W, D):
    s = R(0, 0, W, D, 'san')
    s += R(40, 40, W-80, D-80, 'tile')
    s += L(40, 40, W-40, D-40, 'dt') + L(W-40, 40, 40, D-40, 'dt')
    s += C(W/2, D/2, 45, 'chrome')
    s += L(0, D-15, W*0.55, D-15, 'glassl')                        # стеклянная перегородка
    return s

def washer(W, D, label='СМ'):
    s = R(0, 0, W, D, 'app', 30)
    s += R(40, 25, W-80, 70, 'app2') + C(W/2, D*0.58, min(W, D)*0.3, 'drum') + C(W/2, D*0.58, min(W, D)*0.2, 'd0')
    return s

def utility_sink(W, D):
    s = R(0, 0, W, D, 'counter')
    s += R(W*0.55, 60, W*0.38, D-120, 'water', 40) + R(W*0.74-15, 20, 30, 60, 'chrome')
    return s

def towel_cab(W, D):
    s = R(0, 0, W, D, 'wood')
    for k in range(3):
        s += R(40, 40+k*(D-80)/3, W-80, (D-80)/3-25, 'paper', 20)
    return s

def ironing(W, D):
    s = f'<path d="M{W*0.15:.0f},{D*0.02:.0f} L{W*0.85:.0f},{D*0.02:.0f} L{W*0.85:.0f},{D*0.8:.0f} Q{W/2:.0f},{D*1.02:.0f} {W*0.15:.0f},{D*0.8:.0f} Z" class="ghostf"/>'
    return s

def dryer_rack(W, D):
    s = R(0, 0, W, D, 'ghostf')
    for i in range(1, 8):
        s += L(W*i/8, 0, W*i/8, D, 'dt')
    return s

# ---------------------------------------------------------------- кухня
def counter(W, D):
    return R(0, 0, W, D, 'counter') + L(0, D-40, W, D-40, 'dt')

def fridge(W, D):
    s = R(0, 0, W, D, 'app', 20) + L(40, D-60, W-40, D-60, 'd')
    s += L(W*0.2, D-60, W*0.2, D-20, 'd') + L(W*0.8, D-60, W*0.8, D-20, 'd')
    s += f'<text x="{W/2}" y="{D*0.45}" class="symt" font-size="120">❄</text>'
    return s

def oven_col(W, D):
    return R(0, 0, W, D, 'app', 20) + R(60, 60, W-120, D-140, 'app2', 20) + L(80, D-50, W-80, D-50, 'd')

def hob(W, D):
    s = counter(W, D)
    s += R(40, 40, W-80, D-110, 'glassdark', 20)
    for (fx, fy, r) in ((0.3, 0.3, 95), (0.7, 0.3, 70), (0.3, 0.7, 70), (0.7, 0.7, 95)):
        s += C(40+(W-80)*fx, 40+(D-110)*fy, r, 'burner') + C(40+(W-80)*fx, 40+(D-110)*fy, r*0.5, 'burner')
    return s

def kitchen_sink(W, D):
    s = counter(W, D)
    s += R(60, 90, W*0.55, D-180, 'water', 40) + C(60+W*0.275, D/2, 25, 'd0')
    for k in range(5):
        x = W*0.68 + k*(W*0.27/5)
        s += L(x, 110, x, D-110, 'dt')
    s += R(60+W*0.275-15, 25, 30, 70, 'chrome')
    return s

def island(W, D):
    s = R(0, 0, W, D, 'counter', 20) + L(30, D*0.62, W-30, D*0.62, 'dt')
    return s
