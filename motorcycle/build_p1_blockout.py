"""阶段 1: 整车比例骨架

车轮(胎+辋+毂+盘) / 前叉+三角台 / 车架主结构 / 后摇臂 / 油箱 /
前后裙式挡泥板曲面 / 座椅 / 发动机尺寸占位
目标: 把整车比例、车架、油箱与挡泥板曲面先定下来。
"""
import math
import bpy
from mathutils import Vector

import moto_common as C

mt, st, P = C.reload_all()

colls = C.new_scene()
MAT = C.build_materials()


# ------------------------------------------------------------------ 车轮
def build_wheel(tag, axle, rim_r, tire_h, tire_w, rim_w, hub_r, hub_w, coll,
                disc_side=-1):
    axle = tuple(axle)
    parts = []
    parts.append(mt.tire(f"Wheel_{tag}_Tire", rim_r, tire_h, tire_w,
                         mat=MAT['rubber'], coll=coll, segments=84,
                         center=axle))
    rw = rim_w * 0.5
    rim_prof = [(rim_r, -rw), (rim_r - 0.030, -rw), (rim_r - 0.030, -rw * 0.45),
                (rim_r - 0.048, -rw * 0.45), (rim_r - 0.048, rw * 0.45),
                (rim_r - 0.030, rw * 0.45), (rim_r - 0.030, rw), (rim_r, rw)]
    parts.append(mt.revolve(f"Wheel_{tag}_Rim", rim_prof, 84,
                            MAT['frame_black'], coll, True, axle, axis='Y'))
    hub_prof = [(-hub_w * 0.5, hub_r * 0.5), (-hub_w * 0.5, hub_r),
                (-hub_w * 0.28, hub_r * 1.06), (hub_w * 0.28, hub_r * 1.06),
                (hub_w * 0.5, hub_r), (hub_w * 0.5, hub_r * 0.5)]
    parts.append(mt.revolve(f"Wheel_{tag}_Hub", hub_prof, 40,
                            MAT['frame_black'], coll, True, axle, axis='Y'))
    # 298 mm 制动盘
    disc_r = 0.298 * 0.5
    disc_y = axle[1] + disc_side * (rw + 0.014)
    parts.append(mt.revolve(
        f"Wheel_{tag}_Disc",
        [(-0.0035, disc_r * 0.40), (-0.0035, disc_r), (0.0035, disc_r),
         (0.0035, disc_r * 0.40)],
        72, MAT['steel'], coll, True, (axle[0], disc_y, axle[2]), axis='Y'))
    # 制动卡钳
    cal = mt.rounded_box(f"Brake_Caliper_{tag}", (0.075, 0.052, 0.115),
                         (axle[0] + 0.02, disc_y - 0.030, axle[2] + 0.115),
                         (0, 0, 0), 0.012, 3, MAT['engine_black'], coll)
    parts.append(cal)
    return parts


build_wheel("Front", P.AXLE_F, P.RIM_R, P.TIRE_H_F, P.TIRE_W_F, P.RIM_W_F,
            P.HUB_R_F, P.HUB_W_F, colls['wheels'], disc_side=-1)
build_wheel("Rear", P.AXLE_R, P.RIM_R, P.TIRE_H_R, P.TIRE_W_R, P.RIM_W_R,
            P.HUB_R_R, P.HUB_W_R, colls['wheels'], disc_side=+1)


# ------------------------------------------------------------------ 前叉
FORK_W = 0.1010           # 前叉中心距之半 (中心距 202 mm)


