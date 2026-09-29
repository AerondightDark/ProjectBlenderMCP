"""通用 Blender 建模工具库 (Blender 5.x)
几何基础: 旋转体(lathe) / 环形阵列 / 圆柱棱柱 / 材质
所有模型共用, 不属于任一具体模型。
"""
import bpy
import bmesh
import math
import mathutils
from mathutils import Matrix

TAU = 2.0 * math.pi


def mat_trs(scale, loc, rot_z=0.0, rot_y=0.0, rot_x=0.0):
    """构造 T(loc) @ Rz @ Ry @ Rx @ S(scale) 变换矩阵"""
    m = Matrix.Translation(loc)
    m = m @ Matrix.Rotation(rot_z, 4, 'Z')
    m = m @ Matrix.Rotation(rot_y, 4, 'Y')
    m = m @ Matrix.Rotation(rot_x, 4, 'X')
    m = m @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    return m


# ---------------------------------------------------------------- 场景管理
def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                   bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for item in list(blocks):
            if item.users == 0:
                blocks.remove(item)


def new_collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def link(ob, coll=None):
    coll = coll or bpy.context.scene.collection
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


# ---------------------------------------------------------------- 材质
def make_material(name, color, roughness=0.5, metallic=0.0,
                  sheen=0.0, coat=0.0, ior=1.45, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (10.0, 10.0)
        if out is not None:
            nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    mat["bsdf_node"] = bsdf.name

    def setv(key, value):
        if key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = value
            except Exception:
                pass

    setv("Base Color", (color[0], color[1], color[2], 1.0))
    setv("Roughness", roughness)
    setv("Metallic", metallic)
    setv("IOR", ior)
    setv("Sheen Weight", sheen)
    setv("Coat Weight", coat)
    setv("Alpha", alpha)
    if alpha < 1.0:
        for attr, val in (("blend_method", 'BLEND'),
                          ("surface_render_method", 'BLENDED')):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
    return mat


# ---------------------------------------------------------------- 网格
def _mesh_from_bm(name, bm, mat, coll, smooth):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    if mat:
        ob.data.materials.append(mat)
    link(ob, coll)
    return ob


def lathe(name, profile, segments=96, mat=None, coll=None,
          smooth=True, close_start=False, close_end=False,
          center=(0.0, 0.0, 0.0), rot_z=0.0):
    """profile: [(radius, z), ...] 由下至上; radius=0 会自动焊接成顶点"""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segments):
            a = TAU * i / segments + rot_z
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    for j in range(len(rings) - 1):
        A, B = rings[j], rings[j + 1]
        for i in range(segments):
            k = (i + 1) % segments
            quad = [A[i], A[k], B[k], B[i]]
            uniq = []
            for v in quad:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) < 3:
                continue
            try:
                bm.faces.new(uniq)
            except ValueError:
                pass

    if close_start and len(rings[0]) > 2:
        try:
            bm.faces.new(rings[0])
        except ValueError:
            pass
    if close_end and len(rings[-1]) > 2:
        try:
            bm.faces.new(list(reversed(rings[-1])))
        except ValueError:
            pass

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    ob = _mesh_from_bm(name, bm, mat, coll, smooth)
    ob.location = center
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, coll=None,
        smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    ob = _mesh_from_bm(name, bm, mat, coll, smooth)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def poly_prism(name, sides, radius, height, loc=(0, 0, 0), rot_z=0.0,
               taper=1.0, mat=None, coll=None, smooth=False):
    """多棱柱 / 圆台: 用于柱子、望柱"""
    bm = bmesh.new()
    bottom, top = [], []
    for i in range(sides):
        a = TAU * i / sides + rot_z
        bottom.append(bm.verts.new((radius * math.cos(a),
                                    radius * math.sin(a), 0.0)))
        r2 = radius * taper
        top.append(bm.verts.new((r2 * math.cos(a), r2 * math.sin(a), height)))
    for i in range(sides):
        k = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[k], top[k], top[i]))
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    ob = _mesh_from_bm(name, bm, mat, coll, smooth)
    ob.location = loc
    return ob


