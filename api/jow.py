# api/jow.py — Proxy Jow.fr pour SmartCard
# Nécessite: pip install jow-api requests
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self._cors()
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get('q', [''])[0].strip()
        limit = int(params.get('limit', ['12'])[0])

        if not query:
            self._json({'error': 'Missing query parameter ?q='}, 400)
            return

        try:
            results = self._search_jow(query, limit)
            self._json({'recipes': results, 'query': query})
        except Exception as e:
            self._json({'error': str(e), 'recipes': []}, 500)

    def _search_jow(self, query, limit=12):
        search_url = 'https://api.jow.fr/public/recipe/quicksearch'
        params = urllib.parse.urlencode({
            'query': query,
            'limit': limit,
            'start': 0,
            'availabilityZoneId': 'FR'
        })

        # Step 1 : OPTIONS preflight (Jow requires it)
        req_opt = urllib.request.Request(
            f'{search_url}?{params}',
            method='OPTIONS',
            headers={
                'Accept': '*/*',
                'Accept-Language': 'fr,fr-FR;q=0.9',
                'Origin': 'https://jow.fr',
                'Referer': 'https://jow.fr/',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15',
                'Access-Control-Request-Headers': 'content-type,x-jow-withmeta',
                'Access-Control-Request-Method': 'POST',
            }
        )
        try:
            urllib.request.urlopen(req_opt, timeout=8)
        except urllib.error.HTTPError as e:
            if e.code not in (200, 204):
                raise Exception(f'Jow OPTIONS failed: {e.code}')

        # Step 2 : POST search
        req_post = urllib.request.Request(
            f'{search_url}?{params}',
            data=b'{}',
            method='POST',
            headers={
                'Accept': 'application/json',
                'Accept-Language': 'fr',
                'Content-Type': 'application/json',
                'x-jow-withmeta': '1',
                'Origin': 'https://jow.fr',
                'Referer': 'https://jow.fr/',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15',
            }
        )

        with urllib.request.urlopen(req_post, timeout=10) as resp:
            raw = json.loads(resp.read())

        recipes = raw.get('data', [])

        def parse_ingr(c):
            ing = c.get('ingredient', {})
            unit_id = c.get('unit', {}).get('_id','') or c.get('unit', {}).get('id','')
            # Find unit name
            unit_name = ''
            nat = ing.get('naturalUnit', {})
            if nat.get('_id') == unit_id or nat.get('id') == unit_id:
                unit_name = nat.get('name','')
            else:
                for alt in ing.get('alternativeUnits', []):
                    au = alt.get('unit', {})
                    if au.get('_id') == unit_id or au.get('id') == unit_id:
                        unit_name = au.get('name','')
                        break

            qty_per_cover = ing.get('quantityPerCover') or c.get('quantityPerCover', 0)
            covers = r.get('roundedCoversCount') or r.get('coversCount') or 4
            qty = round(qty_per_cover * covers, 2) if qty_per_cover else 0

            return {
                'name':       ing.get('name',''),
                'qty':        str(qty) if qty else '',
                'unit':       unit_name,
                'isOptional': c.get('isOptional', False)
            }

        STATIC = 'https://static.jow.fr/'
        result = []
        for r in recipes:
            img = r.get('imageUrl')
            vid = r.get('videoUrl')
            covers = r.get('roundedCoversCount') or r.get('coversCount') or 4
            result.append({
                'id':          r.get('_id',''),
                'name':        r.get('title',''),
                'description': r.get('description',''),
                'imageUrl':    (STATIC + img) if img else None,
                'videoUrl':    (STATIC + vid) if vid else None,
                'portions':    covers,
                'prepTime':    r.get('preparationTime', 0),
                'cookTime':    r.get('cookingTime', 0),
                'totalTime':   (r.get('preparationTime',0) or 0) + (r.get('cookingTime',0) or 0),
                'kcalPerCover': round(r.get('totalCaloriesPerCover') or 0),
                'protPerCover': round(r.get('proteinsPerCover') or 0),
                'carbPerCover': round(r.get('carbohydratesPerCover') or 0),
                'fatPerCover':  round(r.get('fatPerCover') or 0),
                'slug':        r.get('slug',''),
                'url':         'https://jow.fr/recettes/' + r.get('slug',''),
                'steps':       [s.get('description', s) if isinstance(s, dict) else s
                               for s in r.get('steps', [])],
                'ingredients': [parse_ingr(c) for c in r.get('constituents', [])
                               if c.get('ingredient', {}).get('name')]
            })
        return result

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *args): pass
