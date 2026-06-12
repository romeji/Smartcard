# api/jow.py
from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q = query.get('q', [''])[0]
        
        if not q:
            self.send_error(400, 'Missing query')
            return
        
        # Appel direct à l'API interne Jow
        url = f'https://api.jow.fr/public/recipe/snap?query={urllib.parse.quote(q)}&maxResults=10'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
