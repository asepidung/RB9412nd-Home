import json
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

app_dir = Path("d:/WebApps/MIKROTIK/rb941-2nd Home/gui_app")
with open(app_dir / "data" / "templates.json", "r") as f:
    templates = json.load(f)
with open(app_dir / "data" / "assignments.json", "r") as f:
    assignments = json.load(f)

tpl_dict = {t["id"]: t for t in templates}

days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
days_indo = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

def get_sessions_str(tpl_id):
    if not tpl_id or tpl_id not in tpl_dict: return "Blocked All"
    tpl = tpl_dict[tpl_id]
    if not tpl.get('sessions'): return "Blocked All"
    sessions = []
    for s in tpl['sessions']:
        sessions.append(f"{s['start']}-{s['end']}")
    return "\n".join(sessions)

pc_sched = [get_sessions_str(assignments.get('pc', {}).get(d)) for d in days]
hp_sched = [get_sessions_str(assignments.get('hp', {}).get(d)) for d in days]

import dataframe_image as dfi

df = pd.DataFrame({
    'Hari': days_indo,
    'PC Hafizh': pc_sched,
    'HP Hafizh & Squad': hp_sched
})

# Apply Pandas Styling
def style_df(styler):
    styler.set_properties(**{
        'background-color': '#f8f9fa',
        'color': '#333',
        'border': '1px solid #dee2e6',
        'padding': '10px',
        'text-align': 'center',
        'vertical-align': 'middle',
        'white-space': 'pre-wrap'
    })
    styler.set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#4c51bf'), 
            ('color', 'white'), 
            ('font-weight', 'bold'),
            ('padding', '12px'),
            ('text-align', 'center'),
            ('font-size', '14px')
        ]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#ffffff')]},
        {'selector': 'td', 'props': [('font-size', '13px'), ('line-height', '1.5')]}
    ])
    styler.hide(axis="index")
    return styler

styled_df = df.style.pipe(style_df)

output_path = app_dir / "jadwal_tabel.png"
dfi.export(styled_df, str(output_path), table_conversion='matplotlib')
print("Table PNG generated with dataframe_image!")
