"""天坛祈年殿 - 第一部分: 材质 / 三层汉白玉台基 / 栏杆 / 红柱"""
import bpy
import math
import sys

sys.path.insert(0, r"D:\work\AI\BlenderMCPTest\try1")
import tiantan_lib as L
from tiantan_lib import TAU

# ------------------------------------------------------------ 初始化
L.clear_scene()
COLL = L.new_collection("TianTan_QinianDian")

MAT = {}
MAT["marble"] = L.make_material("Marble_White", (0.905, 0.885, 0.845),
                                roughness=0.30, sheen=0.12, coat=0.08)
MAT["marble_dark"] = L.make_material("Marble_Shadow", (0.760, 0.735, 0.690),
                                     roughness=0.42)
MAT["red"] = L.make_material("Lacquer_Red", (0.372, 0.048, 0.036),
                             roughness=0.46, coat=0.12)
MAT["red_dark"] = L.make_material("Lacquer_Red_Dark", (0.230, 0.026, 0.021),
                                  roughness=0.52, coat=0.08)
MAT["tile"] = L.make_material("Glazed_Tile_Blue", (0.020, 0.058, 0.290),
                              roughness=0.13, coat=0.65)
MAT["tile_dark"] = L.make_material("Glazed_Tile_Deep", (0.010, 0.032, 0.180),
                                   roughness=0.17, coat=0.55)
MAT["gold"] = L.make_material("Gold_Leaf", (1.000, 0.766, 0.290),
                              roughness=0.16, metallic=1.0)
MAT["gold_dark"] = L.make_material("Gold_Antique", (0.560, 0.390, 0.120),
                                   roughness=0.32, metallic=1.0)
MAT["paint_green"] = L.make_material("Caihua_Green", (0.038, 0.158, 0.134),
                                     roughness=0.44, coat=0.12)
MAT["stone_floor"] = L.make_material("Stone_Floor", (0.245, 0.240, 0.225),
                                     roughness=0.78)

# ------------------------------------------------------------ 尺寸参数
BASE = [  # (外半径, 底 z, 顶 z) 由下至上
    (14.60, 0.00, 1.40),
    (13.10, 1.40, 2.80),
    (11.60, 2.80, 4.20),
]
PLATFORM_TOP = BASE[-1][2]
COL_R_OUT, COL_R_MID, COL_R_IN = 8.60, 6.30, 4.05
COL_D = 0.92


def build_tiers():
    for i, (r_out, z0, z1) in enumerate(BASE):
        cap = 0.30 * (z1 - z0)
        profile = [(0.0, z0), (r_out, z0),
                   (r_out, z1 - cap), (r_out - 0.14, z1), (0.0, z1)]
        L.lathe(f"Base_Tier_{i}_body", profile, segments=160,
                mat=MAT["marble"], coll=COLL)
        # 侧面雕花腰线 (束腰)
        band = z0 + (z1 - z0) * 0.40
        L.ring_band(f"Base_Tier_{i}_band", r_out - 0.005, r_out + 0.085,
                    band, band + 0.20, segments=160,
                    mat=MAT["marble_dark"], coll=COLL, smooth=True)
        # 束腰上下雕花 (连续回纹浅浮雕)
        carve = []
        n_carve = int(round(TAU * r_out / 0.62))
        for j in range(n_carve):
            a = TAU * j / n_carve
            x, y = (r_out + 0.03) * math.cos(a), (r_out + 0.03) * math.sin(a)
            carve.append(L.mat_trs((0.34, 0.16, 0.075),
                                   (x, y, band + 0.33), rot_z=a))
            carve.append(L.mat_trs((0.34, 0.16, 0.075),
                                   (x, y, band - 0.13), rot_z=a))
        L.merged_cubes(f"Base_Tier_{i}_carve", carve,
                       mat=MAT["marble_dark"], coll=COLL, smooth=False)
        # 台面外沿压边
        L.ring_band(f"Base_Tier_{i}_edge", r_out - 0.34, r_out - 0.16,
                    z1 - 0.03, z1, segments=160,
                    mat=MAT["marble_dark"], coll=COLL, smooth=True)


