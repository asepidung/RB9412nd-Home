import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.88.1', port=22, username='idung', password='91142552', timeout=5, look_for_keys=False, allow_agent=False)
stdin, stdout, stderr = client.exec_command('/ip firewall filter print where comment~"^FizhNetFlow_"')
print(stdout.read().decode())
client.close()
