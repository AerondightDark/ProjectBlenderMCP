"""设置相机/灯光/渲染环境并输出预览图 (不修改建筑本体)"""
import bpy
import math
import os
from mathutils import Vector

try:
    OUT = os.path.dirname(os.path.abspath(__file__))   # 本模型目录
except NameError:                                       # 经 MCP 字符串执行时无 __file__
    OUT = r"D:\work\AI\BlenderMCPTest\try1\tiantan"
TARGET = (0.0, 0.0, 17.5)


def ensure_camera(name, loc, target=TARGET, lens=52.0, ortho=None):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'
    cam.location = Vector(loc)
    d = (Vector(target) - Vector(loc)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam


def ensure_light(name, kind, energy, loc, rot=None, size=6.0, angle=3.0):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.lights.new(name, kind))
        bpy.context.scene.collection.objects.link(ob)
    ob.data.type = kind
    ob.data.energy = energy
    ob.location = loc
    if kind == 'SUN':
        ob.data.angle = math.radians(angle)
        if rot:
            ob.rotation_euler = rot
    else:
        ob.data.size = size
        d = (Vector(TARGET) - Vector(loc)).normalized()
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def ensure_world(color=(0.55, 0.68, 0.86), strength=1.3):
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (color[0], color[1], color[2], 1.0)
        bg.inputs[1].default_value = strength


def setup_render(w=1100, h=1400):
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try:
            sc.render.engine = eng
            break
        except Exception:
            continue
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    for attr, val in (("taa_render_samples", 64), ("use_gtao", True)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    sc.view_settings.look = 'None'


def render_to(path, cam):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


ensure_world()
ensure_light("KeySun", 'SUN', 3.1, (30.0, -40.0, 52.0),
             rot=(math.radians(46.0), 0.0, math.radians(36.0)))
ensure_light("FillSun", 'SUN', 1.9, (-42.0, -22.0, 30.0),
             rot=(math.radians(66.0), 0.0, math.radians(-62.0)))
ensure_light("RimArea", 'AREA', 140000.0, (-30.0, 34.0, 30.0), size=24.0)
ensure_light("FrontArea", 'AREA', 60000.0, (6.0, -46.0, 20.0), size=20.0)

setup_render()
CAM_MAIN = ensure_camera("Cam_Main", (36.0, -53.0, 26.0), TARGET, lens=48.0)
CAM_FRONT = ensure_camera("Cam_Front", (0.0, -70.0, 18.0), TARGET, lens=52.0)
CAM_TOP = ensure_camera("Cam_Top", (28.0, -36.0, 56.0), (0.0, 0.0, 14.0),
                        lens=42.0)
CAM_CLOSE = ensure_camera("Cam_Close", (17.0, -30.0, 15.0), (0.0, 0.0, 11.0),
                          lens=64.0)

result = {"preview": "ready", "engine": bpy.context.scene.render.engine,
          "cams": ["Cam_Main", "Cam_Front", "Cam_Top", "Cam_Close"]}
