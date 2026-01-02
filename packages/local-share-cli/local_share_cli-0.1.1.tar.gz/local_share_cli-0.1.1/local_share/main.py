import http.server
import socketserver
import socket
from operator import index

import qrcode
import sys
import os
import tkinter as tk
from tkinter import filedialog

PORT = 8000
httpd = None

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def main():
    try:
        root = tk.Tk()
        root.withdraw()

        path = filedialog.askopenfilename()
        if not path:
            print("No file selected. Exiting.")
            sys.exit(1)

        abs_path = os.path.abspath(path)
        directory = os.path.dirname(abs_path)
        filename = os.path.basename(abs_path)

        with open("template.html", "r") as f:
            template = f.read()

        html = template.replace("{{FILENAME}}", filename)

        os.chdir(directory)

        with open("index.html", "w") as f:
            f.write(html)


        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(("", PORT), handler)

        ip = get_local_ip()
        url = f"http://{ip}:{PORT}/"

        print(f"\nSharing: {path}")
        print(f"URL: {url}\n")

        qr = qrcode.QRCode()
        qr.add_data(url)

        img = qrcode.make(url)
        img.save("share.png")


        path_of_qr_code = "share.png"

        if sys.platform.startswith("linux"):
            os.system(f"xdg-open {path_of_qr_code}")
        elif sys.platform == "darwin":
            os.system(f"open {path_of_qr_code}")
        elif sys.platform == "win32":
            os.startfile(path_of_qr_code)

        print("\nPress Ctrl+C to stop.\n")
        print("READY...")
        httpd.serve_forever()

    except KeyboardInterrupt:
        print("Bye Bye :)")

    finally:
        path_of_qr_code = os.path.abspath("share.png")
        os.remove("index.html")
        if os.path.exists(path_of_qr_code):
            os.remove(path_of_qr_code)
        if httpd:
            httpd.shutdown()
            httpd.server_close()

if __name__ == "__main__":
    main()