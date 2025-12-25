import os
import sys
import http.server
import socketserver
import subprocess
import re
from email.message import EmailMessage
from urllib.parse import unquote, parse_qs

# --- Configuration ---
PORT = 3001
TEXT_EXTENSIONS = {'.txt', '.py', '.html', '.css', '.js', '.json', '.md', '.sh', '.csv', '.xml'}
EDIT_ENABLED = True
UPLOAD_ENABLED = True
DELETE_ENABLED = True

HELP_TEXT = """
=======================
   UPDOGFX2 by EFXTv   
=======================
Usage: updogfx [options]

Options:
  disable           Disables Upload, Edit, and Delete (View Only).
  disable edit      Disables only the text editor.
  disable upload    Disables only file uploads.
  -p [port]         Set custom port (default: 3001)
  -h, --help        Show this help message and exit.

Examples:
  updogfx -p 8080
  updogfx disable -p 5000
  updogfx disable edit
"""

# --- HTML Interface ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPDOGFX2 EFXTv</title>
    <style>
        :root {{ --primary: #4361ee; --danger: #ef233c; --bg: #f8f9fa; --card: #ffffff; --text: #2b2d42; --edit: #f7b731; }}
        body {{ font-family: sans-serif; margin: 0; padding: 20px; background: var(--bg); color: var(--text); }}
        .container {{ max-width: 900px; margin: auto; }}
        .card {{ background: var(--card); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .file-item {{ background: var(--card); padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-left: 5px solid var(--primary); }}
        .file-info {{ flex-grow: 1; overflow: hidden; }}
        .file-name {{ font-weight: 600; color: var(--primary); text-decoration: none; display: block; overflow: hidden; text-overflow: ellipsis; }}
        .actions {{ display: flex; gap: 8px; }}
        .btn {{ padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; border: none; cursor: pointer; color: white; display: inline-block; }}
        .btn-upload {{ background: var(--primary); width: 100%; margin-top: 10px; }}
        .btn-del {{ background: var(--danger); }}
        .btn-edit {{ background: var(--edit); color: #000; }}
        .editor-container {{ display: {editor_display}; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        textarea {{ width: 100%; height: 450px; font-family: monospace; margin-top: 10px; padding: 10px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 8px; }}
        .badge {{ font-size: 0.7rem; background: #e2e2e2; padding: 2px 8px; border-radius: 10px; margin-left: 10px; vertical-align: middle; }}
    </style>
</head>
<body>
    <div class="container">
        <div id="editorSection" class="editor-container">
            <h3>Editing: {editing_filename}</h3>
            <form method="POST">
                <input type="hidden" name="action" value="save_edit">
                <input type="hidden" name="filename" value="{editing_filename}">
                <textarea name="content">{file_content}</textarea><br>
                <div style="margin-top: 10px;">
                    <button type="submit" class="btn" style="background: #2ecc71;">Save Changes</button>
                    <a href="/" class="btn" style="background: #95a5a6;">Cancel</a>
                </div>
            </form>
        </div>
        <div style="display: {main_display}">
            <header><h1>📁 UPDOGFX2 EFXTv {readonly_badge}</h1></header>
            {upload_html}
            <div class="file-list">{file_rows}</div>
        </div>
    </div>
</body>
</html>
"""

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return

    def do_GET(self):
        decoded_path = unquote(self.path)
        if decoded_path.startswith('/delete/'):
            if DELETE_ENABLED:
                filename = os.path.basename(decoded_path[8:])
                if os.path.exists(filename): os.remove(filename)
            return self.redirect('/')
        
        editing_filename, file_content, editor_display, main_display = "", "", "none", "block"
        if EDIT_ENABLED and decoded_path.startswith('/edit/'):
            editing_filename = os.path.basename(decoded_path[6:])
            if os.path.exists(editing_filename):
                editor_display, main_display = "block", "none"
                with open(editing_filename, 'r', errors='replace') as f: file_content = f.read()

        files = sorted([f for f in os.listdir('.') if os.path.isfile(f) and f != 'main.py'])
        rows = ""
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            edit_btn = f'<a class="btn btn-edit" href="/edit/{f}">Edit</a>' if (EDIT_ENABLED and ext in TEXT_EXTENSIONS) else ""
            del_btn = f'<a class="btn btn-del" href="/delete/{f}">Delete</a>' if DELETE_ENABLED else ""
            rows += f'''<div class="file-item"><div class="file-info"><a class="file-name" href="/{f}" download>{f}</a></div>
                        <div class="actions">{edit_btn}{del_btn}</div></div>'''

        upload_html = f'<div class="card"><h3>Upload</h3><form method="POST" enctype="multipart/form-data"><input type="file" name="file" required><button type="submit" class="btn btn-upload">Upload</button></form></div>' if UPLOAD_ENABLED else ""
        readonly_badge = '<span class="badge">Read Only</span>' if not (UPLOAD_ENABLED or EDIT_ENABLED or DELETE_ENABLED) else ""

        if self.path != '/' and os.path.isfile(decoded_path.lstrip('/')) and not decoded_path.startswith(('/edit/', '/delete/')):
            return super().do_GET()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.format(file_rows=rows, upload_html=upload_html, editor_display=editor_display, 
                                             main_display=main_display, editing_filename=editing_filename, 
                                             file_content=file_content, readonly_badge=readonly_badge).encode())

    def do_POST(self):
        ctype = self.headers.get('Content-Type', '')
        if UPLOAD_ENABLED and 'multipart/form-data' in ctype:
            self.handle_upload()
        elif EDIT_ENABLED and 'application/x-www-form-urlencoded' in ctype:
            self.handle_save()
        self.redirect('/')

    def handle_upload(self):
        msg = EmailMessage()
        msg['Content-Type'] = self.headers['Content-Type']
        boundary = msg.get_boundary().encode()
        body = self.rfile.read(int(self.headers['Content-Length']))
        parts = body.split(b'--' + boundary)
        for part in parts:
            if b'filename="' in part:
                head, content = part.split(b'\r\n\r\n', 1)
                filename = head.split(b'filename="')[1].split(b'"')[0].decode()
                content = content.rsplit(b'\r\n', 1)[0]
                with open(os.path.basename(filename), 'wb') as f: f.write(content)

    def handle_save(self):
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))
        if post_data.get('action', [''])[0] == 'save_edit':
            filename = os.path.basename(post_data.get('filename', [''])[0])
            content = post_data.get('content', [''])[0]
            with open(filename, 'w') as f: f.write(content)

    def redirect(self, path):
        self.send_response(303); self.send_header('Location', path); self.end_headers()

def start_cloudflare_tunnel(port):
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        for line in iter(process.stderr.readline, ""):
            if "trycloudflare.com" in line:
                url = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if url:
                    print(f"\n[+] UPDOGFX2 by EFXTv")
                    print(f"[+] P. URL\t: {url.group(0)}")
                    print(f"[+] L. URL\t: http://localhost:{port}\n")
                    break
        return process
    except FileNotFoundError:
        print(f"\n[!] cloudflared not found. Running locally at http://localhost:{port}")
        return None

def run():
    global PORT, EDIT_ENABLED, UPLOAD_ENABLED, DELETE_ENABLED
    
    # 1. Help Check
    if "-h" in sys.argv or "--help" in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    # 2. Port Parsing (handles -p port anywhere)
    if "-p" in sys.argv:
        try:
            p_idx = sys.argv.index("-p")
            PORT = int(sys.argv[p_idx + 1])
        except (ValueError, IndexError):
            print("[!] Invalid port number. Using default 3001.")

    # 3. Disable Logic Parsing
    ARGS = [a.lower() for a in sys.argv]
    if "disable" in ARGS:
        if "edit" in ARGS:
            EDIT_ENABLED = False
            print("[*] Editor Disabled")
        if "upload" in ARGS:
            UPLOAD_ENABLED = False
            print("[*] Uploads Disabled")
        if not ("edit" in ARGS or "upload" in ARGS):
            EDIT_ENABLED = UPLOAD_ENABLED = DELETE_ENABLED = False
            print("[*] Read-Only Mode (All actions disabled)")

    # 4. Start Tunnel and Server
    socketserver.TCPServer.allow_reuse_address = True
    tunnel_proc = start_cloudflare_tunnel(PORT)
    
    try:
        with socketserver.TCPServer(("", PORT), FileHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        if tunnel_proc:
            tunnel_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    run()
