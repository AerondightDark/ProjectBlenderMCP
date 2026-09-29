"""一键: 重建模型 -> 布置预览环境 -> 渲染主视图 (天坛祈年殿)"""
import bpy
import sys
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(_HERE)              # 仓库根: .../try1
    MODEL = _HERE                             # 本模型目录: .../try1/tiantan
except NameError:                            # 经 MCP 字符串执行时无 __file__
    ROOT = r"D:\work\AI\BlenderMCPTest\try1"
    MODEL = ROOT + r"\tiantan"
sys.path.insert(0, os.path.join(ROOT, "lib"))

for name, path in (("build", os.path.join(MODEL, "build_p2.py")),
                   ("preview", os.path.join(MODEL, "preview.py"))):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    exec(compile(src, path, "exec"), globals())

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 900, 1150
try:
    sc.eevee.taa_render_samples = 40
except Exception:
    pass

shots = {
    os.path.join(MODEL, "preview_01.png"): "Cam_Main",
    os.path.join(MODEL, "preview_02.png"): "Cam_Front",
    os.path.join(MODEL, "preview_03.png"): "Cam_Top",
    os.path.join(MODEL, "preview_04.png"): "Cam_Close",
}
written = []
if os.environ.get("TT_SHOTS", "1") == "1":
    for fname, cam in shots.items():
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = fname
        bpy.ops.render.render(write_still=True)
        written.append(os.path.basename(fname))

result = {
    "objects": len(bpy.data.objects),
    "polygons": sum(len(o.data.polygons) for o in bpy.data.objects
                    if o.type == 'MESH'),
    "rendered": written,
}