def build_fork():
    c = colls['frame']
    for side, sy in (('L', -1), ('R', 1)):
        off = sy * FORK_W
        # 外管 (下)
        mt.pipe(f"Fork_Lower_{side}",
                [P.on_axis(0.040, off_y=off), P.on_axis(0.470, off_y=off)],
                0.023, MAT['frame_black'], c, sides=32, smooth_path=False)
        # 护罩: 覆盖内管, 上端接三角台
        mt.pipe(f"Fork_Shroud_{side}",
                [P.on_axis(0.408, off_y=off),
                 P.on_axis(P.T_CLAMP_HI, off_y=off)],
                0.0282, MAT['frame_black'], c, sides=28, smooth_path=False)
        # 顶盖 (上三角台上方少许)
        mt.pipe(f"Fork_TopCap_{side}",
                [P.on_axis(P.T_CLAMP_HI + 0.012, off_y=off),
                 P.on_axis(P.T_CLAMP_HI + 0.040, off_y=off)],
                0.0235, MAT['frame_black'], c, sides=20, smooth_path=False)
        # 轮轴安装座
        mt.rounded_box(f"Fork_AxleMount_{side}", (0.066, 0.034, 0.056),
                       P.on_axis(0.062, off_y=off), (0, 0, 0), 0.010, 3,
                       MAT['frame_black'], c)
        # 下护板 (fender 安装座)
        mt.rounded_box(f"Fork_FenderMount_{side}", (0.050, 0.026, 0.038),
                       P.on_axis(0.300, off_y=off), (0, 0, 0), 0.008, 2,
                       MAT['frame_black'], c)
    for name, t, th in (("TripleClamp_Lower", P.T_CLAMP_LO, 0.030),
                        ("TripleClamp_Upper", P.T_CLAMP_HI, 0.024)):
        ob = mt.rounded_box(name, (0.070, P.CLAMP_W, th), P.on_axis(t),
                            (0, 0, 0), 0.011, 3, MAT['frame_black'], c)
        ob.rotation_euler = (0.0, -P.RAKE, 0.0)
    mt.pipe("SteeringHead_Tube",
            [P.on_axis(P.T_NECK - P.HEAD_TUBE_LEN * 0.5),
             P.on_axis(P.T_NECK + P.HEAD_TUBE_LEN * 0.5)],
            0.0335, MAT['frame_black'], c, sides=24, smooth_path=False)


build_fork()


# ------------------------------------------------------------------ 车架
def build_frame():
    c = colls['frame']
    r = P.FRAME_R
    mt.pipe("Frame_Backbone", P.TOP_TUBE, r, MAT['frame_black'], c, sides=20)
    mt.pipe("Frame_DownTube", P.DOWN_TUBE, r, MAT['frame_black'], c, sides=20)
    for side, sy in (('L', -1), ('R', 1)):
        mt.pipe(f"Frame_Cradle_{side}",
                [(p[0], p[1] + sy * 0.100, p[2]) for p in P.CRADLE],
                r * 0.92, MAT['frame_black'], c, sides=18)
        mt.pipe(f"Frame_SeatPost_{side}",
                [(p[0], p[1] + sy * 0.096, p[2]) for p in P.SEAT_TUBE],
                r * 0.92, MAT['frame_black'], c, sides=18)
        # 下管 -> 摇篮的过渡接头
        mt.rounded_box(f"Frame_DownJoint_{side}", (0.070, 0.034, 0.052),
                       (-0.930, sy * 0.055, -0.186), (0, 0, 0), 0.010, 2,
                       MAT['frame_black'], c)
    # 后摇臂枢轴横管
    mt.pipe("Frame_PivotTube",
            [(P.PIVOT[0], -P.PIVOT_Y - 0.014, P.PIVOT[2]),
             (P.PIVOT[0], P.PIVOT_Y + 0.014, P.PIVOT[2])],
            0.021, MAT['frame_black'], c, sides=18, smooth_path=False)
    # 座椅支撑横管
    mt.pipe("Frame_SeatBrace",
            [(-0.356, -0.104, 0.302), (-0.356, 0.104, 0.302)],
            0.012, MAT['frame_black'], c, sides=14, smooth_path=False)


build_frame()


