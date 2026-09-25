import json
import os
import paramiko
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TEMPLATES_FILE = os.path.join(DATA_DIR, 'templates.json')
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, 'assignments.json')
STATUS_FILE = os.path.join(DATA_DIR, 'status.json') # For mock status
MAC_NAMES_FILE = os.path.join(DATA_DIR, 'mac_names.json') # For mapping MAC to names
BLOCKED_MACS_FILE = os.path.join(DATA_DIR, 'blocked_macs.json') # For storing blocked MACs

# Ensure data files exist
if not os.path.exists(TEMPLATES_FILE):
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump([
            {"id": "t1", "name": "Hari Sekolah", "sessions": [{"start": "06:00", "end": "08:00"}, {"start": "13:00", "end": "16:30"}, {"start": "19:30", "end": "21:30"}]},
            {"id": "t2", "name": "Menjelang Libur", "sessions": [{"start": "06:00", "end": "08:00"}, {"start": "13:00", "end": "16:30"}, {"start": "19:30", "end": "23:59"}]},
            {"id": "t3", "name": "Hari Libur", "sessions": [{"start": "10:00", "end": "12:00"}, {"start": "13:30", "end": "16:30"}, {"start": "20:00", "end": "23:59"}]},
            {"id": "t4", "name": "Block All", "sessions": []}
        ], f)

if not os.path.exists(ASSIGNMENTS_FILE):
    with open(ASSIGNMENTS_FILE, 'w') as f:
        json.dump({
            "pc": {
                "mon": "t1", "tue": "t1", "wed": "t1", "thu": "t1",
                "fri": "t2", "sat": "t3", "sun": "t3"
            },
            "hp": {
                "mon": "t1", "tue": "t1", "wed": "t1", "thu": "t1",
                "fri": "t2", "sat": "t3", "sun": "t3"
            }
        }, f)

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'w') as f:
        json.dump({"pc_hafizh": True, "hp_hafizh": True}, f)

if not os.path.exists(MAC_NAMES_FILE):
    with open(MAC_NAMES_FILE, 'w') as f:
        json.dump({
            "AA:BB:CC:DD:EE:FF": "HP Hafizh",
            "11:22:33:44:55:66": "PC Hafizh"
        }, f)

if not os.path.exists(BLOCKED_MACS_FILE):
    with open(BLOCKED_MACS_FILE, 'w') as f:
        json.dump([], f)

# Helper functions
def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Routes ---

@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        app_user = os.getenv('APP_USER', 'admin')
        app_pass = os.getenv('APP_PASS', 'admin123')
        if request.form['username'] == app_user and request.form['password'] == app_pass:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/jadwal')
def jadwal_public():
    templates_list = load_json(TEMPLATES_FILE)
    templates = {t['id']: t for t in templates_list} if isinstance(templates_list, list) else templates_list
    assignments = load_json(ASSIGNMENTS_FILE)
    
    # Handle legacy assignments format
    if "mon" in assignments:
        assignments = {"pc": assignments, "hp": assignments}
        
    days = [('mon', 'Senin'), ('tue', 'Selasa'), ('wed', 'Rabu'), ('thu', 'Kamis'), ('fri', 'Jumat'), ('sat', 'Sabtu'), ('sun', 'Minggu')]
    
    schedule_data = []
    for day_code, day_name in days:
        day_schedule = {"hari": day_name, "sesi": []}
        
        hp_tpl_id = assignments.get('hp', {}).get(day_code)
        pc_tpl_id = assignments.get('pc', {}).get(day_code)
        
        hp_sessions = templates.get(hp_tpl_id, {}).get('sessions', []) if hp_tpl_id else []
        pc_sessions = templates.get(pc_tpl_id, {}).get('sessions', []) if pc_tpl_id else []
        
        max_sesi = max(len(hp_sessions), len(pc_sessions), 3)
        sesi_names = ["Pagi", "Sore", "Malam", "Ekstra 1", "Ekstra 2"]
        
        for i in range(max_sesi):
            s_name = sesi_names[i] if i < len(sesi_names) else f"Sesi {i+1}"
            
            hp_time = "-"
            if i < len(hp_sessions):
                hp_time = f"{hp_sessions[i]['start']} - {hp_sessions[i]['end']}"
                
            pc_time = "-"
            if i < len(pc_sessions):
                pc_time = f"{pc_sessions[i]['start']} - {pc_sessions[i]['end']}"
                
            day_schedule["sesi"].append({
                "nama_sesi": s_name,
                "hp": hp_time,
                "pc": pc_time
            })
            
        schedule_data.append(day_schedule)
        
    return render_template('jadwal.html', schedule=schedule_data)

# --- API Endpoints ---

