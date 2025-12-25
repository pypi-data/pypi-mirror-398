import os
import sys
import http.server
import socketserver
import subprocess
import re
from email.message import EmailMessage
from urllib.parse import unquote, parse_qs, urlparse

# --- Configuration ---
PORT = 3001
TEXT_EXTENSIONS = {'.txt', '.py', '.html', '.css', '.js', '.json', '.md', '.sh', '.csv', '.xml', '.yaml', '.yml'}
EDIT_ENABLED = True
UPLOAD_ENABLED = True
DELETE_ENABLED = True
BASE_DIR = os.getcwd()

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
  updogfx disable upload -p 9000
"""

# --- HTML Interface ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPDOGFX2 - {current_path}</title>
    <style>
        :root {{ --primary: #4361ee; --danger: #ef233c; --bg: #f8f9fa; --card: #ffffff; --text: #2b2d42; --edit: #f7b731; --folder: #ffd166; }}
        body {{ font-family: sans-serif; margin: 0; padding: 20px; background: var(--bg); color: var(--text); }}
        .container {{ max-width: 900px; margin: auto; }}
        .card {{ background: var(--card); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .file-item {{ background: var(--card); padding: 12px 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-left: 5px solid var(--primary); }}
        .folder-item {{ border-left-color: var(--folder); }}
        .file-info {{ flex-grow: 1; display: flex; align-items: center; gap: 10px; overflow: hidden; }}
        .file-name {{ font-weight: 600; color: var(--primary); text-decoration: none; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }}
        .breadcrumb {{ margin-bottom: 20px; font-size: 1rem; }}
        .breadcrumb a {{ color: var(--primary); text-decoration: none; font-weight: bold; }}
        .actions {{ display: flex; gap: 8px; }}
        .btn {{ padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; border: none; cursor: pointer; color: white; }}
        .btn-upload {{ background: var(--primary); width: 100%; margin-top: 10px; }}
        .btn-del {{ background: var(--danger); }}
        .btn-edit {{ background: var(--edit); color: #000; }}
        .editor-container {{ display: {editor_display}; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        textarea {{ width: 100%; height: 550px; font-family: 'Courier New', monospace; margin-top: 10px; padding: 15px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; line-height: 1.5; }}
        .badge {{ font-size: 0.7rem; background: #e2e2e2; padding: 4px 10px; border-radius: 10px; margin-left: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="editor-container">
            <h3>Editing: {editing_filename}</h3>
            <form method="POST">
                <input type="hidden" name="action" value="save_edit">
                <input type="hidden" name="filepath" value="{editing_filepath}">
                <textarea name="content">{file_content}</textarea><br>
                <div style="margin-top: 15px;">
                    <button type="submit" class="btn" style="background: #2ecc71; font-weight:bold;">SAVE CHANGES</button>
                    <a href="." class="btn" style="background: #95a5a6;">CANCEL</a>
                </div>
            </form>
        </div>
        <div style="display: {main_display}">
            <header><h1>📁 UPDOGFX2 EFXTv {readonly_badge}</h1></header>
            <div class="breadcrumb">{breadcrumb_html}</div>
            {upload_html}
            <div class="file-list">{file_rows}</div>
        </div>
    </div>
</body>
</html>
"""

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return

    def get_safe_path(self, url_path):
        """Resolves URL path to local absolute path while preventing traversal"""
        clean_path = unquote(url_path).split('?')[0].lstrip('/')
        full_path = os.path.abspath(os.path.join(BASE_DIR, clean_path))
        if not full_path.startswith(BASE_DIR):
            return BASE_DIR
        return full_path

    def do_GET(self):
        full_path = self.get_safe_path(self.path)
        query = parse_qs(urlparse(self.path).query)
        
        # --- Handle Delete ---
        if 'delete' in query and DELETE_ENABLED:
            target = self.get_safe_path(query['delete'][0])
            if os.path.exists(target) and target != BASE_DIR:
                if os.path.isdir(target): import shutil; shutil.rmtree(target)
                else: os.remove(target)
            return self.redirect(urlparse(self.path).path)

        # --- Handle Editor ---
        editor_display, main_display, editing_filename, editing_filepath, file_content = "none", "block", "", "", ""
        if 'edit' in query and EDIT_ENABLED:
            target = self.get_safe_path(query['edit'][0])
            if os.path.isfile(target):
                editor_display, main_display = "block", "none"
                editing_filename = os.path.basename(target)
                editing_filepath = query['edit'][0]
                with open(target, 'r', errors='replace') as f: file_content = f.read()

        # --- Serve File Download ---
        if os.path.isfile(full_path) and not query:
            return super().do_GET()

        # --- Directory Listing ---
        if os.path.isdir(full_path):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Breadcrumbs
            rel_path = os.path.relpath(full_path, BASE_DIR)
            parts = rel_path.split(os.sep) if rel_path != "." else []
            bc_html = '<a href="/">Root</a>'
            curr_link = ""
            for p in parts:
                curr_link += f"/{p}"
                bc_html += f' / <a href="{curr_link}/">{p}</a>'

            # List directory content
            try:
                items = sorted(os.listdir(full_path))
            except: items = []
            
            rows = ""
            for item in items:
                if item == "__pycache__" or item.endswith(".pyc"): continue
                item_full = os.path.join(full_path, item)
                item_rel = os.path.relpath(item_full, BASE_DIR)
                is_dir = os.path.isdir(item_full)
                
                icon = "📁" if is_dir else "📄"
                row_type = "folder-item" if is_dir else ""
                href = f"/{item_rel}/" if is_dir else f"/{item_rel}"
                
                edit_btn = f'<a class="btn btn-edit" href="?edit={item_rel}">Edit</a>' if (EDIT_ENABLED and not is_dir and os.path.splitext(item)[1].lower() in TEXT_EXTENSIONS) else ""
                del_btn = f'<a class="btn btn-del" href="?delete={item_rel}" onclick="return confirm(\'Delete {item}?\')">Del</a>' if DELETE_ENABLED else ""
                
                rows += f'''<div class="file-item {row_type}">
                            <div class="file-info"><span>{icon}</span><a class="file-name" href="{href}">{item}</a></div>
                            <div class="actions">{edit_btn}{del_btn}</div>
                          </div>'''

            upload_html = f'<div class="card"><h3>Upload Here</h3><form method="POST" enctype="multipart/form-data"><input type="file" name="file" required><button type="submit" class="btn btn-upload">Upload</button></form></div>' if UPLOAD_ENABLED else ""
            readonly_badge = '<span class="badge">Read Only</span>' if not (UPLOAD_ENABLED or EDIT_ENABLED or DELETE_ENABLED) else ""

            self.wfile.write(HTML_TEMPLATE.format(
                current_path=rel_path, breadcrumb_html=bc_html, file_rows=rows, 
                upload_html=upload_html, editor_display=editor_display, main_display=main_display,
                editing_filename=editing_filename, editing_filepath=editing_filepath,
                file_content=file_content, readonly_badge=readonly_badge).encode())

    def do_POST(self):
        ctype = self.headers.get('Content-Type', '')
        if UPLOAD_ENABLED and 'multipart/form-data' in ctype:
            self.handle_upload()
        elif EDIT_ENABLED and 'application/x-www-form-urlencoded' in ctype:
            self.handle_save()
        self.redirect(self.path)

    def handle_upload(self):
        from email.parser import BytesParser
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        # Simple multipart parsing
        boundary = self.headers['Content-Type'].split("=")[1].encode()
        parts = body.split(b'--' + boundary)
        target_dir = self.get_safe_path(self.path)
        
        for part in parts:
            if b'filename="' in part:
                headers, content = part.split(b'\r\n\r\n', 1)
                filename = re.findall(b'filename="(.+?)"', headers)[0].decode()
                content = content.rsplit(b'\r\n', 1)[0]
                with open(os.path.join(target_dir, filename), 'wb') as f: f.write(content)

    def handle_save(self):
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))
        if post_data.get('action', [''])[0] == 'save_edit':
            target_file = self.get_safe_path(post_data.get('filepath', [''])[0])
            content = post_data.get('content', [''])[0]
            with open(target_file, 'w', encoding='utf-8') as f: f.write(content)

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
                    print(f"\n[+] UPDOGFX2 by EFXTv\n[+] P. URL\t: {url.group(0)}\n[+] L. URL\t: http://localhost:{port}\n")
                    break
        return process
    except FileNotFoundError:
        print(f"\n[!] cloudflared not found. Running locally at http://localhost:{port}")
        return None

def run():
    global PORT, EDIT_ENABLED, UPLOAD_ENABLED, DELETE_ENABLED
    
    # Check help command first
    if "-h" in sys.argv or "--help" in sys.argv or "-help" in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    # Parse port flag anywhere
    if "-p" in sys.argv:
        try: PORT = int(sys.argv[sys.argv.index("-p") + 1])
        except: print("[!] Port error, using 3001")

    # Parse disable commands
    ARGS = [a.lower() for a in sys.argv]
    if "disable" in ARGS:
        if "edit" in ARGS: EDIT_ENABLED = False
        if "upload" in ARGS: UPLOAD_ENABLED = False
        if not ("edit" in ARGS or "upload" in ARGS):
            EDIT_ENABLED = UPLOAD_ENABLED = DELETE_ENABLED = False

    socketserver.TCPServer.allow_reuse_address = True
    tunnel_proc = start_cloudflare_tunnel(PORT)
    try:
        with socketserver.TCPServer(("", PORT), FileHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        if tunnel_proc: tunnel_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    run()