# ------------------------------------------------------------------ 后摇臂
def build_swingarm():
    c = colls['frame']
    for side, sy in (('L', -1), ('R', 1)):
        pts = [(p[0], p[1] * sy, p[2]) for p in P.SWINGARM]
        mt.pipe(f"Swingarm_{side}", pts, P.SWINGARM_R, MAT['frame_black'],
                c, sides=18)
        mt.rounded_box(f"Swingarm_AxleBlock_{side}", (0.075, 0.040, 0.052),
                       (0.062, sy * 0.098, -0.014), (0, 0, 0), 0.010, 3,
                       MAT['frame_black'], c)
    mt.rounded_box("Swingarm_Brace", (0.046, 0.230, 0.028),
                   (-0.108, 0.0, -0.154), (0, 0, 0), 0.008, 2,
                   MAT['frame_black'], c)
    mt.pipe("RearAxle", [(0.0, -0.122, 0.0), (0.0, 0.122, 0.0)],
            0.011, MAT['chrome'], c, sides=16, smooth_path=False)
    # 后避震 (双)
    for side, sy in (('L', -1), ('R', 1)):
        top = Vector((P.SHOCK_TOP[0], P.SHOCK_TOP[1] * sy, P.SHOCK_TOP[2]))
        bot = Vector((P.SHOCK_BOT[0], P.SHOCK_BOT[1] * sy, P.SHOCK_BOT[2]))
        mt.pipe(f"Shock_{side}", [tuple(bot), tuple(top)], 0.019,
                MAT['engine_black'], c, sides=18, smooth_path=False)
        mt.pipe(f"Shock_Spring_{side}",
                [tuple(bot + (top - bot) * 0.14),
                 tuple(bot + (top - bot) * 0.90)],
                0.029, MAT['chrome'], c, sides=20, smooth_path=False)


build_swingarm()


# ------------------------------------------------------------------ 油箱
def tank_profile(t):
    """t=0 前端 -> 1 后端; 返回 (顶 z, 底 z, 半宽)

    底部跟随车架上管的下降坡度, 使油箱骑在管上而不是切入管中。
    """
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


def build_tank():
    nu, nv = 40, 56
    rings = []
    for i in range(nu + 1):
        t = i / float(nu)
        x = P.TANK_X0 + (P.TANK_X1 - P.TANK_X0) * t
        top, bot, hw = tank_profile(t)
        cz, hz = (top + bot) * 0.5, (top - bot) * 0.5
        ring = []
        for j in range(nv):
            a = mt.TAU * j / nv
            ca, sa = math.cos(a), math.sin(a)
            e = 2.0 / 2.30
            y = hw * math.copysign(abs(ca) ** e, ca)
            zz = cz + hz * math.copysign(abs(sa) ** e, sa)
            # 底部中央隧道: 让油箱跨在上管上
            if zz < cz:
                w = (cz - zz) / hz
                ty = abs(y) / P.TANK_TUNNEL_W
                if ty < 1.0:
                    zz += P.TANK_TUNNEL * (1.0 - ty * ty) * (w * w)
            ring.append((x, y, zz))
        rings.append(ring)
    return mt.loft_rings("Tank_Main", rings, MAT['paint_red'], colls['body'],
                         True, True, True)


build_tank()


# ------------------------------------------------------------------ 挡泥板
def build_fender(name, axle, r_in, width, start_deg, arc_deg, sag, drop,
                 mat, coll, nu=64, nv=30, skirt_pow=2.35, forward=True,
                 taper=0.84, tail_extend=0.0):
    """裙式挡泥板: 绕轮轴的部分回转曲面, 两侧裙边下垂, 端部整体下垂成鼻

    tail_extend: 水平方向(角度 0)的半径外扩比例, 形成尾部鸭嘴延伸
    """
    a0 = math.radians(start_deg)
    arc = math.radians(arc_deg)
    sgn = -1.0 if forward else 1.0

    def fn(u, v):
        th = a0 + arc * u
        s = -1.0 + 2.0 * v
        e = abs(2.0 * u - 1.0)
        end = e ** 2.4
        ct = max(0.0, math.cos(th))
        r = (r_in * (1.0 + tail_extend * ct ** 1.7) - drop * end
             - sag * (1.0 + 0.35 * end) * (abs(s) ** skirt_pow))
        w = width * 0.5 * (1.0 - (1.0 - taper) * (abs(s) ** 3.0))
        return (axle[0] + sgn * r * math.cos(th), axle[1] + s * w,
                axle[2] + r * math.sin(th))

    ob = mt.grid_surface(name, fn, nu, nv, mat=mat, coll=coll, smooth=True,
                         merge=1e-5)
    mt.add_solidify(ob, P.FENDER_T, offset=0.0)
    return ob


