import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

def get_device_connection():
    return {
        'device_type': 'cisco_xe',
        'host': os.getenv('DEVICE_HOST'),
        'username': os.getenv('DEVICE_USER'),
        'password': os.getenv('DEVICE_PASS'),
        'port': int(os.getenv('DEVICE_PORT', 22)),
    }

def backup_config(net_connect):
    print("📦 Backing up configuration...")
    config = net_connect.send_command('show running-config')
    filename = f"backups/{os.getenv('DEVICE_HOST')}_config.txt"
    with open(filename, 'w') as f:
        f.write(config)
    print(f"✅ Backup saved to {filename}")

def run_audit(net_connect):
    print("🔍 Running interface audit...")
    output = net_connect.send_command('show ip interface brief')
    print(output)

def run_config(net_connect):
    try:
       filename = "configs/config.txt"
       with open(filename) as f:
            commands_to_send = f.read().splitlines()
       print(f"📦 Modifying configuration with {filename}...")
       net_connect.send_config_set(commands_to_send)
       print("✅ Configuration modified successfully!")
    except FileNotFoundError:
       print("🔍 No configuration file found. Nothing to do.")

def main():
    device = get_device_connection()
    try:
        with ConnectHandler(**device) as net_connect:
            print("🚀 Connected successfully!")
            run_audit(net_connect)
            backup_config(net_connect)
            run_config(net_connect)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
