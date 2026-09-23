import json
import os

app_dir = "d:/WebApps/MIKROTIK/rb941-2nd Home/gui_app"
with open(os.path.join(app_dir, 'data/templates.json')) as f: templates = {t['id']: t for t in json.load(f)}
with open(os.path.join(app_dir, 'data/assignments.json')) as f: assignments = json.load(f)

PC_MACS = ["6C:4C:BC:88:EE:F8"]
cmds = []
def build(target_ass, target_macs, suffix):
    tpl_days = {}
    for day, tpl_id in target_ass.items():
        if tpl_id and tpl_id in templates:
            if tpl_id not in tpl_days: tpl_days[tpl_id] = []
            tpl_days[tpl_id].append(day[:3])
            
    days_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    
    for tpl_id, days in tpl_days.items():
        tpl = templates[tpl_id]
        days_str = ','.join(days)
        for s in tpl.get('sessions', []):
            start = s['start']
            end = s['end']
            s_min = int(start.split(':')[0])*60 + int(start.split(':')[1])
            e_min = int(end.split(':')[0])*60 + int(end.split(':')[1])
            start_str = start + ':00'
            if e_min < s_min:
                end_str_1 = '23:59:59'
                end_str_2 = end + ':59' if end == '23:59' else end + ':00'
                next_days = [days_order[(days_order.index(d) + 1) % 7] for d in days]
                next_days_str = ','.join(next_days)
                for mac in target_macs:
                    if mac.strip():
                        cmds.append(f'/ip firewall filter add chain=forward src-mac-address={mac.strip()} action=accept time={start_str}-{end_str_1},{days_str} comment=\"FizhNetFlow_Allow_{suffix}\"')
                        cmds.append(f'/ip firewall filter add chain=forward src-mac-address={mac.strip()} action=accept time=00:00:00-{end_str_2},{next_days_str} comment=\"FizhNetFlow_Allow_Spillover_{suffix}\"')
            else:
                end_str = end + ':59' if end == '23:59' else end + ':00'
                for mac in target_macs:
                    if mac.strip():
                        cmds.append(f'/ip firewall filter add chain=forward src-mac-address={mac.strip()} action=accept time={start_str}-{end_str},{days_str} comment=\"FizhNetFlow_Allow_{suffix}\"')

build(assignments.get('pc', {}), PC_MACS, 'PC')
for c in cmds: print(c)
