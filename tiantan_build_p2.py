"""天坛祈年殿 - 第二部分: 殿身 / 斗拱 / 三重蓝色攒尖屋顶 / 金色宝顶
运行本文件即可完成全部建模 (内部会重新执行 part1)
"""
import bpy
import math
import sys
import importlib

ROOT = r"D:\work\AI\BlenderMCPTest\try1"
sys.path.insert(0, ROOT)
import tiantan_lib as L
importlib.reload(L)
from tiantan_lib import TAU

# ---- 重新构建地基/台基/柱网, 保证可重复运行 ----
ns = {}
exec(compile(open(ROOT + r"\tiantan_build_p1.py", encoding="utf-8").read(),
             "p1", "exec"), ns)
COLL, MAT = ns["COLL"], ns["MAT"]
PLATFORM_TOP = ns["PLATFORM_TOP"]
COL_R_OUT, COL_R_MID, COL_R_IN, COL_D = (ns["COL_R_OUT"], ns["COL_R_MID"],
                                         ns["COL_R_IN"], ns["COL_D"])
ARCH_TOP = [12.80, 19.75, 26.15]        # 三层柱顶(斗拱底)标高

# ---- 屋顶关键标高 ----
EAVE = [(10.60, 13.70, 6.55, 17.65),    # (檐口半径, 檐口z, 收顶半径, 收顶z)
        (8.90, 20.50, 4.25, 24.25),
        (6.35, 26.90, 1.45, 30.45)]
POWER = [1.45, 1.50, 1.62]
THICK = 0.46
COL_RINGS = [COL_R_OUT, COL_R_MID, COL_R_IN]


# ------------------------------------------------------------------ 殿身
def build_body():
    """殿身: 外墙 + 隔扇门窗带 + 石质墙裙"""
    r_w0 = COL_R_OUT - 1.05
    L.lathe("Body_Wall_L0",
            [(0.0, PLATFORM_TOP), (r_w0, PLATFORM_TOP),
             (r_w0, ARCH_TOP[0] - 0.95),
             (r_w0 - 0.24, ARCH_TOP[0] - 0.72),
             (r_w0 - 0.24, ARCH_TOP[0] - 0.66),
             (0.0, ARCH_TOP[0] - 0.66)],
            segments=128, mat=MAT["red_dark"], coll=COLL, smooth=False)
    # 隔扇门 (红色门板 + 金色门框/横披)
    for idx, z0 in enumerate((PLATFORM_TOP + 1.25, PLATFORM_TOP + 4.30)):
        L.ring_band(f"Body_Door_{idx}", r_w0 - 0.05, r_w0 + 0.04,
                    z0, z0 + 2.55, segments=128,
                    mat=MAT["red"], coll=COLL, smooth=True)
        for fi, fz in enumerate((z0, z0 + 2.44)):
            L.ring_band(f"Body_Door_Frame_{idx}_{fi}",
                        r_w0 - 0.08, r_w0 + 0.07,
                        fz, fz + 0.10, segments=128,
                        mat=MAT["gold_dark"], coll=COLL, smooth=True)
    L.ring_band("Body_Base_Skirt", r_w0 - 0.06, r_w0 + 0.12,
                PLATFORM_TOP, PLATFORM_TOP + 0.40, segments=128,
                mat=MAT["marble_dark"], coll=COLL, smooth=True)
    # 外檐柱与墙之间的坐凳楣子 (连系构件)
    L.ring_band("Body_Collar_Beam", COL_R_OUT - 1.05, COL_R_OUT - 0.10,
                ARCH_TOP[0] - 1.35, ARCH_TOP[0] - 1.15, segments=128,
                mat=MAT["red"], coll=COLL, smooth=True)
    # 中/上层殿身
    for i, (r_col, z0, z1) in enumerate(
            ((COL_R_MID, 15.35, ARCH_TOP[1] - 0.50),
             (COL_R_IN, 21.55, ARCH_TOP[2] - 0.50))):
        r_wall = r_col - 0.30
        L.lathe(f"Body_Wall_L{i+1}",
                [(0.0, z0), (r_wall, z0), (r_wall, z1 - 0.40),
                 (r_wall - 0.18, z1 - 0.22), (0.0, z1 - 0.22)],
                segments=112, mat=MAT["red"], coll=COLL, smooth=False)
        L.ring_band(f"Body_Skirt_L{i+1}", r_wall - 0.06, r_wall + 0.06,
                    z1 - 2.40, z1 - 2.05, segments=112,
                    mat=MAT["gold_dark"], coll=COLL, smooth=True)


