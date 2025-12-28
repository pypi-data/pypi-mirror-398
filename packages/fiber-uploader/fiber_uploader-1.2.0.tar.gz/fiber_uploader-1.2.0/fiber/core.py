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

# --- Constants ---
PYPI_UPLOAD_URL = "https://upload.pypi.org/legacy/"
CONFIG_PATH = os.path.expanduser("~/.pypirc")

# --- Colors ---
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

# --- Project Validator ---
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
            log(f"{filename} kosong atau tidak ditemukan. Membuat default...", "warn")
            project_name = os.path.basename(os.getcwd()).capitalize()
            content = f"# {project_name}\n\nUploaded via **Fiber**.\n\n## Author\n**Eternals**"
            with open(filename, "w") as f:
                f.write(content)
            log(f"{filename} berhasil dibuat.", "success")

    @staticmethod
    def _check_license():
        license_files = glob.glob("LICENSE*") + glob.glob("COPYING*")
        if license_files:
            return

        log("File LICENSE tidak ditemukan!", "warn")
        print(f"{Colors.BOLD}Pilih Lisensi:{Colors.ENDC}")
        print("1. MIT (Recommended)\n2. Apache 2.0\n3. Skip")
        
        try:
            choice = input(f"{Colors.OKCYAN}Pilihan [1-3]: {Colors.ENDC}")
        except KeyboardInterrupt:
            return

        year = datetime.datetime.now().year
        holder = "Eternals"
        content = ""
        
        if choice == '1':
            content = f"MIT License\n\nCopyright (c) {year} {holder}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE."
        elif choice == '2':
            content = f"Apache License 2.0\nCopyright {year} {holder}\n\nLicensed under the Apache License, Version 2.0 (the \"License\");\nyou may not use this file except in compliance with the License.\nYou may obtain a copy of the License at\n\n    http://www.apache.org/licenses/LICENSE-2.0\n\nUnless required by applicable law or agreed to in writing, software\ndistributed under the License is distributed on an \"AS IS\" BASIS,\nWITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\nSee the License for the specific language governing permissions and\nlimitations under the License."

        if content:
            with open("LICENSE", "w") as f:
                f.write(content)
            log(f"LICENSE ({holder}) berhasil dibuat.", "success")

# --- Auth Handler ---
class AuthManager:
    def get_token(self):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
            if "pypi" in config and "password" in config["pypi"]:
                return config["pypi"]["password"]
        
        print(f"\n{Colors.BOLD}Konfigurasi Fiber (Pertama Kali){Colors.ENDC}")
        log("Token PyPI tidak ditemukan di ~/.pypirc", "warn")
        token = getpass.getpass(f"{Colors.OKCYAN}Token (pypi-xxxx): {Colors.ENDC}").strip()
        
        if not token:
            sys.exit(1)

        save = input(f"Simpan token? (y/n): ").lower()
        if save == 'y':
            self.save_token(token)
        return token

    def save_token(self, token):
        config = configparser.ConfigParser()
        config["distutils"] = {"index-servers": "pypi"}
        config["pypi"] = {"username": "__token__", "password": token}
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)
        log(f"Token disimpan.", "success")

# --- Metadata Extractor ---
class MetaParser:
    @staticmethod
    def parse(filepath):
        meta = {}
        try:
            if filepath.endswith('.whl'):
                with zipfile.ZipFile(filepath, 'r') as z:
                    for name in z.namelist():
                        if name.endswith('.dist-info/METADATA'):
                            data = z.read(name)
                            return MetaParser._parse_email_format(data)
            elif filepath.endswith('.tar.gz'):
                with tarfile.open(filepath, 'r:gz') as t:
                    for member in t.getmembers():
                        if member.name.endswith('/PKG-INFO'):
                            f = t.extractfile(member)
                            if f:
                                data = f.read()
                                return MetaParser._parse_email_format(data)
        except Exception as e:
            log(f"Gagal baca metadata dari {filepath}: {e}", "warn")
        return meta

    @staticmethod
    def _parse_email_format(data):
        msg = message_from_bytes(data)
        meta = {
            'name': msg.get('Name'),
            'version': msg.get('Version'),
            'summary': msg.get('Summary'),
            'author': msg.get('Author'),
            'license': msg.get('License'),
            'home_page': msg.get('Home-page'),
            'description': msg.get_payload(),
            'content_type': msg.get('Description-Content-Type')
        }
        return {k: v for k, v in meta.items() if v}

