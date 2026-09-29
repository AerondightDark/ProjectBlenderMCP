"""通用程序化建模工具 (Blender 5.x)

与具体模型无关的公共几何功能:
  基础对象 / 场景管理 / 参数曲面 / 放样 / 扫掠管道 / 旋转体 /
  圆角箱体 / Catmull-Rom 平滑路径 / 轮胎 / 超椭圆截面 / 螺栓 / 镜像

约定:
  - 所有构造函数返回 bpy.types.Object
  - mat 参数接受 bpy.types.Material; coll 参数接受 bpy.types.Collection
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

TAU = 2.0 * math.pi


# ------------------------------------------------------------------ 场景
def get_scene_collection():
    return bpy.context.scene.collection


def ensure_collection(name, parent=None):
    """按名字取集合, 不存在则新建"""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        (parent or get_scene_collection()).children.link(coll)
    return coll


def link_to(ob, coll=None):
    """把对象移入指定集合 (从其它集合解除链接)"""
    coll = coll or get_scene_collection()
    if coll not in ob.users_collection:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
    return ob


def remove_objects(prefix):
    """删除名字以 prefix 开头的所有对象"""
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefix):
            bpy.data.objects.remove(ob, do_unlink=True)


def purge_orphans():
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                   bpy.data.cameras, bpy.data.lights, bpy.data.images,
                   bpy.data.node_groups):
        for item in list(blocks):
            if item.users == 0:
                blocks.remove(item)


def clear_scene():
    """清空场景中所有对象与孤立数据块"""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    purge_orphans()


# ------------------------------------------------------------------ 网格基础
def _finish(name, bm, mat, coll, smooth, merge):
    if merge and merge > 0.0:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        ob.data.materials.append(mat)
    link_to(ob, coll)
    return ob


def mesh_object(name, verts, faces, mat=None, coll=None, smooth=True,
                merge=1e-5):
    """由顶点表 + 面表构造网格对象"""
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    bm.verts.index_update()
    for f in faces:
        uniq = []
        for i in f:
            if vs[i] not in uniq:
                uniq.append(vs[i])
        if len(uniq) < 3:
            continue
        try:
            bm.faces.new(uniq)
        except ValueError:
            pass
    return _finish(name, bm, mat, coll, smooth, merge)


def set_smooth(ob, smooth=True, angle=None):
    for p in ob.data.polygons:
        p.use_smooth = smooth
    return ob


def shade_auto_smooth(ob, angle=math.radians(35.0)):
    """按角度自动平滑: 用边标记替代 5.x 已移除的 auto_smooth 属性"""
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < angle
    bm.to_mesh(me)
    bm.free()
    return ob


def apply_modifier(ob, mod):
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def add_mirror(ob, axis='X', use_clip=True):
    """添加 X 轴镜像修改器 (保留可编辑性)"""
    mod = ob.modifiers.new("Mirror", 'MIRROR')
    mod.use_axis = tuple(a in axis for a in 'XYZ')
    mod.use_clip = use_clip
    mod.merge_threshold = 0.001
    return mod


def add_subsurf(ob, levels=1, render_levels=2):
    mod = ob.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = levels
    mod.render_levels = render_levels
    return mod


def add_solidify(ob, thickness, offset=0.0):
    mod = ob.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = offset
    return mod


# ------------------------------------------------------------------ 数学辅助
def interp_table(table, t):
    """对 [(key, value), ...] 做线性插值, key 升序"""
    if t <= table[0][0]:
        return table[0][1]
    if t >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        k0, v0 = table[i]
        k1, v1 = table[i + 1]
        if k0 <= t <= k1:
            f = (t - k0) / (k1 - k0) if k1 > k0 else 0.0
            return v0 + (v1 - v0) * f
    return table[-1][1]


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def catmull_rom(points, samples_per_seg=12, closed=False, tension=0.5):
    """Catmull-Rom 样条插值, 返回加密后的点列 (list[Vector])"""
    pts = [Vector(p) for p in points]
    n = len(pts)
    if n < 3:
        return list(pts)
    out = []
    seg_count = n if closed else n - 1
    for i in range(seg_count):
        p0 = pts[(i - 1) % n] if (closed or i - 1 >= 0) else pts[i]
        p1 = pts[i % n]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[(i + 1) % n]
        last = (i == seg_count - 1)
        cnt = samples_per_seg + (0 if last else 1)
        for j in range(cnt):
            t = j / float(samples_per_seg)
            t2, t3 = t * t, t * t * t
            k = tension * 2.0
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * (k * t)
                              + (2 * p0 - 5 * p1 + 4 * p2 - p3) * (k * t2 * 0.5)
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * (k * t3 * 0.25)))
    return out


def superellipse(a, b, power=4.0, samples=32, phase=0.0):
    """超椭圆截面 [(u, v), ...]; power 越大越接近矩形, 2 为椭圆"""
    pts = []
    e = 2.0 / power
    for i in range(samples):
        t = TAU * i / samples + phase
        c, s = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** e, c)
        v = b * math.copysign(abs(s) ** e, s)
        pts.append((u, v))
    return pts


def circle_section(radius_a, radius_b=None, samples=24, phase=0.0):
    return superellipse(radius_a, radius_b if radius_b else radius_a,
                        2.0, samples, phase)


# ------------------------------------------------------------------ 参数曲面
def grid_surface(name, func, nu, nv, u0=0.0, u1=1.0, v0=0.0, v1=1.0,
                 wrap_u=False, wrap_v=False, mat=None, coll=None,
                 smooth=True, merge=1e-5):
    """参数曲面: func(u, v) -> (x, y, z); nu/nv 为两个方向的细分数"""
    verts = []
    for i in range(nu + (0 if wrap_u else 1)):
        u = u0 + (u1 - u0) * (i / float(nu))
        for j in range(nv + (0 if wrap_v else 1)):
            v = v0 + (v1 - v0) * (j / float(nv))
            verts.append(tuple(func(u, v)))
    stride = nv + (0 if wrap_v else 1)

    def idx(i, j):
        return (i % (nu if wrap_u else nu + 1)) * stride + \
               (j % (nv if wrap_v else nv + 1))

    faces = []
    for i in range(nu):
        for j in range(nv):
            faces.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1),
                          idx(i, j + 1)))
    return mesh_object(name, verts, faces, mat, coll, smooth, merge)


def loft_rings(name, rings, mat=None, coll=None, smooth=True,
               cap_start=False, cap_end=False, merge=1e-5):
    """一组等长顶点环之间的放样曲面; rings: [[(x,y,z), ...], ...]"""
    count = len(rings[0])
    verts = [tuple(p) for ring in rings for p in ring]
    faces = []
    for k in range(len(rings) - 1):
        a, b = k * count, (k + 1) * count
        for i in range(count):
            j = (i + 1) % count
            faces.append((a + i, a + j, b + j, b + i))
    if cap_start:
        faces.append(tuple(range(count - 1, -1, -1)))
    if cap_end:
        base = (len(rings) - 1) * count
        faces.append(tuple(base + i for i in range(count)))
    return mesh_object(name, verts, faces, mat, coll, smooth, merge)


# ------------------------------------------------------------------ 扫掠管道
def path_frames(path, initial_up=(0.0, 0.0, 1.0)):
    """平行传输标架: 返回与 path 等长的 (tangent, normal, binormal) 列表"""
    pts = [Vector(p) for p in path]
    n = len(pts)
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        if t.length < 1e-12:
            t = Vector((1.0, 0.0, 0.0))
        tangents.append(t.normalized())

    up = Vector(initial_up)
    if abs(tangents[0].dot(up)) > 0.999:
        up = Vector((0.0, 1.0, 0.0))
    normal = (up - tangents[0] * up.dot(tangents[0])).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            prev_t, cur_t = tangents[i - 1], tangents[i]
            axis = prev_t.cross(cur_t)
            if axis.length > 1e-9:
                angle = math.atan2(axis.length, prev_t.dot(cur_t))
                normal = Matrix.Rotation(angle, 3, axis.normalized()) @ normal
            normal = (normal - cur_t * normal.dot(cur_t))
            if normal.length < 1e-9:
                normal = Vector((0.0, 0.0, 1.0))
            normal.normalize()
        binormal = tangents[i].cross(normal)
        frames.append((tangents[i], normal, binormal))
    return frames


def sweep(name, path, section, mat=None, coll=None, smooth=True,
          caps=(True, True), initial_up=(0.0, 0.0, 1.0), scale_fn=None,
          merge=1e-5):
    """沿路径扫掠截面生成管状体

    section: [(u, v), ...] 局部截面点 (u 沿 normal, v 沿 binormal),
             或 callable(t) -> [(u, v), ...]
    """
    pts = [Vector(p) for p in path]
    frames = path_frames(pts, initial_up)
    n = len(pts)
    rings = []
    for i in range(n):
        _, nrm, bnm = frames[i]
        t = i / float(n - 1) if n > 1 else 0.0
        prof = section(t) if callable(section) else section
        sc = scale_fn(t) if scale_fn else 1.0
        rings.append([tuple(pts[i] + nrm * (u * sc) + bnm * (v * sc))
                      for (u, v) in prof])
    return loft_rings(name, rings, mat, coll, smooth, caps[0], caps[1], merge)


def pipe(name, path, radius, mat=None, coll=None, sides=12, samples=None,
         smooth_path=True, caps=(True, True), merge=1e-5):
    """圆形截面管道; radius 为常数或 callable(t)"""
    pts = [Vector(p) for p in path]
    if smooth_path and len(pts) > 2:
        pts = catmull_rom(pts, samples or 6)
    rfn = radius if callable(radius) else (lambda t: radius)
    sec = lambda t: circle_section(rfn(t), None, sides)
    return sweep(name, pts, sec, mat, coll, True, caps, merge=merge)


# ------------------------------------------------------------------ 旋转体
def revolve(name, profile, segments=64, mat=None, coll=None, smooth=True,
            center=(0.0, 0.0, 0.0), axis='Z', angle=TAU, cap_ends=True,
            merge=1e-5):
    """旋转体; profile: [(axial_position, radius), ...]"""
    ang = [angle * i / segments for i in range(segments + (1 if angle < TAU else 0))]
    wrap = angle >= TAU - 1e-9
    rings = []
    for a in ang:
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for (h, r) in profile:
            if axis == 'Z':
                ring.append((r * ca, r * sa, h))
            elif axis == 'X':
                ring.append((h, r * ca, r * sa))
            else:
                ring.append((r * ca, h, r * sa))
        rings.append(ring)
    if wrap:
        verts = [tuple(p) for ring in rings for p in ring]
        cnt = len(profile)
        faces = []
        for k in range(len(rings)):
            a = k * cnt
            b = ((k + 1) % len(rings)) * cnt
            for i in range(cnt - 1):
                faces.append((a + i, a + i + 1, b + i + 1, b + i))
        ob = mesh_object(name, verts, faces, mat, coll, smooth, merge)
        ob.location = center
        return ob
    ob = loft_rings(name, rings, mat, coll, smooth, cap_ends, cap_ends, merge)
    ob.location = center
    return ob


def cylinder(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), sides=32,
             mat=None, coll=None, smooth=True, taper=1.0):
    """中心在原点的圆柱 / 圆台"""
    h = depth * 0.5
    prof = [(-h, radius), (h, radius * taper)]
    ob = revolve(name, prof, sides, mat, coll, smooth, (0, 0, 0), 'Z',
                 cap_ends=True)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def finned_tube(name, z0, z1, r_core, r_fin, fin_gap, fin_th,
                segments=48, mat=None, coll=None, smooth=False,
                core_taper=1.0, fin_taper=1.0, cap=True):
    """带横向散热鳍片的筒体 (鳍片沿 Z 等距), 用于风冷缸体/缸头

    profile 沿 Z 由 z0 到 z1, 半径在 r_core 与 r_fin 之间交替, 形成锯齿。
    """
    total = z1 - z0
    if total <= 0:
        raise ValueError("z1 must exceed z0")
    profile = []
    z = z0
    guard = 0
    while guard < 500:
        guard += 1
        if z + fin_th + fin_gap > z1:
            break
        f = (z - z0) / total
        rc = r_core * (1.0 + (core_taper - 1.0) * f)
        rf = r_fin * (1.0 + (fin_taper - 1.0) * f)
        profile += [(z, rc), (z + fin_th * 0.25, rf), (z + fin_th, rf),
                    (z + fin_th * 1.3, rc)]
        z += fin_th + fin_gap
    f = 1.0
    profile.append((z1, r_core * core_taper))
    if profile[0][0] > z0:
        profile.insert(0, (z0, r_core))
    ob = revolve(name, profile, segments, mat, coll, smooth, (0, 0, 0),
                 'Z', cap_ends=cap)
    return ob


def plate(name, outline, thickness, loc=(0, 0, 0), rot=(0, 0, 0), mat=None,
          coll=None, smooth=False, holes=None):
    """由闭合轮廓挤出的平板; outline 为 XZ 平面的 [(x, z), ...]"""
    bm = bmesh.new()
    vs = [bm.verts.new((x, -thickness * 0.5, z)) for (x, z) in outline]
    try:
        face = bm.faces.new(vs)
    except ValueError:
        return None
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    verts = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(0.0, thickness, 0.0))
    ob = _finish(name, bm, mat, coll, smooth, 1e-6)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# ------------------------------------------------------------------ 圆角箱体
def rounded_box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), radius=0.01,
                segments=3, mat=None, coll=None, smooth=False):
    """带倒角的箱体; size 为全尺寸"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if radius > 1e-6:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts),
                        offset=radius, segments=segments, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    ob = _finish(name, bm, mat, coll, smooth, 1e-6)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, coll=None,
        smooth=False):
    return rounded_box(name, size, loc, rot, 0.0, 1, mat, coll, smooth)


