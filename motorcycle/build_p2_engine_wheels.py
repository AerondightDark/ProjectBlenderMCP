"""阶段 2: V 型双缸发动机细化 + 辐条轮毂 + 悬挂/制动/皮带传动

先重建阶段 1, 再在其上追加机械部件。
"""
import os
import math
import bpy
from mathutils import Vector

import moto_common as C

mt, st, P = C.reload_all()

_SKIP_RENDER = True
_P1 = os.path.join(C.ROOT, 'motorcycle', 'build_p1_blockout.py')
exec(compile(open(_P1, encoding='utf-8').read(), _P1, 'exec'))

colls = globals()['colls']
MAT = globals()['MAT']
MAT['spoke_steel'] = mt.make_material("Spoke_Steel", (0.052, 0.053, 0.058),
                                      roughness=0.42, metallic=0.70)
MAT['brass'] = mt.make_material("Brass_Detail", (0.285, 0.198, 0.072),
                                roughness=0.46, metallic=0.85)


# ------------------------------------------------------------------ 辐条
for tag, axle, hub_r, hub_w, rim_w in (
        ('Front', P.AXLE_F, P.HUB_R_F, P.HUB_W_F, P.RIM_W_F),
        ('Rear', P.AXLE_R, P.HUB_R_R, P.HUB_W_R, P.RIM_W_R)):
    mt.spoke_set(f"Wheel_{tag}_Spokes", axle, P.RIM_R, hub_r, hub_w, rim_w,
                 count=40, cross=2, radius=0.0033, sides=6,
                 mat=MAT['spoke_steel'], coll=colls['wheels'],
                 rim_inset=0.030, hub_side=0.44, rim_side=0.30)


# ------------------------------------------------------------------ 发动机细节
ENG = colls['engine']
BASE = Vector(P.CRANK)
CYL_SET = (("Front", Vector(P.CYL_F_DIR), -P.V_ANGLE * 0.5),
           ("Rear", Vector(P.CYL_R_DIR), P.V_ANGLE * 0.5))

for tag, d, rot_y in CYL_SET:
    # 推杆管 (气缸前后两侧)
    for k in (-1, 1):
        off = Vector((k * 0.100, 0.0, 0.0))
        p0 = BASE + d * 0.086 + off
        p1 = BASE + d * 0.252 + off
        mt.pipe(f"Engine_Pushrod_{tag}_{'A' if k < 0 else 'B'}",
                [tuple(p0), tuple(p1)], 0.0072, MAT['engine_black'], ENG,
                sides=8, smooth_path=False)
    # 火花塞 (缸头两侧)
    sp = BASE + d * (P.HEAD_Z0 + 0.024)
    for k in (-1, 1):
        p0 = (sp.x - k * 0.010, k * 0.086, sp.z)
        p1 = (sp.x - k * 0.022, k * 0.118, sp.z)
        mt.pipe(f"Engine_SparkPlug_{tag}_{'L' if k < 0 else 'R'}",
                [p0, p1], 0.0098, MAT['engine_black'], ENG, sides=10,
                smooth_path=False)
    # 缸头盖压紧螺栓
    for k in (-1, 1):
        c = BASE + d * (P.HEAD_Z0 + P.HEAD_LEN + P.ROCKER_LEN * 0.5)
        n = Vector((0.0, k * 1.0, 0.0))
        mt.hex_bolt(f"Engine_RockerBolt_{tag}_{'L' if k < 0 else 'R'}",
                    0.0085, 0.011, tuple(c + n * (P.ROCKER_W * 0.5)),
                    (math.pi * 0.5 * (1 if k > 0 else -1), 0.0, 0.0),
                    MAT['engine_black'], ENG, washer=False)

# 曲轴箱盖上的印第安人头徽 (金色圆盘)
EMB = (P.CRANK[0] + 0.020, P.CRANKCASE_W * 0.5 + 0.023, P.CRANK[2] - 0.018)
mt.revolve("Engine_CaseEmblem",
           [(-0.0030, 0.0), (-0.0030, 0.040), (0.0030, 0.040)],
           40, MAT['brass'], ENG, True, EMB, axis='Y')
mt.revolve("Engine_CaseEmblemRing",
           [(-0.0035, 0.040), (-0.0035, 0.052), (0.0035, 0.052),
            (0.0035, 0.040)], 44, MAT['engine_black'], ENG, True, EMB,
           axis='Y')

# 空滤盖镀铬环 + 中心盘
AIR = Vector((P.CRANK[0] + 0.086, P.CRANKCASE_W * 0.5 + 0.030,
              P.CRANK[2] + 0.104))