def ring_band(name, radius_in, radius_out, z0, z1, segments=96,
              mat=None, coll=None, smooth=False):
    """竖直环形薄壁 (栏板/额枋/腰线)"""
    profile = [(radius_in, z0), (radius_out, z0),
               (radius_out, z1), (radius_in, z1), (radius_in, z0)]
    return lathe(name, profile, segments=segments, mat=mat, coll=coll,
                 smooth=smooth)


def disc(name, radius, z, thickness=0.0, segments=96, mat=None, coll=None,
         smooth=False):
    if thickness <= 0.0:
        return lathe(name, [(0.0, z), (radius, z)], segments=segments,
                     mat=mat, coll=coll, smooth=smooth)
    return lathe(name, [(0.0, z - thickness), (radius, z - thickness),
                        (radius, z), (0.0, z)], segments=segments,
                 mat=mat, coll=coll, smooth=smooth)


# ---------------------------------------------------------------- 阵列
def merged_cubes(name, matrices, mat=None, coll=None, smooth=False):
    """把大量小方块合并到单个 mesh, 用于瓦楞/垂脊/斗拱等重复装饰"""
    bm = bmesh.new()
    for m in matrices:
        bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    return _mesh_from_bm(name, bm, mat, coll, smooth)


def ridge_cells(azimuth, samples, half_width, thickness):
    """沿母线采样的脊线小方块矩阵; samples: [(r, z, alpha), ...]"""
    out = []
    for (r, z, alpha) in samples:
        x, y = r * math.cos(azimuth), r * math.sin(azimuth)
        out.append(mat_trs((half_width, half_width * 0.62, thickness),
                           (x, y, z), rot_z=azimuth, rot_y=alpha))
    return out


def sample_curve(r0, z0, r1, z1, segs, power=2.0):
    """凹曲面(举折)母线采样, 返回 [(r, z), ...]"""
    pts = []
    for k in range(segs + 1):
        t = k / float(segs)
        r = r1 + (r0 - r1) * (1.0 - t) ** power
        z = z0 + (z1 - z0) * t
        pts.append((r, z))
    return pts


def curve_offset(samples, lift):
    """把母线采样点沿法线外移 lift"""
    n = len(samples)
    out = []
    for i, (r, z) in enumerate(samples):
        if i == 0:
            dr, dz = samples[1][0] - r, samples[1][1] - z
        elif i == n - 1:
            dr, dz = r - samples[-2][0], z - samples[-2][1]
        else:
            dr = samples[i + 1][0] - samples[i - 1][0]
            dz = samples[i + 1][1] - samples[i - 1][1]
        ln = math.hypot(dr, dz) or 1.0
        out.append((r + lift * dz / ln, z - lift * dr / ln))
    return out


def roof_ribs(name, azimuths, samples, half_width, thickness, mat=None,
              coll=None, smooth=True, taper=1.0):
    """沿母线曲面生成连续瓦垄/垂脊条带 (单个合并网格)"""
    bm = bmesh.new()
    n_sp = len(samples)
    for azimuth in azimuths:
        ca, sa = math.cos(azimuth), math.sin(azimuth)
        rings = []
        for k, (r, z) in enumerate(samples):
            t = k / float(n_sp - 1)
            hw = half_width * (1.0 + (taper - 1.0) * t)
            th = thickness * (1.0 + (taper - 1.0) * t)
            quad = ((-hw, 0.0), (hw, 0.0), (hw, th), (-hw, th))
            rings.append([bm.verts.new(((r + du) * ca, (r + du) * sa,
                                        z + dn)) for du, dn in quad])
        for k in range(n_sp - 1):
            A, B = rings[k], rings[k + 1]
            for i in range(4):
                j = (i + 1) % 4
                try:
                    bm.faces.new((A[i], A[j], B[j], B[i]))
                except ValueError:
                    pass
        try:
            bm.faces.new(list(reversed(rings[0])))
            bm.faces.new(rings[-1])
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return _mesh_from_bm(name, bm, mat, coll, smooth)


def ring_angles(count, offset=0.0):
    return [TAU * i / count + offset for i in range(count)]


def place_ring(template_fn, count, radius, z=0.0, offset=0.0,
               coll=None, name_prefix="ring", **kw):
    objs = []
    for idx, a in enumerate(ring_angles(count, offset)):
        ob = template_fn(f"{name_prefix}_{idx:02d}", a, radius, z, coll, **kw)
        objs.append(ob)
    return objs