def sphere(name, radius, loc=(0, 0, 0), segments=32, rings=16, mat=None,
           coll=None, smooth=True, scale=(1.0, 1.0, 1.0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings,
                              radius=radius)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    ob = _finish(name, bm, mat, coll, smooth, 0.0)
    ob.location = loc
    return ob


# ------------------------------------------------------------------ 紧固件
def poly_prism(name, sides, radius, height, loc=(0, 0, 0), rot=(0, 0, 0),
               rot_z=0.0, taper=1.0, mat=None, coll=None, smooth=False,
               cap=True):
    """正多棱柱 / 圆台 (中心在底面)"""
    bm = bmesh.new()
    bottom, top = [], []
    for i in range(sides):
        a = TAU * i / sides + rot_z
        bottom.append(bm.verts.new((radius * math.cos(a),
                                    radius * math.sin(a), 0.0)))
        r2 = radius * taper
        top.append(bm.verts.new((r2 * math.cos(a), r2 * math.sin(a), height)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    if cap:
        bm.faces.new(list(reversed(bottom)))
        bm.faces.new(top)
    ob = _finish(name, bm, mat, coll, smooth, 1e-6)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def hex_bolt(name, radius, height, loc=(0, 0, 0), rot=(0, 0, 0), mat=None,
             coll=None, washer=True, washer_scale=1.6):
    """六角头螺栓: 六角头 + (可选) 圆垫圈, 头底面位于 z=0"""
    bm = bmesh.new()
    sides = 6
    bottom, top = [], []
    for i in range(sides):
        a = TAU * i / sides
        bottom.append(bm.verts.new((radius * math.cos(a),
                                    radius * math.sin(a), 0.0)))
        top.append(bm.verts.new((radius * 0.88 * math.cos(a),
                                 radius * 0.88 * math.sin(a), height)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    if washer:
        seg = 20
        hw = height * 0.22
        wr = radius * washer_scale
        lo, hi = [], []
        for i in range(seg):
            a = TAU * i / seg
            lo.append(bm.verts.new((wr * math.cos(a), wr * math.sin(a), -hw)))
            hi.append(bm.verts.new((wr * math.cos(a), wr * math.sin(a), 0.0)))
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new(list(reversed(lo)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = _finish(name, bm, mat, coll, False, 0.0)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def bolt_ring(name_prefix, count, center, normal, radius, bolt_radius=0.004,
              bolt_height=0.006, mat=None, coll=None, phase=0.0):
    """沿圆周布置一圈螺栓; normal 为圆盘轴向"""
    n = Vector(normal).normalized()
    up = Vector((0.0, 0.0, 1.0))
    if abs(n.dot(up)) > 0.99:
        up = Vector((1.0, 0.0, 0.0))
    u = (up - n * up.dot(n)).normalized()
    v = n.cross(u)
    out = []
    for i in range(count):
        a = TAU * i / count + phase
        p = Vector(center) + u * (radius * math.cos(a)) + \
            v * (radius * math.sin(a))
        rot = n.to_track_quat('Z', 'Y').to_euler()
        out.append(hex_bolt(f"{name_prefix}_{i:02d}", bolt_radius, bolt_height,
                            tuple(p), (rot[0], rot[1], rot[2]), mat, coll))
    return out


# ------------------------------------------------------------------ 轮胎 / 轮辋
def tire_section(rim_radius, outer_radius, width, n=14, bead=0.62,
                 shoulder=0.72):
    """轮胎断面轮廓 [(r, w), ...] 闭合一圈; r=径向, w=半轴向宽度处

    从内侧 (-w) 起, 沿 +w 胎侧向外, 横跨胎面, 再沿 -w 胎侧回到内侧
    """
    ri, ro = rim_radius, outer_radius
    rw = width * 0.5
    w_in = rw * bead
    pts = []
    # 右侧胎侧: 由内缘 (ri, w_in) 外扩至胎肩 (ro, rw)
    for i in range(1, n + 1):
        t = math.sin((i / float(n)) * math.pi * 0.5)
        pts.append((ri + (ro - ri) * (t ** 0.75),
                    w_in + (rw - w_in) * (t ** 0.55)))
    # 胎面: 由 +rw 横跨至 -rw, 轻微拱起
    for i in range(1, n):
        w = rw * (1.0 - 2.0 * i / float(n))
        pts.append((ro - 0.010 * (1.0 - abs(w) / rw) ** 2, w))
    # 左侧胎侧: 由胎肩回到内缘
    for i in range(n, 0, -1):
        t = math.sin((i / float(n)) * math.pi * 0.5)
        pts.append((ri + (ro - ri) * (t ** 0.75),
                    -(w_in + (rw - w_in) * (t ** 0.55))))
    return pts


def tire(name, rim_radius, tire_height, width, mat=None, coll=None,
         segments=72, profile_samples=14, axis='Y', center=(0, 0, 0),
         bead=0.62):
    """轮胎: 断面绕轴旋转; 默认轴向为 Y (摩托车轮)"""
    sec = tire_section(rim_radius, rim_radius + tire_height, width,
                       profile_samples, bead)
    prof = [(w, r) for (r, w) in sec]
    prof.append(prof[0])
    return revolve(name, prof, segments, mat, coll, True, center,
                   axis=axis, cap_ends=False)


def wire_wheel(name, rim_radius, tire_height, tire_width, hub_radius,
               hub_width, spoke_count=40, cross=2, rim_width=None,
               spoke_radius=0.0035, mat=None, coll=None, axis='Y',
               hub_mat=None, rim_mat=None, segments=72, center=(0, 0, 0),
               hub_side=0.42, rim_side=0.22, spoke_sides=6):
    """钢丝辐条轮组: 轮胎 + 轮辋 + 轮毂 + 交叉编织辐条

    返回 dict: tire / rim / hub / spokes / parts
    axis='Y' 时轮轴沿 Y, 轮平面为 XZ
    """
    cx, cy, cz = center
    parts = {}
    parts['tire'] = tire(f"{name}_Tire", rim_radius, tire_height, tire_width,
                         mat, coll, segments, axis=axis, center=center)
    rw = rim_width or tire_width * 0.60
    dh = tire_height * 0.30
    # 轮辋: 环形槽, 剖面 (轴向, 半径)
    rim_prof = [(w, r) for (r, w) in (
        (rim_radius, -rw), (rim_radius - dh, -rw), (rim_radius - dh, rw),
        (rim_radius, rw), (rim_radius, rw * 0.55),
        (rim_radius - dh * 0.45, rw * 0.55), (rim_radius - dh * 0.45, -rw * 0.55),
        (rim_radius, -rw * 0.55), (rim_radius, -rw))]
    parts['rim'] = revolve(f"{name}_Rim", rim_prof, segments,
                           rim_mat or mat, coll, True, center, axis=axis)
    hub_prof = [(-hub_width * 0.5, hub_radius * 0.55),
                (-hub_width * 0.5, hub_radius),
                (-hub_width * 0.28, hub_radius * 1.05),
                (hub_width * 0.28, hub_radius * 1.05),
                (hub_width * 0.5, hub_radius),
                (hub_width * 0.5, hub_radius * 0.55)]
    parts['hub'] = revolve(f"{name}_Hub", hub_prof, max(24, segments // 2),
                           hub_mat or mat, coll, True, center, axis=axis)
    # 辐条: 两侧各 per_side 根, 交叉编织
    spokes = []
    per_side = spoke_count // 2
    for i in range(per_side):
        for side in (-1, 1):
            a0 = TAU * i / per_side
            a1 = TAU * ((i + cross) % per_side) / per_side
            ax0 = side * hub_width * hub_side
            ax1 = side * rw * rim_side
            r_hub = hub_radius * 0.97
            r_rim = rim_radius - dh * 0.5
            p0 = (ax0, r_hub * math.cos(a0), r_hub * math.sin(a0))
            p1 = (ax1, r_rim * math.cos(a1), r_rim * math.sin(a1))
            if axis == 'Y':
                v0 = (p0[1] + cx, p0[0] + cy, p0[2] + cz)
                v1 = (p1[1] + cx, p1[0] + cy, p1[2] + cz)
            else:
                v0 = (p0[0] + cx, p0[1] + cy, p0[2] + cz)
                v1 = (p1[0] + cx, p1[1] + cy, p1[2] + cz)
            spokes.append(pipe(f"{name}_Spoke_{i:02d}_{'A' if side < 0 else 'B'}",
                               [v0, v1], spoke_radius, mat, coll,
                               sides=spoke_sides, smooth_path=False))
    parts['spokes'] = spokes
    return parts


def _bm_tube(bm, p0, p1, radius, segments=6, cap=True):
    """向已有 bmesh 里添加一段圆柱 (用于批量生成辐条/管线)"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    if d.length < 1e-9:
        return
    m = d.to_track_quat('Z', 'Y').to_matrix()
    ring0, ring1 = [], []
    for i in range(segments):
        a = TAU * i / segments
        off = m @ Vector((radius * math.cos(a), radius * math.sin(a), 0.0))
        ring0.append(bm.verts.new(p0 + off))
        ring1.append(bm.verts.new(p1 + off))
    for i in range(segments):
        j = (i + 1) % segments
        try:
            bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        except ValueError:
            pass
    if cap:
        try:
            bm.faces.new(list(reversed(ring0)))
            bm.faces.new(ring1)
        except ValueError:
            pass


def spoke_set(name, center, rim_radius, hub_radius, hub_width, rim_width,
              count=40, cross=2, radius=0.0033, sides=6, mat=None,
              coll=None, axis='Y', rim_inset=0.030, hub_side=0.44,
              rim_side=0.30):
    """交叉编织钢丝辐条组 (合并为单个网格, 轴向默认 Y)"""
    bm = bmesh.new()
    per = max(1, count // 2)
    c = Vector(center)
    for i in range(per):
        for side in (-1, 1):
            a0 = TAU * i / per
            a1 = TAU * ((i + cross) % per) / per
            ax0 = side * hub_width * hub_side
            ax1 = side * rim_width * rim_side
            rh = hub_radius * 0.97
            rr = rim_radius - rim_inset
            if axis == 'Y':
                v0 = c + Vector((rh * math.cos(a0), ax0, rh * math.sin(a0)))
                v1 = c + Vector((rr * math.cos(a1), ax1, rr * math.sin(a1)))
            else:
                v0 = c + Vector((ax0, rh * math.cos(a0), rh * math.sin(a0)))
                v1 = c + Vector((ax1, rr * math.cos(a1), rr * math.sin(a1)))
            _bm_tube(bm, v0, v1, radius, sides)
    return _finish(name, bm, mat, coll, True, 1e-6)


def belt_loop(name, c1, r1, c2, r2, width, thickness, mat=None, coll=None,
              plane='XZ', axis_off=0.0, segments=40):
    """两轮之间的皮带: 外公切线 + 两端圆弧, 扫掠矩形截面

    c1/c2: 两轮中心 (3D), r1/r2: 半径, plane: 皮带所在平面
    """
    a = Vector(c1)
    b = Vector(c2)
    if plane == 'XZ':
        u = Vector((b.x - a.x, 0.0, b.z - a.z))
    else:
        u = Vector((b.x - a.x, b.y - a.y, 0.0))
    d = u.length
    if d < 1e-6:
        return None
    u.normalize()
    n = Vector((-u.z, 0.0, u.x)) if plane == 'XZ' else Vector((-u.y, u.x, 0.0))
    phi = math.acos(max(-1.0, min(1.0, (r1 - r2) / d)))
    pts = []
    dir_a = u * math.cos(phi) + n * math.sin(phi)
    dir_b = u * math.cos(phi) - n * math.sin(phi)

    def _ang(v):
        vv = v.z if plane == 'XZ' else v.y
        return math.atan2(vv, v.x)

    a_dir, b_dir = _ang(dir_a), _ang(dir_b)
    # 大轮 (c1) 上远离小轮的一侧, 包角 > 180 度
    span1 = (a_dir - b_dir) % TAU
    for i in range(segments + 1):
        t = b_dir + span1 * (i / float(segments))
        pts.append(a + (u * math.cos(t) + n * math.sin(t)) * r1)
    # 小轮 (c2) 上远离大轮的一侧
    span2 = (b_dir - a_dir) % TAU
    for i in range(segments + 1):
        t = a_dir + span2 * (i / float(segments))
        pts.append(b + (u * math.cos(t) + n * math.sin(t)) * r2)
    pts.append(pts[0])
    half = width * 0.5
    sec = [(-half, -thickness * 0.5), (half, -thickness * 0.5),
           (half, thickness * 0.5), (-half, thickness * 0.5)]
    return sweep(name, pts, sec, mat, coll, True, (False, False),
                 initial_up=(0.0, 1.0, 0.0))


# ------------------------------------------------------------------ 材质
def make_material(name, color, roughness=0.5, metallic=0.0, sheen=0.0,
                  coat=0.0, ior=1.45, alpha=1.0, emission=None,
                  emission_strength=1.0):
    """Principled BSDF 材质; Blender 5.x 需按 type 查找节点"""
    mat = bpy.data.materials.get(name)
    if mat is None:
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

    def setv(key, value):
        if key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = value
            except Exception:
                pass

    if len(color) == 4:
        setv("Base Color", tuple(color))
    else:
        setv("Base Color", (color[0], color[1], color[2], 1.0))
    setv("Roughness", roughness)
    setv("Metallic", metallic)
    setv("IOR", ior)
    setv("Sheen Weight", sheen)
    setv("Coat Weight", coat)
    setv("Alpha", alpha)
    if emission is not None:
        setv("Emission Color", (emission[0], emission[1], emission[2], 1.0))
        setv("Emission Strength", emission_strength)
    if alpha < 1.0:
        for attr, val in (("blend_method", 'BLEND'),
                          ("surface_render_method", 'BLENDED')):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
    return mat


def assign(ob, mat, slot=0):
    if mat is None:
        return ob
    if len(ob.data.materials) == 0:
        ob.data.materials.append(mat)
    else:
        ob.data.materials[slot] = mat
    return ob


def set_bsdf_input(mat, key, value):
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf and key in bsdf.inputs:
        bsdf.inputs[key].default_value = value
    return mat
