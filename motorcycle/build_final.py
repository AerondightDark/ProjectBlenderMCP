"""最终构建: 重建全部资产 + 穿插检查 + 全视图渲染 + 保存"""
import os
import bpy

import moto_common as C

mt, st, P = C.reload_all()

_SKIP_RENDER = True
_P4 = os.path.join(C.ROOT, 'motorcycle', 'build_p4_paint.py')
exec(compile(open(_P4, encoding='utf-8').read(), _P4, 'exec'))

colls = globals()['colls']
checks = C.run_penetration_checks()

st.setup_render('BLENDER_EEVEE', (1600, 1200), samples=96,
                view_transform='Standard')
shots = C.render_views('final', names=('left', 'right', 'front', 'rear',
                                       'q34f', 'q34r', 'top'),
                       res=(1600, 1200))
C.save(os.path.join(C.ROOT, 'motorcycle', 'Motorcycle.blend'))

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
stats = st.object_stats()
tight = sorted([(k, v) for k, v in checks.items()
                if isinstance(v, dict) and abs(v['min_mm']) < 30.0],
               key=lambda kv: kv[1]['min_mm'])

result = {
    'stage': 'final',
    'shots': shots,
    'dimensions_m': {'length': round(size.x, 4), 'width': round(size.y, 4),
                     'height': round(size.z, 4)},
    'target_m': {'length': P.OVERALL_L, 'width': P.OVERALL_W,
                 'height': P.OVERALL_H},
    'deviation_pct': {
        'length': round((size.x - P.OVERALL_L) / P.OVERALL_L * 100.0, 2),
        'width': round((size.y - P.OVERALL_W) / P.OVERALL_W * 100.0, 2),
        'height': round((size.z - P.OVERALL_H) / P.OVERALL_H * 100.0, 2),
    },
    'wheelbase_m': round(abs(P.AXLE_F[0] - P.AXLE_R[0]), 4),
    'seat_height_m': round(P.GROUND + P.SEAT_H, 4),
    'mesh_objects': stats['objects'],
    'total_verts': stats['verts'],
    'total_tris': stats['tris'],
    'tight_pairs_mm': tight,
}
