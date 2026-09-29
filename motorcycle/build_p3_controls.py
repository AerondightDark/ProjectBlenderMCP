"""阶段 3: 排气系统 + 车灯组 + 车把与把手件 + 脚踏板

在阶段 2 之上追加。
"""
import os
import math
import bpy
from mathutils import Vector

import moto_common as C

mt, st, P = C.reload_all()

_SKIP_RENDER = True
_P2 = os.path.join(C.ROOT, 'motorcycle', 'build_p2_engine_wheels.py')
exec(compile(open(_P2, encoding='utf-8').read(), _P2, 'exec'))

colls = globals()['colls']
MAT = globals()['MAT']
MAT['rubber_grip'] = mt.make_material("Rubber_Grip", (0.020, 0.020, 0.022),
                                      roughness=0.78)
MAT['amber_lens'] = mt.make_material("Lens_Amber", (0.820, 0.330, 0.040),
                                     roughness=0.10, emission=(0.85, 0.30, 0.03),
                                     emission_strength=0.55)

EX = colls['exhaust']
CT = colls['controls']
LT = colls['lights']
BD = colls['body']

# ------------------------------------------------------------------ 排气
PIPE_R = 0.0285
pipe_lower = [(-0.878, 0.110, 0.148), (-0.872, 0.136, 0.018),
              (-0.850, 0.150, -0.118), (-0.720, 0.156, -0.196),
              (-0.420, 0.158, -0.222), (-0.060, 0.158, -0.224),
              (0.196, 0.154, -0.218)]
pipe_upper = [(-0.690, 0.110, 0.148), (-0.684, 0.136, 0.030),
              (-0.664, 0.150, -0.098), (-0.548, 0.156, -0.150),
              (-0.280, 0.158, -0.164), (-0.020, 0.158, -0.166),
              (0.196, 0.154, -0.162)]

mt.pipe("Exhaust_FrontCyl", pipe_lower, PIPE_R, MAT['engine_black'], EX,
        sides=22, samples=5)
mt.pipe("Exhaust_RearCyl", pipe_upper, PIPE_R, MAT['engine_black'], EX,
        sides=22, samples=5)
# 消声器尾段 (略粗) 与斜切端面
for tag, pts in (("Lower", pipe_lower), ("Upper", pipe_upper)):
    tail = Vector(pts[-1])
    prev = Vector(pts[-2])
    d = (tail - prev).normalized()
    mt.pipe(f"Exhaust_Tip_{tag}", [tuple(tail - d * 0.170), tuple(tail)],
            PIPE_R * 1.16, MAT['engine_black'], EX, sides=22,
            smooth_path=False)
# 排气口 (前缸) 与隔热罩
for tag, y in (("Front", 0.112), ("Rear", 0.112)):
    c = (-0.878, y, 0.150) if tag == "Front" else (-0.690, y, 0.150)
    mt.revolve(f"Exhaust_PortFlange_{tag}",
               [(-0.010, 0.030), (-0.010, 0.046), (0.010, 0.046),
                (0.010, 0.030)], 24, MAT['turbo_silver'], EX, True, c)

# ------------------------------------------------------------------ 大灯
HL_BASE = Vector(P.on_axis(0.612))
HL_C = (HL_BASE.x - 0.050, 0.0, HL_BASE.z + 0.008)
# 整流壳 (nacelle): 前端大开口 -> 后端收锥
mt.revolve("Headlight_Nacelle",
           [(-0.070, 0.096), (-0.046, 0.099), (0.006, 0.090), (0.040, 0.066),
            (0.058, 0.042)], 40, MAT['frame_black'], LT, True, HL_C, axis='X')
# 大灯支架 (连接前叉)
for sy in (-1, 1):
    mt.rounded_box(f"Headlight_Bracket_{'L' if sy < 0 else 'R'}",
                   (0.052, 0.030, 0.026),
                   (HL_C[0] + 0.048, sy * 0.070, HL_C[2]), (0, 0, 0), 0.008, 2,
                   MAT['frame_black'], LT)
# 灯圈
mt.revolve("Headlight_Bezel",
           [(0.058, 0.076), (0.058, 0.092), (0.078, 0.090), (0.078, 0.074)],
           40, MAT['chrome'], LT, True, HL_C, axis='X')
# 反射碗 (大端朝前, 填满灯壳开口)
mt.revolve("Headlight_Reflector",
           [(-0.064, 0.090), (-0.048, 0.082), (-0.014, 0.058), (0.014, 0.034),
            (0.030, 0.024)], 40, MAT['chrome'], LT, True, HL_C, axis='X')