def build_rails():
    """每层台基边缘: 望柱 + 栏板 (南侧 -Y 留出踏道开口)"""
    gap_half = math.radians(11.0)          # 南侧开口半角 (-Y 方向 = 270°)
    for i, (r_out, z0, z1) in enumerate(BASE):
        radius = r_out - 0.45
        count = max(12, int(round(TAU * radius / 3.15)))
        post_matrices = []
        for j in range(count):
            a = TAU * j / count
            # 跳过南侧开口
            d = abs(((a - (1.5 * math.pi)) + math.pi) % TAU - math.pi)
            if d < gap_half:
                continue
            x, y = radius * math.cos(a), radius * math.sin(a)
            post_matrices.append(L.mat_trs((0.34, 0.34, 0.78),
                                           (x, y, z1 + 0.39), rot_z=a))
            post_matrices.append(L.mat_trs((0.44, 0.44, 0.16),
                                           (x, y, z1 + 0.86), rot_z=a))
            post_matrices.append(L.mat_trs((0.22, 0.22, 0.26),
                                           (x, y, z1 + 1.06), rot_z=a))
        L.merged_cubes(f"Rail_T{i}_Posts", post_matrices,
                       mat=MAT["marble"], coll=COLL, smooth=False)
        # 栏板: 环形薄壁, 南侧开口由望柱与踏道自然衔接
        L.ring_band(f"Rail_T{i}_Panel", radius - 0.075, radius + 0.075,
                    z1 + 0.16, z1 + 0.62, segments=160,
                    mat=MAT["marble"], coll=COLL, smooth=True)


def build_stairs():
    """南侧 (-Y) 三层踏道 + 中央丹陛石"""
    for i, (r_out, z0, z1) in enumerate(BASE):
        r0 = r_out - 0.35
        depth = r_out + 2.55 - r0
        steps = 4
        for s in range(steps):
            t0 = s / steps
            t1 = (s + 1) / steps
            w = 3.6 + 0.55 * (steps - s)
            L.box(f"Stair_T{i}_step_{s}",
                  (w, depth / steps, (z1 - z0) / steps),
                  loc=(0.0, -(r0 + depth * (t0 + t1) * 0.5),
                       z0 + (z1 - z0) * (t0 + t1) * 0.5),
                  mat=MAT["marble"], coll=COLL)
        # 丹陛石 (踏道中央浅浮雕)
        L.box(f"Stair_T{i}_danbi", (1.55, depth * 0.92, (z1 - z0) + 0.10),
              loc=(0.0, -(r0 + depth * 0.46), z0 + (z1 - z0) * 0.5 + 0.04),
              mat=MAT["marble_dark"], coll=COLL)
        for s in range(steps):
            t = (s + 0.5) / steps
            L.box(f"Stair_T{i}_lip_{s}", (1.72, depth / steps * 0.5, 0.07),
                  loc=(0.0, -(r0 + depth * t), z0 + (z1 - z0) * t + 0.05),
                  mat=MAT["marble"], coll=COLL)


def build_ground():
    L.lathe("Ground_Apron", [(0.0, -0.24), (34.0, -0.24), (34.0, 0.0),
                             (0.0, 0.0)], segments=128,
            mat=MAT["stone_floor"], coll=COLL, smooth=False)


def build_columns():
    """外檐柱 / 中金柱 / 内金柱 (各 12 根)"""
    specs = [
        (COL_R_OUT, COL_D, PLATFORM_TOP, 12.80, 12),
        (COL_R_MID, COL_D * 0.91, 15.55, 19.75, 12),
        (COL_R_IN, COL_D * 0.83, 21.75, 26.15, 12),
    ]
    for ci, (radius, dia, z0, z1, count) in enumerate(specs):
        for j in range(count):
            a = TAU * j / count
            x, y = radius * math.cos(a), radius * math.sin(a)
            L.poly_prism(f"Col_L{ci}_{j:02d}", 20, dia * 0.5, z1 - z0,
                         loc=(x, y, z0), taper=0.965,
                         mat=MAT["red"], coll=COLL, smooth=True)
            if ci == 0:
                # 柱础 (石鼓)
                L.lathe(f"Col_L0_Base_{j:02d}",
                        [(0.0, 0.0), (dia * 0.80, 0.0), (dia * 0.80, 0.10),
                         (dia * 0.62, 0.24), (dia * 0.52, 0.30), (0.0, 0.30)],
                        segments=32, mat=MAT["marble_dark"], coll=COLL,
                        smooth=True, center=(x, y, z0))
            # 柱顶额枋环
        L.ring_band(f"Arch_Frieze_L{ci}", radius - dia * 0.55,
                    radius + dia * 0.55, z1 - 0.62, z1 - 0.10,
                    segments=160, mat=MAT["red_dark"], coll=COLL,
                    smooth=True)


build_ground()
build_tiers()
build_rails()
build_stairs()
build_columns()

result = {"stage": "part1_done",
          "objects": len(bpy.data.objects),
          "materials": len(bpy.data.materials)}