mt.revolve("Engine_AirCleanerRing",
           [(-0.003, 0.050), (-0.003, 0.058), (0.004, 0.058), (0.004, 0.050)],
           48, MAT['chrome'], ENG, True,
           tuple(AIR + Vector((0.0, 0.026, 0.0))), axis='Y')
mt.revolve("Engine_AirCleanerCap",
           [(-0.003, 0.0), (-0.003, 0.021), (0.005, 0.021), (0.005, 0.0)],
           32, MAT['chrome'], ENG, True,
           tuple(AIR + Vector((0.0, 0.028, 0.0))), axis='Y')

# 节气门体 (V 型夹角内 -> 空滤)
mt.pipe("Engine_ThrottleBody",
        [tuple(BASE + Vector((-0.010, 0.0, 0.116))),
         tuple(BASE + Vector((0.052, 0.108, 0.112)))],
        0.031, MAT['engine_black'], ENG, sides=20, samples=2)

# 发动机安装耳
for sy in (-1, 1):
    mt.rounded_box(f"Engine_MountFront_{'L' if sy < 0 else 'R'}",
                   (0.056, 0.030, 0.062),
                   (-0.876, sy * 0.112, -0.112), (0, 0, 0), 0.010, 2,
                   MAT['engine_black'], ENG)
    mt.rounded_box(f"Engine_MountRear_{'L' if sy < 0 else 'R'}",
                   (0.052, 0.028, 0.056),
                   (-0.404, sy * 0.100, -0.088), (0, 0, 0), 0.009, 2,
                   MAT['engine_black'], ENG)


# ------------------------------------------------------------------ 制动卡钳
mt.remove_objects("Brake_Caliper")
for _me in list(bpy.data.meshes):
    if _me.users == 0:
        bpy.data.meshes.remove(_me)
for tag, axle, disc_side, rim_w, ang_deg in (
        ('Front', P.AXLE_F, -1, P.RIM_W_F, 128.0),
        ('Rear', P.AXLE_R, +1, P.RIM_W_R, -152.0)):
    disc_y = axle[1] + disc_side * (rim_w * 0.5 + 0.014)
    a = math.radians(ang_deg)
    c = (axle[0] + 0.113 * math.cos(a), disc_y,
         axle[2] + 0.113 * math.sin(a))
    cal = mt.rounded_box(f"Brake_Caliper_{tag}", (0.074, 0.054, 0.100), c,
                         (0.0, math.pi * 0.5 - a, 0.0), 0.014, 3,
                         MAT['engine_black'], colls['wheels'])
    del cal


# ------------------------------------------------------------------ 皮带传动 (左侧)
PULLEY_Y = -0.152          # 皮带须落在摇臂外侧
REAR_P = (0.0, PULLEY_Y, 0.0)
FRONT_P = (-0.420, PULLEY_Y, -0.078)
mt.revolve("Drive_RearPulley",
           [(-0.015, 0.062), (-0.015, 0.118), (0.015, 0.116), (0.015, 0.060)],
           56, MAT['frame_black'], colls['frame'], True, REAR_P, axis='Y')
mt.revolve("Drive_RearPulleyInner",
           [(-0.018, 0.038), (-0.018, 0.064), (0.018, 0.064), (0.018, 0.038)],
           40, MAT['frame_black'], colls['frame'], True, REAR_P, axis='Y')
# 皮带轮 -> 轮毂 连接筒
mt.revolve("Drive_PulleySpacer",
           [(-0.092, 0.046), (-0.092, 0.062), (-0.016, 0.062), (-0.016, 0.046)],
           32, MAT['frame_black'], colls['frame'], True, REAR_P, axis='Y')
mt.revolve("Drive_FrontPulley",
           [(-0.014, 0.040), (-0.014, 0.072), (0.014, 0.070), (0.014, 0.038)],
           44, MAT['frame_black'], colls['frame'], True, FRONT_P, axis='Y')
mt.belt_loop("Drive_Belt", REAR_P, 0.118, FRONT_P, 0.070, 0.030, 0.0092,
             MAT['engine_black'], colls['frame'], plane='XZ', segments=34)


# ------------------------------------------------------------------ 输出
ground = globals()['ground']
shots = C.render_views('p2', names=('left', 'right', 'q34f', 'q34r'))
C.save()

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
result = {
    'stage': 2,
    'shots': shots,
    'objects': len(bpy.data.objects),
    'length': round(size.x, 4),
    'width': round(size.y, 4),
    'height': round(size.z, 4),
    'stats': st.object_stats()['verts'],
}
