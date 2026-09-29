"""摩托车建模公共模块: 路径引导 / 材质库 / 场景与渲染辅助"""
import sys
import os
import math
import importlib

ROOT = r'd:/work/AI/BlenderMCPTest/try1'
for _p in (ROOT, os.path.join(ROOT, 'motorcycle'), os.path.join(ROOT, 'lib')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy                                             # noqa: E402
import lib.mesh_tools as mt                            # noqa: E402
import lib.scene_tools as st                           # noqa: E402
import moto_params as P                                # noqa: E402

TMP = os.path.join(ROOT, 'motorcycle', 'render')
BLEND = os.path.join(ROOT, 'motorcycle', 'Motorcycle.blend')


def reload_all():
    """热重载公共库, 便于迭代修改"""
    importlib.reload(P)
    importlib.reload(mt)
    importlib.reload(st)
    return mt, st, P


# ------------------------------------------------------------------ 材质库
def build_materials():
    """按实车配色建立材质字典"""
    m = {}
    m['paint_red'] = mt.make_material(
        "Paint_IndianRed", P.RED, roughness=0.13, metallic=0.0, coat=0.85)
    m['paint_cream'] = mt.make_material(
        "Paint_Cream", P.CREAM, roughness=0.16, coat=0.80)
    m['frame_black'] = mt.make_material(
        "Frame_Black", P.BLACK_GLOSS, roughness=0.30, metallic=0.35)
    m['engine_black'] = mt.make_material(
        "Engine_Black", P.BLACK_MATTE, roughness=0.62, metallic=0.25)
    m['turbo_silver'] = mt.make_material(
        "Turbo_Silver", P.TURBO_SILVER, roughness=0.28, metallic=0.95)
    m['chrome'] = mt.make_material(
        "Chrome", P.CHROME, roughness=0.06, metallic=1.0)
    m['rubber'] = mt.make_material(
        "Rubber_Tire", P.RUBBER, roughness=0.85)
    m['leather'] = mt.make_material(
        "Leather_Seat", P.LEATHER, roughness=0.62, sheen=0.14)
    m['steel'] = mt.make_material(
        "Steel_Disc", (0.62, 0.63, 0.65), roughness=0.22, metallic=1.0)
    m['amber'] = mt.make_material(
        "Lamp_Amber", P.AMBER, roughness=0.15, emission=P.AMBER,
        emission_strength=1.2)
    m['red_lamp'] = mt.make_material(
        "Lamp_Red", (0.62, 0.03, 0.03), roughness=0.12,
        emission=(0.9, 0.05, 0.03), emission_strength=1.4)
    m['glass'] = mt.make_material(
        "Lamp_Glass", (0.92, 0.94, 0.96), roughness=0.04, alpha=0.22,
        ior=1.5)
    m['gold'] = mt.make_material(
        "Gold_Emblem", (0.72, 0.52, 0.18), roughness=0.24, metallic=1.0)
    m['white_letter'] = mt.make_material(
        "Tire_Lettering", (0.80, 0.79, 0.76), roughness=0.7)
    return m


# ------------------------------------------------------------------ 场景
def new_scene(name="Motorcycle"):
    """清空场景并建立摩托车的集合结构"""
    mt.clear_scene()
    scn = bpy.context.scene
    scn.name = name
    scn.unit_settings.system = 'METRIC'
    scn.unit_settings.scale_length = 1.0
    colls = {
        'root': mt.ensure_collection("Moto"),
        'wheels': mt.ensure_collection("Moto_Wheels"),
        'frame': mt.ensure_collection("Moto_Frame"),
        'engine': mt.ensure_collection("Moto_Engine"),
        'body': mt.ensure_collection("Moto_Body"),
        'controls': mt.ensure_collection("Moto_Controls"),
        'lights': mt.ensure_collection("Moto_Lights"),
        'exhaust': mt.ensure_collection("Moto_Exhaust"),
        'rig': mt.ensure_collection("Moto_Rig"),
    }
    for key in ('wheels', 'frame', 'engine', 'body', 'controls', 'lights',
                'exhaust'):
        colls['root'].children.link(colls[key])
    return colls


def setup_look(colls=None, energy=0.22, world=0.55):
    """相机 / 灯光 / 地面 / 渲染参数 (能量按 3 m 尺度标定, 避免过曝)"""
    colls = colls or {}
    st.setup_render('BLENDER_EEVEE', (1440, 1080), samples=64,
                    view_transform='Standard')
    st.set_world((0.26, 0.29, 0.34), world)
    ground_mat = mt.make_material("Ground_Mat", (0.32, 0.32, 0.33),
                                  roughness=0.70)
    ground = st.add_ground(size=24.0, z=P.GROUND, mat=ground_mat)
    mt.link_to(ground, colls.get('rig', mt.get_scene_collection()))
    st.studio_lights(target=(-0.75, 0.0, 0.15), scale=1.0, energy=energy)
    return ground


VIEWS = [
    ('left', (0.0, -4.6, 0.55), (-0.78, 0.0, 0.16), 100.0),
    ('front', (-5.4, 0.0, 0.60), (-0.78, 0.0, 0.16), 100.0),
    ('right', (0.0, 4.6, 0.55), (-0.78, 0.0, 0.16), 100.0),
    ('rear', (5.4, 0.0, 0.60), (-0.78, 0.0, 0.16), 100.0),
    ('q34f', (-3.9, -2.6, 1.05), (-0.78, 0.0, 0.18), 100.0),
    ('q34r', (3.6, 2.9, 0.95), (-0.78, 0.0, 0.18), 100.0),
    ('top', (0.0, 0.0, 5.2), (-0.78, 0.0, 0.0), 100.0),
    ('d_engine', (0.28, 1.28, 0.26), (-0.78, 0.0, 0.04), 88.0),
    ('d_front', (-2.46, -1.02, 0.10), (-1.63, 0.0, -0.02), 85.0),
    ('d_rear', (1.62, -1.08, 0.16), (0.16, 0.0, -0.05), 85.0),
    ('d_cockpit', (0.26, 1.34, 0.96), (-0.86, 0.0, 0.46), 85.0),
    ('d_exhaust', (1.08, 1.24, -0.18), (-0.18, 0.16, -0.20), 85.0),
]


def check_penetration(ob_a, ob_b, max_samples=320):
    """A 的采样点相对 B 表面的最小有符号距离; 负值 = 进入 B 内部

    返回 (min_signed, inside_count, sample_count)
    """
    if ob_a is None or ob_b is None:
        return None
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob_a.evaluated_get(deps)
    me = ev.to_mesh()
    mw = ob_a.matrix_world
    step = max(1, len(me.vertices) // max_samples)
    pts = [mw @ me.vertices[i].co for i in range(0, len(me.vertices), step)]
    ev.to_mesh_clear()
    inv = ob_b.matrix_world.inverted()
    best, inside = 1e9, 0
    for p in pts:
        pl = inv @ p
        ok, loc, nrm, _ = ob_b.closest_point_on_mesh(pl)
        if not ok:
            continue
        vec = pl - loc
        sd = vec.length if vec.dot(nrm) >= 0 else -vec.length
        if sd < best:
            best = sd
        if sd < 0:
            inside += 1
    return best, inside, len(pts)


PENETRATION_PAIRS = [
    ('Wheel_Front_Tire', 'Fender_Front'),
    ('Wheel_Rear_Tire', 'Fender_Rear'),
    ('Tank_Main', 'Frame_Backbone'),
    ('Tank_Main', 'Engine_RockerCover_Front'),
    ('Tank_Main', 'Engine_RockerCover_Rear'),
    ('Seat_Solo', 'Frame_Backbone'),
    ('Seat_Solo', 'Tank_Main'),
    ('Seat_Solo', 'SidePanel_L'),
    ('Exhaust_FrontCyl', 'Wheel_Rear_Tire'),
    ('Exhaust_RearCyl', 'Wheel_Rear_Tire'),
    ('Exhaust_FrontCyl', 'Fender_Rear'),
    ('Floorboard_L', 'Engine_Crankcase'),
    ('Floorboard_R', 'Engine_Crankcase'),
    ('Engine_Crankcase', 'Frame_Cradle_L'),
    ('Engine_Crankcase', 'Frame_DownTube'),
    ('Fork_Lower_L', 'Fender_Front'),
    ('Drive_Belt', 'Swingarm_L'),
]


def run_penetration_checks(pairs=None):
    out = {}
    for a, b in (pairs or PENETRATION_PAIRS):
        oa, ob = bpy.data.objects.get(a), bpy.data.objects.get(b)
        if oa is None or ob is None:
            out[f"{a}|{b}"] = 'missing'
            continue
        r = check_penetration(oa, ob)
        if r is None:
            out[f"{a}|{b}"] = 'n/a'
            continue
        best, inside, n = r
        out[f"{a}|{b}"] = {
            'min_mm': round(best * 1000.0, 1),
            'inside_pts': inside,
            'samples': n,
        }
    return out


def render_views(tag, names=None, res=(1440, 1080), colls=None, ortho=True):
    """按标准机位渲染一组视图, 返回文件路径列表"""
    colls = colls or {}
    rig = colls.get('rig', mt.get_scene_collection())
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = res
    out = []
    for name, loc, target, lens in VIEWS:
        if names and name not in names:
            continue
        cam = bpy.data.objects.get(f"Cam_{name}")
        if cam is None:
            cam = st.add_camera(f"Cam_{name}", loc, target, lens)
            mt.link_to(cam, rig)
        else:
            cam.location = loc
            st.look_at(cam, target)
        st.set_active_camera(cam)
        path = st.render_still(os.path.join(TMP, f"{tag}_{name}.png"))
        out.append(path)
    return out


def save(path=None):
    return st.save_blend(path or BLEND)
