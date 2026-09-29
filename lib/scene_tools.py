"""通用场景 / 相机 / 灯光 / 渲染工具 (Blender 5.x)

与具体模型无关的公共功能: 渲染设置、三点布光、看板相机、
多视角批量出图、地面、网格统计。
"""
import bpy
import math
import os
from mathutils import Vector, Euler

try:
    from . import mesh_tools as mt
except ImportError:
    import mesh_tools as mt


# ------------------------------------------------------------------ 渲染
def setup_render(engine='BLENDER_EEVEE', resolution=(1280, 960), samples=48,
                 film_transparent=False, view_transform='Standard'):
    """配置渲染参数; 返回实际使用的引擎名"""
    scn = bpy.context.scene
    try:
        scn.render.engine = engine
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x, scn.render.resolution_y = resolution
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = film_transparent
    scn.render.image_settings.file_format = 'PNG'
    try:
        scn.view_settings.view_transform = view_transform
    except TypeError:
        pass
    if scn.render.engine == 'BLENDER_EEVEE':
        ee = scn.eevee
        for attr, val in (("taa_render_samples", samples),
                          ("use_shadows", True),
                          ("use_raytracing", True),
                          ("use_gtao", True)):
            try:
                setattr(ee, attr, val)
            except Exception:
                pass
    elif scn.render.engine == 'CYCLES':
        scn.cycles.samples = samples
        scn.cycles.use_denoising = True
    return scn.render.engine


def render_still(path):
    """真正执行渲染并写盘 (视口渲染不含材质, 必须走这里)"""
    scn = bpy.context.scene
    out = os.path.abspath(path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)
    return out if os.path.exists(out) else None


# ------------------------------------------------------------------ 相机
def look_at(ob, target):
    """让对象的 -Z 指向 target (相机朝向)"""
    d = Vector(target) - ob.location
    if d.length < 1e-9:
        return ob
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def add_camera(name, loc, target, lens=60.0, ortho=None, clip=(0.05, 500.0)):
    """新增相机并指向 target; ortho 给定时为平行投影 (值为视野尺寸)"""
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.clip_start, cam_data.clip_end = clip
    if ortho is not None:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam_data)
    mt.link_to(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def set_active_camera(cam):
    bpy.context.scene.camera = cam
    return cam


# ------------------------------------------------------------------ 灯光
def add_light(name, kind, loc, energy, color=(1, 1, 1), size=1.0,
              target=None, angle=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == 'AREA':
        data.size = size
    elif kind == 'SUN':
        data.angle = angle if angle is not None else 0.05
    ob = bpy.data.objects.new(name, data)
    mt.link_to(ob)
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    return ob


def studio_lights(target=(0, 0, 0), scale=1.0, energy=1.0):
    """三点布光: 主光 + 侧逆光 + 补光 + 环境"""
    t = Vector(target)
    lights = []
    lights.append(add_light("Light_Key", 'AREA',
                            (t.x + 2.6 * scale, t.y - 2.6 * scale,
                             t.z + 2.4 * scale),
                            1400 * energy, (1.0, 0.97, 0.92), 3.0 * scale, t))
    lights.append(add_light("Light_Rim", 'AREA',
                            (t.x - 3.0 * scale, t.y + 2.4 * scale,
                             t.z + 1.9 * scale),
                            900 * energy, (0.88, 0.93, 1.0), 2.5 * scale, t))
    lights.append(add_light("Light_Fill", 'AREA',
                            (t.x + 0.4 * scale, t.y + 3.4 * scale,
                             t.z + 1.2 * scale),
                            500 * energy, (1.0, 1.0, 1.0), 3.5 * scale, t))
    lights.append(add_light("Light_Top", 'AREA',
                            (t.x, t.y + 0.3 * scale, t.z + 3.6 * scale),
                            600 * energy, (1.0, 1.0, 1.0), 3.0 * scale, t))
    set_world(color=(0.35, 0.38, 0.42), strength=0.6)
    return lights


def set_world(color=(0.4, 0.42, 0.45), strength=1.0):
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = next((n for n in world.node_tree.nodes if n.type == 'BACKGROUND'),
              None)
    if bg is not None:
        bg.inputs[0].default_value = (color[0], color[1], color[2], 1.0)
        bg.inputs[1].default_value = strength
    return world


# ------------------------------------------------------------------ 地面
def add_ground(size=20.0, z=0.0, mat=None, name="Ground"):
    return mt.box(name, (size, size, 0.02), (0.0, 0.0, z - 0.01),
                  mat=mat, smooth=False)


# ------------------------------------------------------------------ 批量视图
def orbit_views(target=(0, 0, 0), radius=3.0, height=1.0, azimuths=None,
                lens=70.0, prefix="Cam"):
    """环形机位; azimuths 为角度列表 (0=正前 -Y 方向?)"""
    azs = azimuths if azimuths is not None else [0, 45, 90, 135, 180, 225, 270, 315]
    cams = []
    for i, a in enumerate(azs):
        rad = math.radians(a)
        loc = (target[0] + radius * math.sin(rad),
               target[1] - radius * math.cos(rad),
               target[2] + height)
        cams.append(add_camera(f"{prefix}_{i:02d}_{int(a):03d}", loc, target,
                               lens))
    return cams


def render_named_views(views, out_dir, prefix, resolution=None):
    """views: [(name, cam, target, radius, height, lens), ...]"""
    saved = bpy.context.scene.camera
    paths = []
    for name, cam, target, radius, height, lens in views:
        cam.location = (target[0] + radius * math.sin(math.radians(0)),
                        target[1] - radius, target[2] + height)
        look_at(cam, target)
        set_active_camera(cam)
        if resolution:
            bpy.context.scene.render.resolution_x = resolution[0]
            bpy.context.scene.render.resolution_y = resolution[1]
        p = render_still(os.path.join(out_dir, f"{prefix}_{name}.png"))
        paths.append(p)
    bpy.context.scene.camera = saved
    return paths


# ------------------------------------------------------------------ 统计
def object_stats():
    """统计当前场景对象数与三角面数"""
    total_v = total_f = total_t = 0
    per_object = {}
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        v, f = len(me.vertices), len(me.polygons)
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        per_object[ob.name] = (v, f, t)
        total_v += v
        total_f += f
        total_t += t
        ev.to_mesh_clear()
    return {'objects': len([o for o in bpy.data.objects if o.type == 'MESH']),
            'verts': total_v, 'faces': total_f, 'tris': total_t,
            'detail': per_object}


def bbox_of(names=None):
    """计算对象集合的整体包围盒 (世界坐标) -> (min, max, size)"""
    deps = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if names is not None and ob.name not in names:
            continue
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ob.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
        ev.to_mesh_clear()
    return lo, hi, (hi - lo)


def save_blend(path):
    out = os.path.abspath(path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out