@app.route('/api/status', methods=['GET', 'POST'])
def api_status():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        data = request.json
        status = load_json(STATUS_FILE)
        if 'pc_hafizh' in data: status['pc_hafizh'] = data['pc_hafizh']
        if 'hp_hafizh' in data: status['hp_hafizh'] = data['hp_hafizh']
        save_json(STATUS_FILE, status)
        return jsonify({"success": True, "status": status})
    return jsonify(load_json(STATUS_FILE))

@app.route('/api/templates', methods=['GET', 'POST'])
def api_templates():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        templates = request.json
        save_json(TEMPLATES_FILE, templates)
        return jsonify({"success": True})
    return jsonify(load_json(TEMPLATES_FILE))

@app.route('/api/assignments', methods=['GET', 'POST'])
def api_assignments():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if request.method == 'POST':
        assignments = request.json
        save_json(ASSIGNMENTS_FILE, assignments)
        return jsonify({"success": True})
    
    # Backward compatibility with old flat structure if exist
    assignments = load_json(ASSIGNMENTS_FILE)
    if "mon" in assignments:
        assignments = {"pc": assignments, "hp": assignments}
    return jsonify(assignments)

@app.route('/api/devices', methods=['GET', 'POST'])
def api_devices():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    mac_names = load_json(MAC_NAMES_FILE)
    blocked_macs = load_json(BLOCKED_MACS_FILE)
    
    if request.method == 'POST':
        data = request.json
        # Handle rename
        if "name" in data:
            mac_names[data['mac']] = data['name']
            save_json(MAC_NAMES_FILE, mac_names)
        
        # Handle block/unblock
        if "blocked" in data:
            mac = data['mac']
            if data['blocked'] and mac not in blocked_macs:
                blocked_macs.append(mac)
            elif not data['blocked'] and mac in blocked_macs:
                blocked_macs.remove(mac)
            save_json(BLOCKED_MACS_FILE, blocked_macs)
            
        return jsonify({"success": True})

    # Fetch real devices from Mikrotik DHCP Leases
    MIKROTIK_IP = os.getenv('MIKROTIK_IP', '192.168.88.1')
    MIKROTIK_PORT = int(os.getenv('MIKROTIK_PORT', 22))
    MIKROTIK_USER = os.getenv('MIKROTIK_USER', 'admin')
    MIKROTIK_PASS = os.getenv('MIKROTIK_PASS', '')
    DRY_RUN = os.getenv('DRY_RUN', 'True').lower() in ('true', '1', 't')
    
    connected_devices = []
    
    if not DRY_RUN:
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(MIKROTIK_IP, port=MIKROTIK_PORT, username=MIKROTIK_USER, password=MIKROTIK_PASS, timeout=5, look_for_keys=False, allow_agent=False, disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']})
            
            # Print terse for easier regex parsing
            stdin, stdout, stderr = client.exec_command('/ip dhcp-server lease print terse where status=bound')
            output = stdout.read().decode('utf-8')
            client.close()
            
            # Parse terse output
            # Example: 0   mac-address=AA:BB:CC:DD:EE:FF address=192.168.88.254 host-name="PC-Hafizh" ...
            import re
            for line in output.splitlines():
                if not line.strip(): continue
                mac_match = re.search(r'mac-address=([0-9A-Fa-f:]+)', line)
                ip_match = re.search(r'address=([0-9\.]+)', line)
                hostname_match = re.search(r'host-name=("[^"]+"|[^ \n]+)', line)
                
                if mac_match and ip_match:
                    mac = mac_match.group(1).upper()
                    ip = ip_match.group(1)
                    hostname = hostname_match.group(1).strip('"') if hostname_match else ""
                    
                    connected_devices.append({
                        "mac": mac,
                        "ip": ip,
                        "type": "dhcp",
                        "hostname": hostname
                    })
        except Exception as e:
            print("Failed to fetch DHCP leases:", str(e))
    else:
        # Fallback to mock data for DRY_RUN
        connected_devices = [
            {"mac": "6C:4C:BC:88:EE:F8", "ip": "192.168.88.254", "type": "dhcp", "hostname": "PC Hafizh"},
            {"mac": "12:61:4D:C4:6D:25", "ip": "192.168.88.253", "type": "dhcp", "hostname": "HP Hafizh"},
            {"mac": "99:88:77:66:55:44", "ip": "192.168.88.15", "type": "dhcp", "hostname": "Unknown"}
        ]
    
    # Append metadata
    for dev in connected_devices:
        # Use known name if we have it in mac_names, otherwise fallback to hostname, else Unknown
        known_name = mac_names.get(dev['mac'])
        dev['name'] = known_name if known_name else (dev.get('hostname') or "Unknown Device")
        dev['blocked'] = dev['mac'] in blocked_macs
        
    return jsonify(connected_devices)

@app.route('/api/apply', methods=['POST'])
def api_apply():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    # --- Load Configuration ---
    MIKROTIK_IP = os.getenv('MIKROTIK_IP', '192.168.88.1')
    MIKROTIK_PORT = int(os.getenv('MIKROTIK_PORT', 22))
    MIKROTIK_USER = os.getenv('MIKROTIK_USER', 'admin')
    MIKROTIK_PASS = os.getenv('MIKROTIK_PASS', '')
    DRY_RUN = os.getenv('DRY_RUN', 'True').lower() in ('true', '1', 't')
    
    PC_MACS = os.getenv('PC_MACS', '').split(',')
    HP_MACS = os.getenv('HP_MACS', '').split(',')
    BYPASS_MACS = os.getenv('BYPASS_MACS', '').split(',')
    
    # --- Load Data ---
    templates_list = load_json(TEMPLATES_FILE)
    templates = {t['id']: t for t in templates_list} if isinstance(templates_list, list) else templates_list
    assignments = load_json(ASSIGNMENTS_FILE)
    status = load_json(STATUS_FILE)
    blocked_macs = load_json(BLOCKED_MACS_FILE)
    
    # Handle legacy assignments format
    if "mon" in assignments:
        assignments = {"pc": assignments, "hp": assignments}
        
    cmds = []
    
    # 1. CLEANUP OLD RULES
    cmds.append('/ip firewall filter remove [find comment~"^FizhNetFlow_"]')
    cmds.append('/ip firewall filter remove [find chain=fizhnetflow]')
    
    # 1.5 SETUP FIZHNETFLOW CHAIN
    cmds.append('/ip firewall filter add chain=forward action=jump jump-target=fizhnetflow comment="FizhNetFlow_Jump" place-before=0')
    
    # 1.6 APPLY VIP BYPASS (Always allow)
    for mac in BYPASS_MACS:
        if mac.strip():
            cmds.append(f'/ip firewall filter add chain=fizhnetflow src-mac-address={mac.strip()} action=return comment="FizhNetFlow_VIP_Bypass"')
            
    # 1.7 CPU SAVER (Accept established/related to prevent 100% CPU load on hAP lite)
    cmds.append('/ip firewall filter add chain=fizhnetflow connection-state=established,related action=return comment="FizhNetFlow_CPU_Saver"')
            
    # 1.8 APPLY VIP GAME BYPASS (Anti-Lag for Mobile Legends)
    cmds.append('/ip firewall filter add chain=fizhnetflow packet-mark=mlbb_pkt action=return comment="FizhNetFlow_VIP_Game_Bypass"')

    # 2. APPLY KILL SWITCHES (Highest Priority)
    if not status.get('pc_hafizh', True):
        for mac in PC_MACS:
            if mac.strip():
                cmds.append(f'/ip firewall filter add chain=fizhnetflow src-mac-address={mac.strip()} action=drop comment="FizhNetFlow_Kill_PC"')
                
    if not status.get('hp_hafizh', True):
        # HP Kill Switch applies to bridge-lan instead of specific MACs
        cmds.append(f'/ip firewall filter add chain=fizhnetflow in-interface=bridge-lan action=drop comment="FizhNetFlow_Kill_HP"')
                
    # 3. APPLY BLOCKED CONNECTED DEVICES
    for mac in blocked_macs:
        cmds.append(f'/ip firewall filter add chain=fizhnetflow src-mac-address={mac} action=drop comment="FizhNetFlow_Blocked_Device"')

    # 3.5 POPULATE WHATSAPP ADDRESS LIST (Dynamic IPs)
    cmds.append('/ip firewall address-list remove [find list="WhatsApp_IPs"]')
    wa_domains = ['whatsapp.com', 'whatsapp.net', 'wa.me', 'c.whatsapp.net', 'v.whatsapp.net', 'e1.whatsapp.net', 'e2.whatsapp.net', 'e3.whatsapp.net', 'e4.whatsapp.net', 'e5.whatsapp.net', 'e6.whatsapp.net', 'e7.whatsapp.net', 'e8.whatsapp.net', 'e9.whatsapp.net', 'e10.whatsapp.net', 'e11.whatsapp.net', 'e12.whatsapp.net', 'e13.whatsapp.net', 'e14.whatsapp.net', 'e15.whatsapp.net', 'e16.whatsapp.net', 'mmg.whatsapp.net', 'pps.whatsapp.net', 'fna.whatsapp.net']
    for dom in wa_domains:
        cmds.append(f'/ip firewall address-list add list=WhatsApp_IPs address={dom}')

    # 4. BUILD SCHEDULE RULES
    # Helper to group assignments by template
    def build_schedule_for_target(target_assignments, target_macs, comment_suffix):
        days_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        
        # Map template_id -> list of days it is active
        tpl_days = {}
        for day, tpl_id in target_assignments.items():
            if tpl_id and tpl_id in templates:
                if tpl_id not in tpl_days:
                    tpl_days[tpl_id] = []
                tpl_days[tpl_id].append(day[:3])
                
        match_criteria = [f'src-mac-address={m.strip()}' for m in target_macs if m.strip()]
        if not match_criteria:
            match_criteria = ['in-interface=bridge-lan']

        for tpl_id, days in tpl_days.items():
            tpl = templates[tpl_id]
            days_str = ",".join(days)
            for session_info in tpl.get('sessions', []):
                start = session_info['start']
                end = session_info['end']
                
                # Convert to comparable integers (minutes)
                s_min = int(start.split(':')[0])*60 + int(start.split(':')[1])
                e_min = int(end.split(':')[0])*60 + int(end.split(':')[1])
                
                start_str = start + ":00"
                
                if e_min < s_min:
                    # Session crosses midnight! We must split it into two rules.
                    # 1. Current days: start to 23:59:59
                    end_str_1 = "23:59:59"
                    
                    # 2. Next days: 00:00:00 to end
                    end_str_2 = end + ":59" if end == "23:59" else end + ":00"
                    next_days = [days_order[(days_order.index(d) + 1) % 7] for d in days]
                    next_days_str = ",".join(next_days)
                    
                    for criteria in match_criteria:
                        # Part 1 (Current Day)
                        cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} action=return time={start_str}-{end_str_1},{days_str} comment="FizhNetFlow_Allow_{comment_suffix}"')
                        # Part 2 (Next Day Spillover)
                        cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} action=return time=00:00:00-{end_str_2},{next_days_str} comment="FizhNetFlow_Allow_Spillover_{comment_suffix}"')
                else:
                    # Normal session
                    end_str = end + ":59" if end == "23:59" else end + ":00"
                    for criteria in match_criteria:
                        cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} action=return time={start_str}-{end_str},{days_str} comment="FizhNetFlow_Allow_{comment_suffix}"')

        # WHATSAPP & DNS BYPASS (Always allow WA even outside schedule)
        for criteria in match_criteria:
            # Allow DNS (Crucial for WA to find its servers if using external DNS)
            cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} protocol=udp dst-port=53 action=return comment="FizhNetFlow_Allow_DNS_{comment_suffix}"')
            
            # Allow WA Chat Ports
            cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} protocol=tcp dst-port=5222,5223,5228,4244,5242 action=return comment="FizhNetFlow_Allow_WA_Chat_{comment_suffix}"')
            
            # Allow WA Calls (UDP STUN & Media)
            cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} protocol=udp dst-port=3478,45395,50318,59234 action=return comment="FizhNetFlow_Allow_WA_Call_{comment_suffix}"')
            
            # Allow WhatsApp IP ranges based on known Facebook/WA ASNs (Simplified for Home use)
            # Instead of tls-host (which drops TCP SYN), we use a widely known WA subnet trick or Address List
            cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} dst-address-list=WhatsApp_IPs action=return comment="FizhNetFlow_Allow_WA_Media_{comment_suffix}"')

        # Finally, drop ALL other traffic for this target that didn't match the allowed times
        # This acts as the default block if not inside a schedule.
        for criteria in match_criteria:
            cmds.append(f'/ip firewall filter add chain=fizhnetflow {criteria} action=drop comment="FizhNetFlow_Drop_{comment_suffix}_Outside_Schedule"')

    # Build for PC
    if 'pc' in assignments:
        build_schedule_for_target(assignments['pc'], PC_MACS, "PC")
        
    # Build for HP (Pass empty list for target_macs so it creates a blanket rule)
    if 'hp' in assignments:
        build_schedule_for_target(assignments['hp'], [], "HP")
        
    print("----- COMMANDS TO EXECUTE -----")
    for c in cmds: print(c)
    print("-------------------------------")
    
    if DRY_RUN:
        print("[DRY RUN] Commands printed to console, not sent to router.")
        return jsonify({"success": True, "message": "Dry run successful. Check console for commands."})
        
    # Execute via Paramiko
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(MIKROTIK_IP, port=MIKROTIK_PORT, username=MIKROTIK_USER, password=MIKROTIK_PASS, timeout=10, look_for_keys=False, allow_agent=False, disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']})
        
        for cmd in cmds:
            client.exec_command(cmd)
            
        client.close()
        return jsonify({"success": True, "message": "Schedules successfully applied to MikroTik!"})
    except Exception as e:
        print(f"FAILED SSH: {e}")
        return jsonify({"error": f"SSH Connection Failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
