from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import urllib.error
import traceback


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        query = params.get("q", [""])[0].strip()
        limit = int(params.get("limit", ["12"])[0])

        if not query:
            self._json(
                {"error": "Missing query parameter ?q="},
                400
            )
            return

        try:
            recipes = self._search_jow(query, limit)

            self._json({
                "query": query,
                "recipes": recipes
            })

        except Exception as e:
            self._json({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, 500)

    def _search_jow(self, query, limit):

        search_url = "https://api.jow.fr/public/recipe/quicksearch"

        params = urllib.parse.urlencode({
            "query": query,
            "limit": limit,
            "start": 0,
            "availabilityZoneId": "FR"
        })

        req_post = urllib.request.Request(
            f"{search_url}?{params}",
            data=b"{}",
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-jow-withmeta": "1",
                "Origin": "https://jow.fr",
                "Referer": "https://jow.fr/",
                "User-Agent": "Mozilla/5.0"
            }
        )

        try:
            with urllib.request.urlopen(req_post, timeout=15) as resp:
                raw = json.loads(
                    resp.read().decode("utf-8")
                )

        except urllib.error.HTTPError as e:
            body = ""

            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass

            raise Exception(
                f"Jow POST failed ({e.code}) : {body}"
            )

        # DEBUG TEMPORAIRE
        raise Exception(
            json.dumps(raw, ensure_ascii=False)[:3000]
        )

        data = raw.get("data", [])

        if isinstance(data, list):
            recipes = data
        elif isinstance(data, dict):
            recipes = (
                data.get("recipes")
                or data.get("items")
                or data.get("results")
                or []
            )
        else:
            recipes = []

        result = []

        for recipe in recipes:

            if not isinstance(recipe, dict):
                continue

            result.append({
                "id": recipe.get("_id", ""),
                "name": recipe.get("title", ""),
                "description": recipe.get("description", ""),
                "slug": recipe.get("slug", "")
            })

        return result

    def _json(self, data, code=200):
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(code)
        self._cors()

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

    def log_message(self, *args):
        pass