# ------------------------------------------------------------------ 斗拱
def build_dougong():
    """额枋 + 斗拱 + 檐檩 (每层柱顶到檐口之间)"""
    for level, col_r in enumerate(COL_RINGS):
        z_top = ARCH_TOP[level]
        z_eave = EAVE[level][1]
        span = z_eave - z_top
        # 额枋
        L.ring_band(f"DG_Frieze_{level}", col_r - 0.44, col_r + 0.44,
                    z_top, z_top + span * 0.34, segments=128,
                    mat=MAT["paint_green"], coll=COLL, smooth=True)
        L.ring_band(f"DG_Frieze_Gold_{level}", col_r - 0.50, col_r + 0.50,
                    z_top + span * 0.34, z_top + span * 0.46, segments=128,
                    mat=MAT["gold"], coll=COLL, smooth=True)
        # 斗拱单元 (柱位 + 柱间)
        cells, gold = [], []
        positions = []
        for j in range(12):
            positions.append(TAU * j / 12)
            positions.append(TAU * (j + 0.5) / 12)
        r_br = col_r + 0.24
        for a in positions:
            x, y = r_br * math.cos(a), r_br * math.sin(a)
            cells.append(L.mat_trs((0.56, 0.56, span * 0.28),
                                   (x, y, z_top + span * 0.60), rot_z=a))
            cells.append(L.mat_trs((0.36, 1.45, span * 0.22),
                                   (x, y, z_top + span * 0.82), rot_z=a))
            cells.append(L.mat_trs((0.52, 0.52, span * 0.20),
                                   (x, y, z_top + span * 0.96), rot_z=a))
            gold.append(L.mat_trs((0.30, 1.52, span * 0.09),
                                  (x, y, z_top + span * 0.91), rot_z=a))
        L.merged_cubes(f"DG_Bracket_{level}", cells,
                       mat=MAT["paint_green"], coll=COLL, smooth=False)
        L.merged_cubes(f"DG_Bracket_Gold_{level}", gold,
                       mat=MAT["gold"], coll=COLL, smooth=False)
        # 檐檩 (承接屋顶的环形梁)
        L.ring_band(f"DG_EaveBeam_{level}", col_r - 0.55, col_r + 1.30,
                    z_top + span * 0.99, z_eave + 0.16, segments=128,
                    mat=MAT["paint_green"], coll=COLL, smooth=True)


# ------------------------------------------------------------------ 屋顶
def roof_profile(r_eave, z_eave, r_top, z_top, power, thickness):
    samples = L.sample_curve(r_eave, z_eave, r_top, z_top, 24, power)
    outer = [(r_eave + 0.58, z_eave + 0.02), (r_eave + 0.40, z_eave + 0.22)] + \
            samples + [(r_top * 0.62, z_top + 0.26), (0.0, z_top + 0.36)]
    inner = [(0.0, z_top + 0.36 - thickness * 0.85)] + \
            [(r, z - thickness) for (r, z) in reversed(samples)] + \
            [(r_eave + 0.44, z_eave - 0.26), (r_eave + 0.52, z_eave - 0.06)]
    return outer + inner


