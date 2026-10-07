#!/usr/bin/env python3
"""Re-apply design rules / net classes to the .kicad_pro (pcbnew.SaveBoard resets them)."""
import json
p = '/home/karpulis/KiCad/E0001 - fader driver board/E0001_fader_driver.kicad_pro'
d = json.load(open(p))
ds = d.setdefault('board', {}).setdefault('design_settings', {})
r = ds.setdefault('rules', {})
r.update({"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
          "min_via_annular_width": 0.1, "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
          "min_silk_clearance": 0.0, "min_text_height": 0.7, "min_text_thickness": 0.1, "min_connection": 0.0})
ds['track_widths'] = [0.0, 0.2, 0.25, 0.3, 0.4, 0.6, 0.8]
ds['via_dimensions'] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}, {"diameter": 0.8, "drill": 0.4}]
sev = ds.setdefault('rule_severities', {})
sev.update({"lib_footprint_mismatch": "warning", "lib_footprint_issues": "warning"})
ns = d.setdefault('net_settings', {})
classes = ns.get('classes') or []
base = dict(classes[0]) if classes else {}
default = dict(base); default.update({"name": "Default", "clearance": 0.16, "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3,
                                      "priority": 2147483647})
power = dict(base); power.update({"name": "Power", "clearance": 0.2, "track_width": 0.5, "via_diameter": 0.8, "via_drill": 0.4,
                                  "priority": 0})
ns['classes'] = [default, power]
ns['netclass_patterns'] = [{"netclass": "Power", "pattern": "/VIN"}, {"netclass": "Power", "pattern": "+5V"},
                           {"netclass": "Power", "pattern": "/MOTOR_P"}, {"netclass": "Power", "pattern": "/MOTOR_N"}]
json.dump(d, open(p, 'w'), indent=2)
print('patched', p)
