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

    def _extract_steps(self, recipe):

        fields_found = []
        steps = []

        candidate_fields = [
            "steps",
            "preparationSteps",
            "recipeSteps",
            "instructions",
            "directions",
            "method"
        ]

        for field in candidate_fields:

            value = recipe.get(field)

            if isinstance(value, list):

                fields_found.append(field)

                for item in value:

                    if isinstance(item, dict):

                        text = (
                            item.get("label")
                            or item.get("description")
                            or item.get("text")
                            or item.get("title")
                        )

                        if text:
                            steps.append(text)

                    elif isinstance(item, str):
                        steps.append(item)

                if steps:
                    break

        return steps, fields_found

    def _search_jow(self, query, limit=12):

        search_url = "https://api.jow.fr/public/recipe/quicksearch"

        params = urllib.parse.urlencode({
            "query": query,
            "limit": limit,
            "start": 0,
            "availabilityZoneId": "FR"
        })

        req = urllib.request.Request(
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

        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(
                resp.read().decode("utf-8")
            )

        data = raw.get("data", {})
        recipes = data.get("content", [])recipes = data.get("content", [])

if recipes:
    raise Exception(
        json.dumps(
            recipes[0],
            ensure_ascii=False
        )[:30000]
    )

        STATIC = "https://static.jow.fr/"

        result = []

        for recipe in recipes:

            if not isinstance(recipe, dict):
                continue

            def parse_ingr(c):

                ingredient = c.get("ingredient", {})

                return {
                    "name": ingredient.get("name", ""),
                    "qty": str(
                        ingredient.get(
                            "quantityPerCover",
                            ""
                        )
                    ),
                    "unit": "",
                    "isOptional": c.get(
                        "isOptional",
                        False
                    )
                }

            image_url = (
                recipe.get("editorialPictureUrl")
                or recipe.get("imageUrl")
            )

            video_url = recipe.get("videoUrl")

            steps, step_fields = self._extract_steps(recipe)

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

                "slug": recipe.get(
                    "slug",
                    ""
                ),

                "url": (
                    "https://jow.fr/recettes/"
                    + recipe.get("slug", "")
                ),

                "prepTime": recipe.get(
                    "preparationTime",
                    0
                ),

                "cookTime": recipe.get(
                    "cookingTime",
                    0
                ),

                "totalTime": (
                    (recipe.get(
                        "preparationTime"
                    ) or 0)
                    +
                    (recipe.get(
                        "cookingTime"
                    ) or 0)
                ),

                "steps": steps,

                "debugStepFields": step_fields,

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