build_fender("Fender_Front", P.AXLE_F, P.R_TIRE_F + P.FENDER_GAP_F,
             P.FENDER_W_F, P.FENDER_START_F, P.FENDER_ARC_F,
             P.FENDER_SAG_F, P.FENDER_DROP_F, MAT['paint_red'],
             colls['body'], forward=True, taper=P.FENDER_TAPER_F,
             tail_extend=P.FENDER_TAIL_F)
build_fender("Fender_Rear", P.AXLE_R, P.R_TIRE_R + P.FENDER_GAP_R,
             P.FENDER_W_R, P.FENDER_START_R, P.FENDER_ARC_R,
             P.FENDER_SAG_R, P.FENDER_DROP_R, MAT['paint_red'],
             colls['body'], forward=False, taper=P.FENDER_TAPER_R,
             tail_extend=P.FENDER_TAIL_R)


# ------------------------------------------------------------------ 座椅
def build_seat():
    nu, nv = 32, 30
    rings = []
    for i in range(nu + 1):
        t = i / float(nu)
        x = P.SEAT_X0 + (P.SEAT_X1 - P.SEAT_X0) * t
        hw = mt.interp_table([(0.00, 0.026), (0.08, 0.056), (0.22, 0.098),
                              (0.42, 0.132), (0.58, P.SEAT_W), (0.78, 0.146),
                              (0.90, 0.124), (1.00, 0.086)], t)
        top = mt.interp_table([(0.00, P.SEAT_Z - 0.030), (0.10, P.SEAT_Z - 0.014),
                               (0.28, P.SEAT_Z - 0.002), (0.48, P.SEAT_Z - 0.005),
                               (0.66, P.SEAT_Z + 0.012), (0.84, P.SEAT_Z + 0.030),
                               (1.00, P.SEAT_Z + 0.044)], t)
        thick = mt.interp_table([(0.00, 0.032), (0.20, 0.058), (0.45, 0.070),
                                 (0.70, 0.072), (0.88, 0.060), (1.00, 0.046)], t)
        cz, hz = top - thick * 0.5, thick * 0.5
        ring = []
        for j in range(nv):
            a = mt.TAU * j / nv
            ca, sa = math.cos(a), math.sin(a)
            e = 2.0 / 2.30
            y = hw * math.copysign(abs(ca) ** e, ca)
            z = cz + hz * math.copysign(abs(sa) ** e, sa)
            ring.append((x, y, z))
        rings.append(ring)
    seat = mt.loft_rings("Seat_Solo", rings, MAT['leather'], colls['body'],
                         True, True, True)
    # 悬浮座支架: 车架上管 -> 座垫底部
    for side, sy in (('L', -1), ('R', 1)):
        mt.pipe(f"Seat_Bracket_{side}",
                [(-0.334, sy * 0.086, 0.290), (-0.248, sy * 0.060, 0.312)],
                0.011, MAT['frame_black'], colls['body'], sides=12,
                smooth_path=False)
    return seat


build_seat()


# ------------------------------------------------------------------ 侧板
def build_side_panels():
    """座椅下方 / 油箱后方的三角形盖板 (Sturgis 版左侧带 56 号)"""
    c = colls['body']
    outline = [(-0.540, 0.344), (-0.316, 0.362), (-0.274, 0.234),
               (-0.498, 0.216)]
    for side, sy in (('L', -1), ('R', 1)):
        mt.plate(f"SidePanel_{side}", outline, 0.013,
                 (0.0, sy * 0.086, 0.0), (sy * 0.07, 0.0, 0.0),
                 MAT['paint_red'], c)


build_side_panels()


