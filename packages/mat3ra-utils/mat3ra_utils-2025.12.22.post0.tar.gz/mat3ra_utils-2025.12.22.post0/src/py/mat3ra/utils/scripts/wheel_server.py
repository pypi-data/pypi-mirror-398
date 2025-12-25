# This script serves static files from the 'dist' directory for Python wheel installation.
# Usage:
# Option 1: Build and Serve
# 1. Install dependencies with `pip install ".[dev]"`
# 2. Install the build tool with `pip install build`
# 3. Build the wheel with `python -m build`. You should see output like:
#    ```Successfully built mat3ra_api_examples-dev9+g7c6e8d9.tar.gz and
#    mat3ra_api_examples-dev9+g7c6e8d9-py3-none-any.whl```
# 4. Run the server to serve the newly built files: `python wheel_server.py`
#    This serves the files at http://localhost:8080 (or the next available port).
#
# Option 2: Serve Existing Files
# - To skip the build process and serve existing files, use the `--skip-build` flag:
#   `python wheel_server.py --skip-build`
#   This is useful when you already have built wheels in the 'dist' directory.
#
# General:
# - The server will output the full URL of the served wheel file, which can be used directly.
# - To install the wheel using micropip in Pyodide:
#   ```await micropip.install('<server_url>/<wheel_file_name>', deps=False)```
# - The script outputs the URL to use in the notebook or `config.yml` file for convenience.


import argparse
import glob
import os
import socket
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler


class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        super().end_headers()


def run_command(command):
    """Utility function to run a shell command."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")
        exit(1)


def setup_environment(directory):
    """Setup the build environment by installing dependencies and the build tool."""
    print("Cleaning old builds...")
    for file in glob.glob(f"{directory}/*.whl") + glob.glob(f"{directory}/*.tar.gz"):
        os.remove(file)
        print(f"Removed {file}")

    print("Installing dependencies...")
    run_command('pip install ".[dev]"')

    print("Installing build tool...")
    run_command("pip install build")

    print("Building the wheel file...")
    run_command("python -m build")


def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def inform_user(port):
    whl_files = glob.glob("*.whl")
    file = whl_files[0] if whl_files else None
    url_str = f"http://localhost:{port}/{file}"
    print("Copy URL to use in notebook or `config.yml`: ", url_str, "\n")
    print(f"import micropip\nawait micropip.install('{url_str}')\n")


def main():
    parser = argparse.ArgumentParser(description="Python wheel server.")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on.")
    parser.add_argument("--dir", type=str, default="./dist", help="Directory to serve.")
    parser.add_argument("--skip-build", action="store_true", help="Skip building the wheel and serve existing files.")
    args = parser.parse_args()

    if not args.skip_build:
        setup_environment(args.dir)

    port = args.port
    bind_addr = "localhost"
    directory = args.dir

    os.chdir(directory)
    while check_port(bind_addr, port):
        print(f"Port {port} is already in use. Trying with port {port + 1}.")
        port += 1

    httpd = HTTPServer((bind_addr, port), CORSHTTPRequestHandler)
    print(f"Serving at http://{bind_addr}:{port}")
    inform_user(port)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
