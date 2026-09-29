"""技术检查: 部件间隙/穿插检测 + 关键部位特写渲染"""
import os
import bpy

import moto_common as C

mt, st, P = C.reload_all()

_SKIP_RENDER = True
_P4 = os.path.join(C.ROOT, 'motorcycle', 'build_p4_paint.py')
exec(compile(open(_P4, encoding='utf-8').read(), _P4, 'exec'))

colls = globals()['colls']
checks = C.run_penetration_checks()
shots = C.render_views('chk', names=('left', 'd_engine', 'd_front', 'd_rear',
                                     'd_cockpit', 'd_exhaust'))
C.save()

names = [o.name for o in bpy.data.objects if o.name != 'Ground']
lo, hi, size = st.bbox_of(names)
tight = [(k, v) for k, v in checks.items()
         if isinstance(v, dict) and abs(v['min_mm']) < 70.0]
worst = sorted(tight, key=lambda kv: kv[1]['min_mm'])[:8]

result = {
    'stage': 'check',
    'shots': shots,
    'dimensions': {'length': round(size.x, 4), 'width': round(size.y, 4),
                   'height': round(size.z, 4)},
    'target': {'length': P.OVERALL_L, 'width': P.OVERALL_W,
               'height': P.OVERALL_H},
    'wheelbase': round(abs(P.AXLE_F[0] - P.AXLE_R[0]), 4),
    'seat_height': round(P.GROUND + P.SEAT_H, 4),
    'tightest_pairs': worst,
    'penetration_flags': [k for k, v in checks.items()
                          if isinstance(v, dict) and v['inside_pts'] > 0],
    'checks': checks,
}