# ------------------------------------------------------------------ 发动机 (尺寸占位)
def build_engine_block():
    c = colls['engine']
    base = Vector(P.CRANK)
    mt.rounded_box("Engine_Crankcase",
                   (P.CRANKCASE_L, P.CRANKCASE_W, P.CRANKCASE_H),
                   P.CRANK, (0, 0, 0), 0.048, 5, MAT['engine_black'], c)
    # 变速箱壳体 (曲轴箱 -> 摇臂枢轴前), 顶部低于曲轴箱形成台阶
    mt.rounded_box("Engine_Transmission", (0.300, 0.224, 0.170),
                   (-0.480, 0.0, -0.072), (0, 0, 0), 0.044, 4,
                   MAT['engine_black'], c)
    # 曲轴箱前后圆盖 (右侧)
    mt.revolve("Engine_PrimaryCover",
               [(-0.014, 0.062), (-0.014, 0.132), (0.018, 0.132),
                (0.018, 0.062)],
               44, MAT['engine_black'], c, True,
               (P.CRANK[0] + 0.020, P.CRANKCASE_W * 0.5 + 0.008,
                P.CRANK[2] - 0.020), axis='Y')
    # 变速箱侧盖 (右侧离合器盖)
    mt.revolve("Engine_ClutchCover",
               [(-0.012, 0.048), (-0.012, 0.098), (0.016, 0.098),
                (0.016, 0.048)],
               40, MAT['engine_black'], c, True,
               (-0.472, 0.232 * 0.5 + 0.006, -0.050), axis='Y')
    for tag, d, rot_y in (("Front", P.CYL_F_DIR, -P.V_ANGLE * 0.5),
                          ("Rear", P.CYL_R_DIR, P.V_ANGLE * 0.5)):
        cyl = mt.finned_tube(f"Engine_Cylinder_{tag}", 0.0, P.CYL_LEN,
                             P.CYL_CORE_R, P.CYL_FIN_R, P.FIN_GAP, P.FIN_TH,
                             44, MAT['engine_black'], c, False)
        cyl.location = tuple(base + Vector(d) * P.CYL_Z0)
        cyl.rotation_euler = (0.0, rot_y, 0.0)
        cyl.scale = (1.14, 1.0, 1.0)
        head = mt.finned_tube(f"Engine_Head_{tag}", 0.0, P.HEAD_LEN,
                              P.HEAD_CORE_R, P.HEAD_FIN_R, P.HEAD_FIN_GAP,
                              P.HEAD_FIN_TH, 44, MAT['turbo_silver'], c, False)
        head.location = tuple(base + Vector(d) * P.HEAD_Z0)
        head.rotation_euler = (0.0, rot_y, 0.0)
        head.scale = (1.16, 1.0, 1.0)
        mt.rounded_box(f"Engine_RockerCover_{tag}",
                       (0.112, P.ROCKER_W, P.ROCKER_LEN),
                       tuple(base + Vector(d) * (P.HEAD_Z0 + P.HEAD_LEN
                                                 + P.ROCKER_LEN * 0.5)),
                       (0.0, rot_y, 0.0), 0.013, 3,
                       MAT['engine_black'], c)
    # 空滤盖 (右侧, V 型夹角中)
    air_c = base + Vector((0.086, P.CRANKCASE_W * 0.5 + 0.048, 0.108))
    mt.revolve("Engine_AirCleaner",
               [(-0.016, 0.032), (-0.016, P.AIR_CLEANER_D * 0.5),
                (0.030, P.AIR_CLEANER_D * 0.5), (0.030, 0.032)],
               44, MAT['engine_black'], c, True, tuple(air_c), axis='Y')
    # 曲轴箱侧盖 (左侧)
    mt.revolve("Engine_CaseCover_L",
               [(-0.014, 0.056), (-0.014, P.CASE_COVER_R), (0.016,
                                                            P.CASE_COVER_R),
                (0.016, 0.056)],
               44, MAT['engine_black'], c, True,
               (P.CRANK[0] + 0.030, -(P.CRANKCASE_W * 0.5 + 0.008),
                P.CRANK[2] - 0.012), axis='Y')


build_engine_block()


# ------------------------------------------------------------------ 输出
ground = C.setup_look(colls)
C.save()
shots = []
if not globals().get('_SKIP_RENDER'):
    shots = C.render_views('p1', names=('left', 'front', 'right', 'q34f',
                                        'top'))

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
result = {
    'stage': 1,
    'objects': len(bpy.data.objects),
    'bbox_min': [round(v, 4) for v in lo],
    'bbox_max': [round(v, 4) for v in hi],
    'length': round(size.x, 4),
    'width': round(size.y, 4),
    'height': round(size.z, 4),
    'target': {'length': P.OVERALL_L, 'width': P.OVERALL_W,
               'height': P.OVERALL_H},
}
