"""一键: 重建模型 -> 布置预览环境 -> 渲染主视图"""
import bpy
import sys
import os

ROOT = r"D:\work\AI\BlenderMCPTest\try1"
sys.path.insert(0, ROOT)

for name, path in (("build", ROOT + r"\tiantan_build_p2.py"),
                   ("preview", ROOT + r"\tiantan_preview.py")):
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
    "preview_01.png": "Cam_Main",
    "preview_02.png": "Cam_Front",
    "preview_03.png": "Cam_Top",
    "preview_04.png": "Cam_Close",
}
written = []
if os.environ.get("TT_SHOTS", "1") == "1":
    for fname, cam in shots.items():
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = os.path.join(ROOT, fname)
        bpy.ops.render.render(write_still=True)
        written.append(fname)

result = {
    "objects": len(bpy.data.objects),
    "polygons": sum(len(o.data.polygons) for o in bpy.data.objects
                    if o.type == 'MESH'),
    "rendered": written,
}
