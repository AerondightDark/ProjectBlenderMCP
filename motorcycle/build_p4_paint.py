"""阶段 4: Sturgis SD Edition 双色涂装 + 印第安人头饰 logo + 侧板 56 号

按实车照片: 挡泥板中央奶油色宽带 + 红色裙边; 油箱下部奶油色;
侧板奶油色底 + 黑色 56; 油箱侧面多色头饰徽标。
"""
import os
import math
import bpy
from mathutils import Vector

import moto_common as C

mt, st, P = C.reload_all()

_SKIP_RENDER = True
_P3 = os.path.join(C.ROOT, 'motorcycle', 'build_p3_controls.py')
exec(compile(open(_P3, encoding='utf-8').read(), _P3, 'exec'))

colls = globals()['colls']
MAT = globals()['MAT']
BD = colls['body']

MAT['paint_cream'] = mt.make_material("Paint_Cream", P.CREAM, roughness=0.18,
                                      metallic=0.0, coat=0.70)
MAT['logo_head'] = mt.make_material("Logo_Head", (0.400, 0.208, 0.092),
                                    roughness=0.42)
MAT['logo_feather'] = mt.make_material("Logo_Feather", (0.845, 0.800, 0.690),
                                       roughness=0.48)
MAT['logo_tip'] = mt.make_material("Logo_Tip", (0.070, 0.068, 0.072),
                                   roughness=0.45)
MAT['number_black'] = mt.make_material("Number_Black", (0.028, 0.028, 0.030),
                                       roughness=0.40)


# ------------------------------------------------------------------ 面级双色分配
def ensure_slots(ob, mats):
    """保证槽 0/1 为指定材质, 返回 (idx0, idx1)"""
    me = ob.data
    while len(me.materials) < len(mats):
        me.materials.append(None)
    for i, m in enumerate(mats):
        me.materials[i] = m
    return (0, 1)


def paint_fender(ob, center_ratio=0.60, nv=30):
    """中央奶油带 + 两侧红色裙边 (按横向参数 v 分配材质)"""
    slots = ensure_slots(ob, [MAT['paint_red'], MAT['paint_cream']])
    me = ob.data
    half = center_ratio * 0.5
    for k, p in enumerate(me.polygons):
        v = (k % nv + 0.5) / float(nv)
        p.material_index = slots[1] if abs(v - 0.5) < half else slots[0]
    return ob


def tank_geometry(t):
    top = mt.interp_table([(0.00, 0.522), (0.06, 0.572), (0.16, 0.596),
                           (0.36, 0.608), (0.58, 0.606), (0.78, 0.584),
                           (0.92, 0.538), (1.00, 0.480)], t)
    bot = mt.interp_table([(0.00, 0.462), (0.10, 0.444), (0.25, 0.422),
                           (0.45, 0.402), (0.65, 0.378), (0.85, 0.352),
                           (1.00, 0.330)], t)
    hw = mt.interp_table([(0.00, 0.058), (0.05, 0.088), (0.14, 0.118),
                          (0.30, 0.142), (0.48, 0.152), (0.66, 0.146),
                          (0.80, 0.128), (0.92, 0.098), (1.00, 0.050)], t)
    return top, bot, hw


def paint_tank(ob):
    """上半/顶部红色, 侧面下部奶油色"""
    slots = ensure_slots(ob, [MAT['paint_red'], MAT['paint_cream']])
    me = ob.data
    span = P.TANK_X1 - P.TANK_X0
    for p in me.polygons:
        c = p.center
        t = (c.x - P.TANK_X0) / span
        top, bot, hw = tank_geometry(max(0.0, min(1.0, t)))
        frac = (c.z - bot) / max(1e-6, top - bot)
        side = abs(c.y) > 0.46 * hw
        p.material_index = slots[1] if (frac < 0.50 and side) else slots[0]
    return ob


paint_fender(bpy.data.objects['Fender_Front'], center_ratio=0.58)
paint_fender(bpy.data.objects['Fender_Rear'], center_ratio=0.62)
paint_tank(bpy.data.objects['Tank_Main'])

# 侧板改奶油色底
for tag in ('L', 'R'):
    ob = bpy.data.objects.get(f"SidePanel_{tag}")
    if ob:
        ob.data.materials.clear()
        ob.data.materials.append(MAT['paint_cream'])


