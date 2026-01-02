import os
import subprocess
import sys
import requests
import http.server
import socketserver

def install_from_pypi(package_name: str):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code != 200:
        return f"❌ Package '{package_name}' not found in PyPI."
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return f"✅ Package '{package_name}' was successfully installed."
    except subprocess.CalledProcessError:
        return f"⚠️ Error installing package '{package_name}'."

def search_web(query: str, api_key: str, count: int = 5):

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": count}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    
    return [
        {"title": item["name"], "url": item["url"]}
        for item in results.get("webPages", {}).get("value", [])
    ]
def apos(folder: str, port_input: int, ip, homepage: str):

    if not os.path.isdir(folder):
        return "❌ There is no path."
    try:
        port = int(port_input)
    except ValueError:
        return "❌ The port must be a number."

    homepage_path = os.path.join(folder, homepage)
    if not os.path.isfile(homepage_path):
        return f"❌ The homepage file '{homepage}' does not exist in the path '{folder}'."

    os.chdir(folder)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.path = "/" + homepage
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    handler = CustomHandler

    try:
        with socketserver.TCPServer((ip, port), handler) as httpd:
            print(f"✅ Serving folder '{folder}' at http://{ip}:{port} with homepage '{homepage}'")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            return f"❌ Port {port} is currently busy."
        else:
            return f"❌ {e}"