# 灯泡
mt.sphere("Headlight_Bulb", 0.020, (HL_C[0] + 0.006, 0.0, HL_C[2]), 16, 10,
          MAT['chrome'], LT)
# 玻璃 (微凸)
mt.revolve("Headlight_Lens",
           [(-0.072, 0.0), (-0.066, 0.062), (-0.060, 0.088),
            (-0.058, 0.092), (-0.058, 0.0)], 40, MAT['glass'], LT, True,
           HL_C, axis='X')
# 灯壳顶部印第安人头饰
mt.rounded_box("Headlight_Ornament", (0.030, 0.026, 0.018),
               (HL_C[0] - 0.030, 0.0, HL_C[2] + 0.100), (0, 0, 0), 0.006, 2,
               MAT['brass'], LT)

# ------------------------------------------------------------------ 转向灯
for tag, sy in (('L', -1), ('R', 1)):
    # 前转向灯 (装在前叉上)
    fp = Vector(P.on_axis(0.540, off_y=sy * 0.120))
    mt.pipe(f"TurnSignal_Front_{tag}",
            [tuple(fp), tuple(fp + Vector((0.0, sy * 0.026, 0.0)))],
            0.010, MAT['frame_black'], LT, sides=14, smooth_path=False)
    mt.sphere(f"TurnSignal_FrontLens_{tag}", 0.032, tuple(
        fp + Vector((0.0, sy * 0.046, 0.0))), 24, 14, MAT['amber_lens'],
        LT, True, (1.0, 1.0, 0.9))
    # 后转向灯 (后挡泥板后部两侧)
    mt.pipe(f"TurnSignal_Rear_{tag}",
            [(0.362, sy * 0.086, 0.010), (0.352, sy * 0.128, 0.008)],
            0.010, MAT['frame_black'], LT, sides=14, smooth_path=False)
    mt.sphere(f"TurnSignal_RearLens_{tag}", 0.029,
              (0.348, sy * 0.150, 0.007), 24, 14, MAT['amber_lens'], LT,
              True, (1.0, 1.0, 0.9))

# 尾灯 (后挡泥板末端)
mt.revolve("Taillight_Housing",
           [(-0.026, 0.030), (-0.026, 0.052), (0.020, 0.056), (0.020, 0.032)],
           32, MAT['frame_black'], LT, True, (0.404, 0.0, -0.030), axis='X')
mt.sphere("Taillight_Lens", 0.040, (0.428, 0.0, -0.030), 24, 16,
          MAT['red_lamp'], LT, True, (0.55, 1.0, 1.0))
mt.rounded_box("Taillight_Bracket", (0.058, 0.060, 0.070),
               (0.372, 0.0, -0.052), (0, 0, 0), 0.010, 2,
               MAT['frame_black'], LT)

# ------------------------------------------------------------------ 车把
RISER_TOP = Vector(P.on_axis(P.T_CLAMP_HI + 0.024))
for tag, sy in (('L', -1), ('R', 1)):
    mt.pipe(f"Handlebar_Riser_{tag}",
            [tuple(RISER_TOP + Vector((0.0, sy * 0.056, 0.004))),
             tuple(RISER_TOP + Vector((0.0, sy * 0.056, P.BAR_RISER_H)))],
            0.017, MAT['frame_black'], CT, sides=18, smooth_path=False)
    mt.hex_bolt(f"Handlebar_RiserBolt_{tag}", 0.013, 0.016,
                tuple(RISER_TOP + Vector((0.0, sy * 0.056,
                                          P.BAR_RISER_H + 0.004))),
                (0.0, 0.0, 0.0), MAT['chrome'], CT)

BAR_Z = RISER_TOP.z + P.BAR_RISER_H
right_path = [(RISER_TOP.x, 0.060, BAR_Z),
              (RISER_TOP.x - 0.006, 0.108, BAR_Z + 0.006),
              (RISER_TOP.x + 0.028, 0.196, BAR_Z + 0.002),
              (RISER_TOP.x + 0.120, 0.286, BAR_Z - 0.016),
              (RISER_TOP.x + 0.228, 0.342, BAR_Z - 0.036),
              (RISER_TOP.x + 0.336, 0.366, BAR_Z - 0.048)]
