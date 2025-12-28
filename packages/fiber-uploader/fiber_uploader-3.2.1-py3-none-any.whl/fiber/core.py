import os
import sys
import glob
import time
import hashlib
import mimetypes
import configparser
import getpass
import datetime
import zipfile
import tarfile
from email import message_from_bytes
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4

PYPI_UPLOAD_URL = "https://upload.pypi.org/legacy/"
CONFIG_PATH = os.path.expanduser("~/.pypirc")

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg, type="info"):
    if type == "info":
        print(f"{Colors.OKBLUE}[Fiber]{Colors.ENDC} {msg}")
    elif type == "success":
        print(f"{Colors.OKGREEN}[Fiber]{Colors.ENDC} {msg}")
    elif type == "warn":
        print(f"{Colors.WARNING}[Warn]{Colors.ENDC} {msg}")
    elif type == "error":
        print(f"{Colors.FAIL}[Error]{Colors.ENDC} {msg}")

class ProjectValidator:
    @staticmethod
    def validate():
        if not (os.path.exists("setup.py") or os.path.exists("pyproject.toml")):
            return
        ProjectValidator._check_readme()
        ProjectValidator._check_license()

    @staticmethod
    def _check_readme():
        filename = "README.md"
        if not os.path.exists(filename) or os.stat(filename).st_size == 0:
            log(f"{filename} kosong. Membuat default...", "warn")
            name = os.path.basename(os.getcwd()).capitalize()
            content = f"# {name}\n\nUploaded via **Fiber**.\n\n## Author\n**Eternals**"
            with open(filename, "w") as f:
                f.write(content)
            log(f"{filename} dibuat.", "success")

    @staticmethod
    def _check_license():
        if glob.glob("LICENSE*") or glob.glob("COPYING*"):
            return
        log("File LICENSE tidak ditemukan!", "warn")
        print(f"{Colors.BOLD}Pilih Lisensi:{Colors.ENDC}\n1. MIT\n2. Apache 2.0\n3. Skip")
        try:
            c = input(f"{Colors.OKCYAN}Pilihan: {Colors.ENDC}")
        except: return
        
        y, h = datetime.datetime.now().year, "Eternals"
        content = ""
        if c == '1':
            content = f"MIT License\n\nCopyright (c) {y} {h}\n\nPermission is hereby granted, free of charge..."
        elif c == '2':
            content = f"Apache License 2.0\nCopyright {y} {h}\n..."
        
        if content:
            with open("LICENSE", "w") as f: f.write(content)
            log(f"LICENSE ({h}) dibuat.", "success")

class AuthManager:
    def get_token(self):
        cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            cfg.read(CONFIG_PATH)
            if "pypi" in cfg and "password" in cfg["pypi"]:
                return cfg["pypi"]["password"]
        
        log("Token PyPI tidak ditemukan.", "warn")
        t = getpass.getpass(f"{Colors.OKCYAN}Token (pypi-xxxx): {Colors.ENDC}").strip()
        if not t: sys.exit(1)
        if input("Simpan? (y/n): ").lower() == 'y':
            cfg["distutils"] = {"index-servers": "pypi"}
            cfg["pypi"] = {"username": "__token__", "password": t}
            with open(CONFIG_PATH, 'w') as f: cfg.write(f)
            log("Token disimpan.", "success")
        return t

class MetaParser:
    @staticmethod
    def parse(filepath):
        try:
            if filepath.endswith('.whl'):
                with zipfile.ZipFile(filepath, 'r') as z:
                    for n in z.namelist():
                        if n.endswith('.dist-info/METADATA'):
                            return MetaParser._parse(z.read(n))
            elif filepath.endswith('.tar.gz'):
                with tarfile.open(filepath, 'r:gz') as t:
                    for m in t.getmembers():
                        if m.name.endswith('/PKG-INFO'):
                            f = t.extractfile(m)
                            if f: return MetaParser._parse(f.read())
        except: pass
        return {}

    @staticmethod
    def _parse(data):
        msg = message_from_bytes(data)
        return {
            'name': msg.get('Name'),
            'version': msg.get('Version'),
            'summary': msg.get('Summary'),
            'description': msg.get_payload(),
            # FIX: Key harus 'description_content_type' agar PyPI render Markdown
            'description_content_type': msg.get('Description-Content-Type') 
        }

class PackageFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.filetype = 'bdist_wheel' if self.filename.endswith('.whl') else 'sdist'
        
        self.metadata = MetaParser.parse(filepath)
        
        # FALLBACK 1: Filename Parsing
        if not self.metadata.get('name'):
            p = self.filename.replace('.tar.gz','').replace('.whl','').split('-')
            self.metadata['name'] = p[0]
            self.metadata['version'] = p[1] if len(p)>1 else '0.0.0'

        # FALLBACK 2: Force Read Local README (Final Solution)
        if not self.metadata.get('description'):
            for f in ['README.md', 'README.txt', 'README']:
                if os.path.exists(f):
                    with open(f, 'r', encoding='utf-8') as rf:
                        self.metadata['description'] = rf.read()
                        # FIX: Set content type correct key
                        self.metadata['description_content_type'] = 'text/markdown' if f.endswith('.md') else 'text/plain'
                    break

    def get_hash(self):
        h = hashlib.sha256()
        with open(self.filepath, 'rb') as f:
            while True:
                d = f.read(65536)
                if not d: break
                h.update(d)
        return h.hexdigest()

class Uploader:
    def __init__(self, token):
        self.token = token
        self.boundary = uuid4().hex

    def upload(self, pkg):
        log(f"Memproses: {Colors.BOLD}{pkg.filename}{Colors.ENDC}")
        fields = {
            ":action": "file_upload",
            "protocol_version": "1",
            "metadata_version": "2.1",
            "filetype": pkg.filetype,
            "pyversion": "source" if pkg.filetype == 'sdist' else "py3",
            "sha256_digest": pkg.get_hash(),
        }
        
        # Merge metadata (termasuk description & description_content_type)
        meta = {k: v for k, v in pkg.metadata.items() if v is not None}
        fields.update(meta)

        # Build Multipart Body
        body = []
        for k, v in fields.items():
            body.extend([
                f'--{self.boundary}'.encode(),
                f'Content-Disposition: form-data; name="{k}"'.encode(),
                b'', str(v).encode('utf-8')
            ])
        
        mime = mimetypes.guess_type(pkg.filename)[0] or 'application/octet-stream'
        body.extend([
            f'--{self.boundary}'.encode(),
            f'Content-Disposition: form-data; name="content"; filename="{pkg.filename}"'.encode(),
            f'Content-Type: {mime}'.encode(),
            b''
        ])
        
        with open(pkg.filepath, 'rb') as f: body.append(f.read())
        body.extend([f'--{self.boundary}--'.encode(), b''])
        
        data = b'\r\n'.join(body)
        req = Request(PYPI_UPLOAD_URL, data=data, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={self.boundary}")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("User-Agent", "Fiber/1.2.2") # Versi Baru

        try:
            log(f"Mengunggah ({len(data)/1024:.1f} KB)...")
            with urlopen(req) as res:
                if res.status == 200:
                    log("Berhasil!", "success")
                    log(f"Link: https://pypi.org/project/{meta.get('name')}/{meta.get('version')}/")
        except HTTPError as e:
            log(f"Gagal: {e.code} - {e.read().decode()}", "error")
        except URLError as e:
            log(f"Koneksi error: {e.reason}", "error")

def main():
    print(f"\n{Colors.OKCYAN}Fiber v1.2.2{Colors.ENDC} - Zero Dependency Uploader")
    if len(sys.argv) < 2: sys.exit("Usage: fiber dist/*")
    
    ProjectValidator.validate()
    files = glob.glob(sys.argv[1]) if len(sys.argv) > 1 else []
    
    if not files: sys.exit(log("File tidak ditemukan.", "error"))
    
    token = AuthManager().get_token()
    uploader = Uploader(token)
    
    for f in files:
        if os.path.isfile(f):
            try: uploader.upload(PackageFile(f))
            except Exception as e: log(f"Error {f}: {e}", "error")

if __name__ == "__main__": main()

