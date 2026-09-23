import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import datetime
from pathlib import Path

# Data Setup
app_dir = Path("d:/WebApps/MIKROTIK/rb941-2nd Home/gui_app")
with open(app_dir / "data" / "templates.json", "r") as f:
    templates = json.load(f)
with open(app_dir / "data" / "assignments.json", "r") as f:
    assignments = json.load(f)

# Convert templates to dict
tpl_dict = {t["id"]: t for t in templates}

days_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
days_labels = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

def time_to_float(t_str):
    h, m = map(int, t_str.split(':'))
    return h + m/60.0

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle('Jadwal Akses Internet (FizhNetFlow)', fontsize=16, fontweight='bold')

targets = [('PC Hafizh', 'pc', '#4facf7'), ('HP Hafizh & Squad', 'hp', '#20c997')]

for idx, (title, target_key, color) in enumerate(targets):
    ax = axes[idx]
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylim(-0.5, 6.5)
    ax.set_xlim(0, 24)
    
    # Format axes
    ax.set_yticks(range(7))
    ax.set_yticklabels(reversed(days_labels))
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{i:02d}:00" for i in range(0, 25, 2)])
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    target_assign = assignments.get(target_key, {})
    
    for i, day in enumerate(reversed(days_order)):
        tpl_id = target_assign.get(day)
        if tpl_id and tpl_id in tpl_dict:
            tpl = tpl_dict[tpl_id]
            for session in tpl.get('sessions', []):
                start_h = time_to_float(session['start'])
                end_h = time_to_float(session['end'])
                if end_h == 23.983333333333334: end_h = 24.0 # 23:59
                duration = end_h - start_h
                rect = patches.Rectangle((start_h, i - 0.3), duration, 0.6, facecolor=color, edgecolor='black', alpha=0.8)
                ax.add_patch(rect)
                
                # Add text label for template name (only once per day if fits)
                if duration > 3:
                    ax.text(start_h + duration/2, i, tpl['name'], ha='center', va='center', color='black', fontsize=8)

plt.tight_layout()
output_path = app_dir / "jadwal_internet.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Schedule PNG generated at {output_path}")
