from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import traceback

STATIC = "https://static.jow.fr/"


# ─────────────────────────────────────────────
# Utils
# ─────────────────────────────────────────────

def _format_qty(qty, unit_name, natural_unit_name):
    if qty is None or qty == 0:
        return "", unit_name or ""

    natural = (natural_unit_name or "").lower()

    if natural == "kilogramme":
        grams = qty * 1000
        if grams < 1000:
            return str(int(round(grams))), "g"
        return str(round(qty, 2)), "kg"

    val = int(round(qty)) if qty == int(qty) else round(qty, 1)
    return str(val), unit_name or ""


# ─────────────────────────────────────────────
# Handler
# ─────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    # ─────────────────────────────────────────
    # CORS
    # ─────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ─────────────────────────────────────────
    # GET
    # ─────────────────────────────────────────
    def do_GET(self):

        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        query = params.get("q", [""])[0].strip()
        limit = int(params.get("limit", ["12"])[0])

        if not query:
            return self._json({"error": "Missing ?q="}, 400)

        try:
            recipes = self._search_jow(query, limit)
            return self._json({"query": query, "recipes": recipes})

        except Exception as e:
            return self._json({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "recipes": []
            }, 500)

    # ─────────────────────────────────────────
    # JSON
    # ─────────────────────────────────────────
    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ─────────────────────────────────────────
    # API JOW
    # ─────────────────────────────────────────
    def _get_recipe_details(self, recipe_id):
        url = f"https://api.jow.fr/public/recipe/{recipe_id}"

        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _search_jow(self, query, limit=12):

        url = "https://api.jow.fr/public/recipe/quicksearch"
        params = urllib.parse.urlencode({
            "query": query,
            "limit": limit,
            "start": 0,
            "availabilityZoneId": "FR"
        })

        req = urllib.request.Request(
            f"{url}?{params}",
            method="POST",
            data=b"{}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-jow-withmeta": "1",
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        recipes = raw.get("data", {}).get("content", [])
        result = []

        for recipe in recipes:

            if not isinstance(recipe, dict):
                continue

            recipe_id = recipe.get("_id")
            details = {}

            if recipe_id:
                try:
                    details = self._get_recipe_details(recipe_id)
                except:
                    details = {}

            constituents = details.get("constituents") or recipe.get("constituents") or []

            ingredients = [
                self._parse_ingredient(c)
                for c in constituents
                if c.get("ingredient", {}).get("name")
            ]

            steps = self._extract_steps(details)

            image_url = self._build_image_url(recipe, details)

            video_url = self._normalize_media_url(
                details.get("videoUrl") or recipe.get("videoUrl")
            )

            # ── nutrition simple ──
            nutrition = {
                "calories": details.get("calories") or 0,
                "fat": details.get("matiereGrasses") or 0,
                "carbohydrates": details.get("glucides") or 0,
                "proteins": details.get("proteines") or 0,
                "fibers": details.get("fibres") or 0
            }

            eating_habits = details.get("eatingHabitsCompatibility") or {}

            required_tools = [
                t.get("name")
                for t in details.get("requiredTools", [])
                if isinstance(t, dict) and t.get("name")
            ]

            slug = recipe.get("slug") or details.get("slugs", {}).get("fr") or ""

            result.append({
                "id": recipe_id or "",
                "name": recipe.get("title") or recipe.get("name") or "",
                "description": details.get("description") or recipe.get("description") or "",
                "slug": slug,
                "url": f"https://jow.fr/recettes/{slug}" if slug else "",

                "imageUrl": image_url,
                "videoUrl": video_url,

                "prepTime": details.get("preparationTime") or 0,
                "cookTime": details.get("cookingTime") or 0,
                "totalTime": (
                    (details.get("preparationTime") or 0) +
                    (details.get("cookingTime") or 0)
                ),

                "pricePerPortion": details.get("pricePerPortion"),

                "nutriScore": details.get("note_nutriscore"),
                "greenScore": details.get("note_environment"),

                "nutrition": nutrition,
                "eatingHabits": eating_habits,
                "requiredTools": required_tools,

                "steps": steps,
                "ingredients": ingredients
            })

        return result

    # ─────────────────────────────────────────
    # IMAGE FIX ROBUST
    # ─────────────────────────────────────────
    def _normalize_media_url(self, url):
        if not url:
            return None

        if isinstance(url, dict):
            url = url.get("url") or url.get("src")

        if not url:
            return None

        url = str(url).strip()

        if url.startswith("http"):
            return url

        if url.startswith("/"):
            return STATIC + url.lstrip("/")

        return STATIC + url

    def _force_png(self, url):
        if not url:
            return None
        return url.rsplit(".", 1)[0] + ".png" if "." in url else url + ".png"


    def _force_jpg(self, url):
        if not url:
            return None
        return url.rsplit(".", 1)[0] + ".jpg" if "." in url else url + ".jpg"

    def _build_image_url(self, recipe, details):

        candidates = [
            recipe.get("editorialPictureUrl"),
            recipe.get("imageUrl"),
            recipe.get("pictureUrl"),

            details.get("editorialPictureUrl"),
            details.get("imageUrl"),
            details.get("pictureUrl"),
            details.get("imageWithBackgroundPatternUrl"),
        ]

        for c in candidates:
            url = self._normalize_media_url(c)
            if not url:
                continue

            # ── PRIORITÉ PNG ──
            png_url = self._force_png(url)
            jpg_url = self._force_jpg(url)

            # IMPORTANT :
            # on retourne PNG en priorité (UI), mais fallback safe
            return {
                "url": png_url,
                "fallback": jpg_url
            }

        return None

    # ─────────────────────────────────────────
    # INGREDIENTS
    # ─────────────────────────────────────────
    def _parse_ingredient(self, item):

        ingredient = item.get("ingredient", {})

        qty = item.get("quantityPerCover") or 0
        unit = item.get("unit", {}) or {}
        unit_name = unit.get("name") if isinstance(unit, dict) else ""

        qty_display, unit_display = _format_qty(qty, unit_name, "")

        img = ingredient.get("imageUrl")
        img = self._normalize_media_url(img)

        return {
            "name": ingredient.get("name", ""),
            "qty": qty_display,
            "unit": unit_display,
            "imageUrl": img,
            "isOptional": item.get("isOptional", False)
        }

    # ─────────────────────────────────────────
    # STEPS
    # ─────────────────────────────────────────
    def _extract_steps(self, details):

        directions = details.get("directions") or []

        steps = []
        for d in directions:
            if isinstance(d, dict):
                t = d.get("label")
                if t:
                    steps.append(t)
            elif isinstance(d, str):
                steps.append(d)

        return steps