for tag, sy in (('L', -1), ('R', 1)):
    path = [(p[0], p[1] * sy, p[2]) for p in right_path]
    mt.pipe(f"Handlebar_{tag}", path, P.BAR_TUBE_R, MAT['frame_black'], CT,
            sides=18, samples=6)
    # 握把
    g0 = Vector(path[-2]).lerp(Vector(path[-1]), 0.24)
    g1 = Vector(path[-1]) + (Vector(path[-1]) - Vector(path[-2])).normalized() * 0.030
    mt.pipe(f"Handlebar_Grip_{tag}", [tuple(g0), tuple(g1)], 0.0195,
            MAT['rubber_grip'], CT, sides=20, smooth_path=False)
    # 制动/离合主缸
    m0 = Vector(path[-2]).lerp(Vector(path[-1]), 0.02)
    mt.rounded_box(f"Handlebar_Switch_{tag}", (0.052, 0.040, 0.030),
                   tuple(m0 + Vector((0.0, sy * 0.028, 0.012))),
                   (0, 0, 0), 0.008, 2, MAT['frame_black'], CT)
    mt.pipe(f"Handlebar_Lever_{tag}",
            [tuple(m0 + Vector((0.0, sy * 0.040, 0.010))),
             tuple(m0 + Vector((0.052, sy * 0.086, 0.006)))],
            0.0068, MAT['chrome'], CT, sides=12, smooth_path=False)

# ------------------------------------------------------------------ 后视镜
for tag, sy in (('L', -1), ('R', 1)):
    base = Vector((right_path[4][0], right_path[4][1] * sy,
                   right_path[4][2]))
    stem_top = base + Vector((-0.024, sy * 0.122, P.MIRROR_STEM_H))
    mt.pipe(f"Mirror_Stem_{tag}", [tuple(base), tuple(stem_top)], 0.0068,
            MAT['frame_black'], CT, sides=12, samples=2)
    mt.revolve(f"Mirror_Housing_{tag}",
               [(-0.010, 0.0), (-0.010, P.MIRROR_R), (0.006, P.MIRROR_R)],
               32, MAT['frame_black'], CT, True, tuple(stem_top +
                                                       Vector((0.006, 0.0, 0.0))),
               axis='X')
    mt.revolve(f"Mirror_Glass_{tag}",
               [(0.004, 0.0), (0.004, P.MIRROR_R * 0.94)],
               32, MAT['chrome'], CT, True,
               tuple(stem_top + Vector((0.010, 0.0, 0.0))), axis='X')

# ------------------------------------------------------------------ 脚踏板
for tag, sy in (('L', -1), ('R', 1)):
    mt.rounded_box(f"Floorboard_{tag}", (0.330, 0.128, 0.020),
                   (-0.884, sy * 0.172, -0.196), (0, sy * 0.045, 0), 0.008, 3,
                   MAT['frame_black'], CT)
    mt.pipe(f"Floorboard_Bracket_{tag}",
            [(-0.884, sy * 0.106, -0.196), (-0.884, sy * 0.150, -0.196)],
            0.014, MAT['frame_black'], CT, sides=14, smooth_path=False)
    # 制动/换挡杆
    mt.pipe(f"Floorboard_Pedal_{tag}",
            [(-0.750, sy * 0.150, -0.150), (-0.700, sy * 0.186, -0.176),
             (-0.660, sy * 0.196, -0.190)],
            0.0095, MAT['chrome'], CT, sides=12, samples=3)
    mt.pipe(f"Floorboard_Peg_{tag}",
            [(-0.660, sy * 0.196, -0.190), (-0.644, sy * 0.200, -0.190)],
            0.014, MAT['rubber_grip'], CT, sides=14, smooth_path=False)

# ------------------------------------------------------------------ 油箱盖
mt.revolve("FuelCap",
           [(-0.010, 0.020), (-0.010, 0.038), (0.012, 0.042), (0.016, 0.030)],
           28, MAT['chrome'], BD, True, (-0.760, 0.0, 0.606), axis='Z')


# ------------------------------------------------------------------ 输出
ground = globals()['ground']
shots = C.render_views('p3', names=('left', 'right', 'front', 'q34f',
                                    'q34r'))
C.save()

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
result = {
    'stage': 3,
    'shots': shots,
    'objects': len(bpy.data.objects),
    'length': round(size.x, 4),
    'width': round(size.y, 4),
    'height': round(size.z, 4),
    'target': {'length': P.OVERALL_L, 'width': P.OVERALL_W,
               'height': P.OVERALL_H},
}