def build_roofs():
    for i, ((r_e, z_e, r_t, z_t), power) in enumerate(zip(EAVE, POWER)):
        L.lathe(f"Roof_{i}_Shell",
                roof_profile(r_e, z_e, r_t, z_t, power, THICK),
                segments=192, mat=MAT["tile"], coll=COLL, smooth=True)
        samples = L.sample_curve(r_e, z_e, r_t, z_t, 30, power)

        # --- 瓦垄 (连续琉璃瓦楞, 沿屋面母线扫掠) ---
        n_longs = 72
        rib_curve = L.curve_offset(samples, 0.028)
        L.roof_ribs(f"Roof_{i}_Tiles",
                    [TAU * j / n_longs for j in range(n_longs)],
                    rib_curve, half_width=0.128, thickness=0.052,
                    mat=MAT["tile"], coll=COLL, smooth=True)

        # --- 垂脊 (12 道, 上端收细) ---
        ridge_curve = L.curve_offset(samples, 0.060)
        L.roof_ribs(f"Roof_{i}_Ridge", [TAU * j / 12 for j in range(12)],
                    ridge_curve, half_width=0.26, thickness=0.16,
                    mat=MAT["tile_dark"], coll=COLL, smooth=True, taper=0.62)

        # --- 檐口瓦当 / 滴水 ---
        tiles = []
        for j in range(144):
            a = TAU * j / 144
            r = r_e + 0.40
            tiles.append(L.mat_trs((0.15, 0.14, 0.30),
                                   (r * math.cos(a), r * math.sin(a),
                                    z_e + 0.14), rot_z=a))
        L.merged_cubes(f"Roof_{i}_EaveTile", tiles, mat=MAT["tile_dark"],
                       coll=COLL, smooth=True)

        # --- 檐下椽子与连檐板 ---
        rafters = []
        for j in range(96):
            a = TAU * j / 96
            r = r_e - 0.55
            rafters.append(L.mat_trs((0.11, 0.13, 0.46),
                                     (r * math.cos(a), r * math.sin(a),
                                      z_e - 0.22), rot_z=a))
        L.merged_cubes(f"Roof_{i}_Rafter", rafters, mat=MAT["red_dark"],
                       coll=COLL, smooth=False)
        L.ring_band(f"Roof_{i}_Lianyan", r_e - 0.60, r_e - 0.40,
                    z_e - 0.46, z_e - 0.02, segments=160,
                    mat=MAT["paint_green"], coll=COLL, smooth=True)


# ------------------------------------------------------------------ 宝顶
def sphere_profile(radius, z0, segments=18):
    pts = []
    for k in range(segments + 1):
        t = -math.pi * 0.5 + math.pi * k / segments
        pts.append((radius * math.cos(t), z0 + radius * math.sin(t)))
    return pts


def build_finial():
    z = EAVE[-1][3]
    # 须弥座 (罩住屋顶收顶)
    L.lathe("Finial_Seat",
            [(0.0, z - 0.25), (1.95, z - 0.10), (1.78, z + 0.20),
             (1.42, z + 0.38), (1.58, z + 0.62), (1.58, z + 0.86),
             (1.24, z + 1.10), (0.0, z + 1.10)],
            segments=96, mat=MAT["gold"], coll=COLL, smooth=True)
    petals = []
    for j in range(20):
        a = TAU * j / 20
        petals.append(L.mat_trs((0.34, 0.50, 0.30),
                                (1.34 * math.cos(a), 1.34 * math.sin(a),
                                 z + 1.20), rot_z=a))
    L.merged_cubes("Finial_Lotus", petals, mat=MAT["gold"], coll=COLL,
                   smooth=True)
    # 莲座上的承露盘 + 主宝珠
    L.lathe("Finial_Neck", [(0.0, z + 1.16), (0.72, z + 1.24),
                            (0.82, z + 1.66), (0.60, z + 1.90),
                            (0.0, z + 1.90)],
            segments=64, mat=MAT["gold"], coll=COLL, smooth=True)
    L.lathe("Finial_Ball", sphere_profile(1.32, z + 2.98, 22),
            segments=96, mat=MAT["gold"], coll=COLL, smooth=True)
    L.lathe("Finial_Top", sphere_profile(0.58, z + 4.62, 14),
            segments=64, mat=MAT["gold"], coll=COLL, smooth=True)
    L.lathe("Finial_Spike", [(0.36, z + 4.78), (0.23, z + 5.10),
                             (0.10, z + 5.38), (0.0, z + 5.64)],
            segments=48, mat=MAT["gold"], coll=COLL, smooth=True)
    L.lathe("Finial_Tip_Ball", sphere_profile(0.21, z + 5.74, 12),
            segments=48, mat=MAT["gold"], coll=COLL, smooth=True)


build_body()
build_dougong()
build_roofs()
build_finial()

tot = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
result = {"stage": "part2_done",
          "objects": len(bpy.data.objects),
          "polygons": tot}
