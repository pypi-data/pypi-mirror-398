import argparse
import subprocess
import os
import sys
def check_service_installed():
    # Check if ziti-edge-tunnel.service is enabled
    check_command = 'sudo systemctl is-enabled ziti-edge-tunnel.service'
    result = subprocess.run(check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def install_ziti():
    # Only install if not already installed
    if not check_service_installed():
        install_command = 'curl -sSLf https://get.openziti.io/tun/scripts/install-ubuntu.bash | bash'
        subprocess.run(install_command, shell=True, check=True)

def enable_service():
    enable_command = 'sudo systemctl enable --now ziti-edge-tunnel.service'
    subprocess.run(enable_command, shell=True, check=True)



def add_identity(jwt_file):
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    if not os.path.isfile(jwt_file):
        print(f"Error: JWT file '{jwt_file}' does not exist.")
        sys.exit(1)

    print(f"Adding identity using JWT file: {jwt_file}")
    identity_name = os.path.splitext(os.path.basename(jwt_file))[0]

    print("identity_name is",identity_name)

    try:
        # Read JWT file content
        with open(jwt_file, 'r') as file:
            jwt_content = file.read().strip()

        # Use the content directly in the command
        add_identity_command = f'sudo ziti-edge-tunnel add --jwt "{jwt_content}" --identity {identity_name}'
        print(f"Running command: {add_identity_command}")  # For debugging
        result = subprocess.run(add_identity_command, shell=True, check=True, capture_output=True, text=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to add identity: {e.stderr}")
        sys.exit(1)

def set_permissions():
    permissions_command1 = 'sudo chown -cR :ziti /opt/openziti/etc/identities'
    permissions_command2 = 'sudo chmod -cR ug=rwX,o-rwx /opt/openziti/etc/identities'
    subprocess.run(permissions_command1, shell=True, check=True)
    subprocess.run(permissions_command2, shell=True, check=True)

def restart_service():
    restart_command = 'sudo systemctl restart ziti-edge-tunnel.service'
    subprocess.run(restart_command, shell=True, check=True)

def main():
    parser = argparse.ArgumentParser(description='Tool to automate Ziti Edge Tunnel setup on Ubuntu.')
    parser.add_argument('jwt_file', metavar='JWT_FILE', help='Path to the JWT file')

    args = parser.parse_args()

    # Perform installation and setup steps
    install_ziti()
    enable_service()
    add_identity(args.jwt_file)
    set_permissions()
    restart_service()

    print("Ziti Edge Tunnel setup completed successfully.")

if __name__ == "__main__":
    main()


