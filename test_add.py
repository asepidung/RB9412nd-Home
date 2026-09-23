import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.88.1', port=22, username='idung', password='91142552', timeout=5, look_for_keys=False, allow_agent=False)

cmd = '/ip firewall filter add chain=forward src-mac-address=6C:4C:BC:88:EE:F8 action=accept time=06:00:00-08:00:00,mon,thu,tue,wed comment="FizhNetFlow_Allow_PC"'
print("Running:", cmd)
stdin, stdout, stderr = client.exec_command(cmd)
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

client.close()
