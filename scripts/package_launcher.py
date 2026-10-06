#!/usr/bin/env python3
"""Run a packaged immutable playable build on a fresh loopback port."""
import argparse,hashlib,http.server,json,pathlib,sys,urllib.parse,webbrowser
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--no-open',action='store_true',help='Serve and print the URL without opening a browser')
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parent/'runtime'
metadata=json.loads((root/'build.json').read_text())
manifest=json.loads((root/'integrity.json').read_text())['files']
actual={}
for p in root.rglob('*'):
    if p.is_symlink():sys.exit('Refusing build containing symlinks')
    # Finder creates these when users browse an extracted folder. Ignore only
    # unmanifested Finder metadata; manifested files retain checksum protection.
    if p.name=='.DS_Store' and p.relative_to(root).as_posix() not in manifest:continue
    if p.is_file() and p!=root/'integrity.json':actual[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
if actual!=manifest:
    missing=sorted(manifest.keys()-actual.keys())
    added=sorted(actual.keys()-manifest.keys())
    changed=sorted(k for k in manifest.keys()&actual.keys() if manifest[k]!=actual[k])
    sys.exit('Build integrity failed: package contents changed\n'+ '\n'.join(f'{label}: {", ".join(names)}' for label,names in [('Missing',missing),('Unexpected',added),('Changed',changed)] if names))
class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript','.mjs':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path)
        if parsed.path=='/__build':
            b=json.dumps({**metadata,'port':self.server.server_port}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if parsed.path in ('/','/index.html') and urllib.parse.parse_qs(parsed.query).get('build',[None])[0]!=metadata['buildId']:
            self.send_error(409,'Open the exact launcher URL');return
        super().do_GET()
    def list_directory(self,path):self.send_error(403);return None
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**kw:Handler(*a,directory=str(root),**kw))
url=f'http://127.0.0.1:{server.server_port}/?build={metadata["buildId"]}'
print(url,flush=True)
if not args.no_open: webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
