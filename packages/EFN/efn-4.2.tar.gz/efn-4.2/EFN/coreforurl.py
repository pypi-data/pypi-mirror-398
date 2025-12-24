import requests, platform, subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
import ssl

def geturl(url):
    return requests.get(url).text

def downloadfile(url, destination):
    try:
        r = requests.get(url)
        with open(destination, "wb") as f:
            f.write(r.content)
        return "File downloaded successfully!"
    except Exception as e:
        return f"Download failed: {e}"

def getip():
    try:
        return requests.get("https://api.ipify.org").text
    except Exception as e:
        return f"Error: {e}"

def pingserver(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", host]
    try:
        output = subprocess.check_output(command)
        return output.decode()
    except Exception as e:
        return f"Ping failed: {e}"

def httppost(url, data):
    try:
        response = requests.post(url, data=data)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def httpget(url):
    import requests
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        return f"HTTP GET Error: {e}"

def starthttpserver(port=8000):
    def serverthread():
        with HTTPServer(("", port), SimpleHTTPRequestHandler) as httpd:
            print(f"Serving on port {port}...")
            httpd.serve_forever()

    thread = threading.Thread(target=serverthread)
    thread.daemon = True
    thread.start()

def starthttpsserver(port=8443, certfile="cert.pem", keyfile="key.pem"):
    def serverthread():
        httpd = HTTPServer(("", port), SimpleHTTPRequestHandler)
        httpd.socket = ssl.wrap_socket(httpd.socket,
                                       certfile=certfile,
                                       keyfile=keyfile,
                                       server_side=True)
        print(f"Serving HTTPS on port {port}...")
        httpd.serve_forever()

    thread = threading.Thread(target=server_thread)
    thread.daemon = True
    thread.start()

