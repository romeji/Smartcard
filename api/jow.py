# api/jow.py

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
                "traceback": traceback.format_exc(),
                "recipes": []
            }, 500)

    def _search_jow(self, query, limit=12):

        search_url = "https://api.jow.fr/public/recipe/quicksearch"

        params = urllib.parse.urlencode({
            "query": query,
            "limit": limit,
            "start": 0,
            "availabilityZoneId": "FR"
        })

        # OPTIONS preflight
        try:
            req_opt = urllib.request.Request(
                f"{search_url}?{params}",
                method="OPTIONS",
                headers={
                    "Accept": "*/*",
                    "Origin": "https://jow.fr",
                    "Referer": "https://jow.fr/",
                    "User-Agent": "Mozilla/5.0",
                    "Access-Control-Request-Headers":
                        "content-type,x-jow-withmeta",
                    "Access-Control-Request-Method": "POST"
                }
            )

            urllib.request.urlopen(req_opt, timeout=8)

        except urllib.error.HTTPError as e:
            if e.code not in (200, 204):
                raise Exception(
                    f"Jow OPTIONS failed ({e.code})"
                )

        # POST search
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
    with urllib.request.urlopen(req_post, timeout=10) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    # DEBUG TEMPORAIRE
    raise Exception(
        json.dumps(raw, ensure_ascii=False)[:3000]
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
            body = ""

            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass

            raise Exception(
                f"Jow POST failed ({e.code}) : {body}"
            )

        recipes = raw.get("data", [])

        STATIC = "https://static.jow.fr/"

        result = []

        for recipe in recipes:

            def parse_ingr(c):

                ingredient = c.get("ingredient", {})

                unit_id = (
                    c.get("unit", {}).get("_id", "")
                    or c.get("unit", {}).get("id", "")
                )

                unit_name = ""

                natural_unit = ingredient.get(
                    "naturalUnit",
                    {}
                )

                if (
                    natural_unit.get("_id") == unit_id
                    or natural_unit.get("id") == unit_id
                ):
                    unit_name = natural_unit.get("name", "")

                else:
                    for alt in ingredient.get(
                        "alternativeUnits",
                        []
                    ):
                        au = alt.get("unit", {})

                        if (
                            au.get("_id") == unit_id
                            or au.get("id") == unit_id
                        ):
                            unit_name = au.get("name", "")
                            break

                qty_per_cover = (
                    ingredient.get("quantityPerCover")
                    or c.get("quantityPerCover")
                    or 0
                )

                covers = (
                    recipe.get("roundedCoversCount")
                    or recipe.get("coversCount")
                    or 4
                )

                qty = (
                    round(qty_per_cover * covers, 2)
                    if qty_per_cover
                    else 0
                )

                return {
                    "name": ingredient.get("name", ""),
                    "qty": str(qty) if qty else "",
                    "unit": unit_name,
                    "isOptional": c.get(
                        "isOptional",
                        False
                    )
                }

            image_url = recipe.get("imageUrl")
            video_url = recipe.get("videoUrl")

            covers = (
                recipe.get("roundedCoversCount")
                or recipe.get("coversCount")
                or 4
            )

            result.append({
                "id": recipe.get("_id", ""),
                "name": recipe.get("title", ""),
                "description": recipe.get(
                    "description",
                    ""
                ),
                "imageUrl": (
                    STATIC + image_url
                    if image_url
                    else None
                ),
                "videoUrl": (
                    STATIC + video_url
                    if video_url
                    else None
                ),
                "portions": covers,
                "prepTime": recipe.get(
                    "preparationTime",
                    0
                ),
                "cookTime": recipe.get(
                    "cookingTime",
                    0
                ),
                "totalTime": (
                    recipe.get("preparationTime", 0)
                    + recipe.get("cookingTime", 0)
                ),
                "kcalPerCover": round(
                    recipe.get(
                        "totalCaloriesPerCover"
                    ) or 0
                ),
                "protPerCover": round(
                    recipe.get(
                        "proteinsPerCover"
                    ) or 0
                ),
                "carbPerCover": round(
                    recipe.get(
                        "carbohydratesPerCover"
                    ) or 0
                ),
                "fatPerCover": round(
                    recipe.get(
                        "fatPerCover"
                    ) or 0
                ),
                "slug": recipe.get("slug", ""),
                "url": (
                    "https://jow.fr/recettes/"
                    + recipe.get("slug", "")
                ),
                "steps": [
                    s.get("description", s)
                    if isinstance(s, dict)
                    else s
                    for s in recipe.get(
                        "steps",
                        []
                    )
                ],
                "ingredients": [
                    parse_ingr(c)
                    for c in recipe.get(
                        "constituents",
                        []
                    )
                    if c.get(
                        "ingredient",
                        {}
                    ).get("name")
                ]
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