# ------------------------------------------------------------------ 侧板 56 号
for tag, sy in (('L', -1), ('R', 1)):
    bpy.ops.object.text_add(location=(-0.446, sy * 0.0925, 0.286))
    ob = bpy.context.object
    ob.name = f"SidePanel_Number56_{tag}"
    ob.data.name = f"Num56_{tag}"
    ob.data.body = "56"
    ob.data.size = 0.062
    ob.data.extrude = 0.0018
    ob.data.align_x = 'CENTER'
    ob.data.align_y = 'CENTER'
    ob.rotation_euler = ((math.pi * 0.5, 0.0, 0.0) if sy < 0
                         else (math.pi * 0.5, 0.0, math.pi))
    mt.link_to(ob, BD)
    ob.data.materials.append(MAT['number_black'])


# ------------------------------------------------------------------ 油箱头饰徽标
def add_text(name, body, size, loc, rot, mat, coll, font=None):
    bpy.ops.object.text_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.name = name
    ob.data.body = body
    ob.data.size = size
    ob.data.extrude = 0.0016
    ob.data.align_x = 'CENTER'
    ob.data.align_y = 'CENTER'
    if font:
        try:
            ob.data.font = bpy.data.fonts.load(font)
        except Exception:
            pass
    ob.rotation_euler = rot
    mt.link_to(ob, coll)
    ob.data.materials.append(mat)
    return ob


def build_tank_logo(sy, tag):
    """多色印第安人头饰: 面部 + 扇形羽毛 + 羽尖"""
    cx, cz = -0.880, 0.452
    _, _, hw = tank_geometry((cx - P.TANK_X0) / (P.TANK_X1 - P.TANK_X0))
    y0 = sy * (hw + 0.0012)
    head = mt.sphere(f"TankLogo_Head_{tag}", 1.0, (cx, y0, cz), 20, 12,
                     MAT['logo_head'], BD)
    head.scale = (0.027, 0.0062, 0.033)
    n = 9
    for i in range(n):
        a = math.radians(18.0 + 144.0 * i / (n - 1))
        r = 0.046
        fx = cx + r * math.cos(a)
        fz = cz + r * math.sin(a)
        f = mt.sphere(f"TankLogo_Feather_{tag}_{i:02d}", 1.0, (fx, y0, fz),
                      14, 8, MAT['logo_feather'], BD)
        f.scale = (0.040, 0.0048, 0.0125)
        f.rotation_euler = (0.0, -a, 0.0)
        r2 = r + 0.036
        tx = cx + r2 * math.cos(a)
        tz = cz + r2 * math.sin(a)
        t = mt.sphere(f"TankLogo_Tip_{tag}_{i:02d}", 1.0, (tx, y0, tz),
                      10, 6, MAT['logo_tip'], BD)
        t.scale = (0.014, 0.0046, 0.0102)
        t.rotation_euler = (0.0, -a, 0.0)
    band = mt.sphere(f"TankLogo_Band_{tag}", 1.0, (cx, y0, cz - 0.038), 16, 8,
                     MAT['logo_tip'], BD)
    band.scale = (0.034, 0.0046, 0.0085)


build_tank_logo(-1, 'L')
build_tank_logo(+1, 'R')

# 油箱 "Indian" 手写体
SCRIPT_FONT = 'C:/Windows/Fonts/BRUSHSCI.TTF'
for tag, sy in (('L', -1), ('R', 1)):
    _, _, hw = tank_geometry((-1.020 - P.TANK_X0) / (P.TANK_X1 - P.TANK_X0))
    add_text(f"TankScript_{tag}", "Indian", 0.052,
             (-1.020, sy * (hw + 0.0022), 0.552),
             ((math.pi * 0.5, 0.0, 0.0) if sy < 0
              else (math.pi * 0.5, 0.0, math.pi)),
             MAT['number_black'], BD, SCRIPT_FONT)


# ------------------------------------------------------------------ 输出
ground = globals()['ground']
shots = C.render_views('p4', names=('left', 'right', 'front', 'q34f',
                                    'q34r', 'top'))
C.save()

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
result = {
    'stage': 4,
    'shots': shots,
    'objects': len(bpy.data.objects),
    'length': round(size.x, 4),
    'width': round(size.y, 4),
    'height': round(size.z, 4),
    'target': {'length': P.OVERALL_L, 'width': P.OVERALL_W,
               'height': P.OVERALL_H},
}