# --- Package Parser ---
class PackageFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        
        if self.filename.endswith('.whl'):
            self.filetype = 'bdist_wheel'
        elif self.filename.endswith('.tar.gz'):
            self.filetype = 'sdist'
        else:
            self.filetype = 'unknown'

        self.metadata = MetaParser.parse(filepath)
        
        if not self.metadata.get('name'):
            parts = self.filename.replace('.tar.gz', '').replace('.whl', '').split('-')
            self.metadata['name'] = parts[0]
            self.metadata['version'] = parts[1] if len(parts) > 1 else '0.0.0'

    def get_hash(self):
        sha256 = hashlib.sha256()
        with open(self.filepath, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data: break
                sha256.update(data)
        return sha256.hexdigest()

# --- Uploader Logic ---
class Uploader:
    def __init__(self, token):
        self.token = token
        self.boundary = uuid4().hex

    def _build_multipart_body(self, fields, file_obj):
        body = []
        for key, value in fields.items():
            if value is None: continue
            body.append(f'--{self.boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="{key}"'.encode())
            body.append(b'')
            body.append(str(value).encode('utf-8'))

        mime_type = mimetypes.guess_type(file_obj.filename)[0] or 'application/octet-stream'
        body.append(f'--{self.boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="content"; filename="{file_obj.filename}"'.encode())
        body.append(f'Content-Type: {mime_type}'.encode())
        body.append(b'')
        
        with open(file_obj.filepath, 'rb') as f:
            body.append(f.read())

        body.append(f'--{self.boundary}--'.encode())
        body.append(b'')
        return b'\r\n'.join(body)

    def upload(self, package):
        log(f"Memproses: {Colors.BOLD}{package.filename}{Colors.ENDC}")
        sha256 = package.get_hash()
        
        fields = {
            ":action": "file_upload",
            "protocol_version": "1",
            "metadata_version": "2.1",
            "filetype": package.filetype,
            "pyversion": "source" if package.filetype == 'sdist' else "py3",
            "sha256_digest": sha256,
        }
        
        fields.update(package.metadata)

        data = self._build_multipart_body(fields, package)
        req = Request(PYPI_UPLOAD_URL, data=data, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={self.boundary}")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("User-Agent", "Fiber/1.2 (Termux-Optimized)")

        try:
            log(f"Mengunggah {package.filename} ({len(data)/1024:.1f} KB)...", "info")
            start_time = time.time()
            with urlopen(req) as response:
                if response.status == 200:
                    elapsed = time.time() - start_time
                    log(f"Berhasil! ({elapsed:.2f}s)", "success")
                    log(f"Link: https://pypi.org/project/{package.metadata.get('name')}/{package.metadata.get('version')}/")
        except HTTPError as e:
            error_body = e.read().decode()
            log(f"Gagal: HTTP {e.code}", "error")
            print(f"{Colors.FAIL}{error_body}{Colors.ENDC}")
        except URLError as e:
            log(f"Koneksi error: {e.reason}", "error")

def main():
    print(f"""
{Colors.OKCYAN}   ___{Colors.ENDC}
{Colors.OKCYAN}  / _/ib{Colors.ENDC}{Colors.BOLD}er{Colors.ENDC}
{Colors.OKCYAN} / _/   {Colors.ENDC}  Lightweight PyPI Uploader
{Colors.OKCYAN}/_/     {Colors.ENDC}  v1.2.0 (Smart Metadata)
    """)
    
    if len(sys.argv) < 2:
        print("Usage: fiber dist/*")
        sys.exit(1)
    
    ProjectValidator.validate()

    files = []
    for arg in sys.argv[1:]:
        files.extend(glob.glob(arg))
    
    if not files:
        log("File tidak ditemukan.", "error")
        sys.exit(1)

    auth = AuthManager()
    token = auth.get_token()
    uploader = Uploader(token)
    
    print("-" * 40)
    for f in files:
        if not os.path.isfile(f): continue
        try:
            pkg = PackageFile(f)
            if pkg.filetype == 'unknown': continue
            uploader.upload(pkg)
        except Exception as e:
            log(f"Error pada {f}: {e}", "error")
            import traceback
            traceback.print_exc()
    print("-" * 40)

