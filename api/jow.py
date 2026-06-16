from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import traceback

STATIC = "https://static.jow.fr/"


def _format_qty(qty, unit_name, natural_unit_name):
    """
    Convertit quantityPerCover (toujours en kg ou pièces) en valeur lisible.
    - Si l'unité naturelle est le Kilogramme : convertit en g si < 1 kg
    - Sinon garde la valeur telle quelle
    """
    if qty is None or qty == 0:
        return "", unit_name or ""

    natural = (natural_unit_name or "").lower()

    if natural == "kilogramme":
        grams = qty * 1000
        if grams < 1000:
            return str(int(round(grams))), "g"
        else:
            return str(round(qty, 2)), "kg"
    else:
        # Pièce, tranche, etc. — on affiche tel quel
        val = int(round(qty)) if qty == int(qty) else round(qty, 1)
        return str(val), unit_name or ""


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
            self._json({"error": "Missing query parameter ?q="}, 400)
            return

        try:
            recipes = self._search_jow(query, limit)
            self._json({"query": query, "recipes": recipes})
        except Exception as e:
            self._json({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "recipes": []
            }, 500)

    def _get_recipe_details(self, recipe_id):
        url = f"https://api.jow.fr/public/recipe/{recipe_id}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _parse_ingredient(self, item):
        """
        Parse un constituent Jow.
        quantityPerCover est TOUJOURS dans l'unité naturelle (kg ou pièce).
        On convertit en unité lisible selon naturalUnit.
        """
        ingredient = item.get("ingredient", {})
        natural_unit = (
            ingredient.get("naturalUnit") or {}
            if isinstance(ingredient.get("naturalUnit"), dict)
            else {}
        )
        natural_unit_name = natural_unit.get("name", "")

        # L'unité affichée dans la recette (peut être Tranche, Pièce, etc.)
        unit_obj = item.get("unit", {}) or {}
        unit_name = unit_obj.get("name", "") if isinstance(unit_obj, dict) else ""

        qty_raw = item.get("quantityPerCover") or 0

        # Si l'unité affichée n'est PAS kg, on l'utilise telle quelle
        if unit_name and unit_name.lower() not in ("kilogramme", "kg"):
            val = qty_raw
            val_str = str(int(round(val))) if val == int(val) else str(round(val, 1))
            qty_display = val_str
            unit_display = unit_name
        else:
            qty_display, unit_display = _format_qty(qty_raw, unit_name, natural_unit_name)

        # Image ingrédient
        img_url = ingredient.get("imageUrl", "")
        img_full = (STATIC + img_url) if img_url and not img_url.startswith("http") else img_url

        # Alternatives
        alternatives = []
        for alt in item.get("alternatives", []):
            alt_ing = alt.get("ingredient", {})
            if alt_ing.get("name"):
                alternatives.append(alt_ing.get("name"))

        return {
            "name": ingredient.get("name", ""),
            "qty": qty_display,
            "unit": unit_display,
            "imageUrl": img_full or None,
            "isOptional": item.get("isOptional", False),
            "alternatives": alternatives
        }

    def _extract_steps(self, details):
        """
        Jow utilise 'directions' (liste d'objets avec 'label').
        Fallback sur d'autres champs si absent.
        """
        # Priorité : directions (format réel de l'API)
        directions = details.get("directions", [])
        if directions and isinstance(directions, list):
            steps = []
            for d in directions:
                if isinstance(d, dict):
                    label = d.get("label", "").strip()
                    if label:
                        steps.append(label)
                elif isinstance(d, str) and d.strip():
                    steps.append(d.strip())
            if steps:
                return steps

        # Fallbacks
        for field in ["steps", "preparationSteps", "recipeSteps", "instructions"]:
            value = details.get(field)
            if not value:
                continue
            steps = []
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        text = (item.get("label") or item.get("description")
                                or item.get("text") or "")
                        if text.strip():
                            steps.append(text.strip())
                    elif isinstance(item, str) and item.strip():
                        steps.append(item.strip())
            elif isinstance(value, str) and value.strip():
                steps.append(value.strip())
            if steps:
                return steps

        return []

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
            raw = json.loads(resp.read().decode("utf-8"))

        data = raw.get("data", {})
        recipes = data.get("content", [])
        result = []

        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue

            recipe_id = recipe.get("_id")
            details = {}
            if recipe_id:
                try:
                    details = self._get_recipe_details(recipe_id)
                except Exception:
                    details = {}

            # ── Ingrédients ──────────────────────────────────────────────
            constituents = details.get("constituents") or recipe.get("constituents") or []
            ingredients = [
                self._parse_ingredient(c)
                for c in constituents
                if c.get("ingredient", {}).get("name")
            ]

            # ── Étapes ───────────────────────────────────────────────────
            steps = self._extract_steps(details)

            # ── Images & vidéo ───────────────────────────────────────────
            image_url = details.get("editorialPictureUrl") or recipe.get("editorialPictureUrl") or recipe.get("imageUrl")
            video_url = details.get("videoUrl") or recipe.get("videoUrl")

            image_full = (STATIC + image_url) if image_url and not image_url.startswith("http") else image_url
            # PNG version: replace extension or append ?format=png
            if image_full and image_full.startswith("https://static.jow.fr/"):
                # Try PNG variant (same path, extension swap)
                png_url = image_full.rsplit('.', 1)[0] + '.png' if '.' in image_full.split('/')[-1] else image_full + '.png'
            else:
                png_url = image_full
            if video_url:
                video_full = video_url if video_url.startswith("http") else (STATIC + video_url)
            else:
                video_full = None

            # ── Nutrition ────────────────────────────────────────────────
            nutr_raw = details.get("nutritionFactsRaw") or {}
            nutr_facts = details.get("nutritionalFacts") or []
            # nutritionalFacts est une liste [{id, label, unit, amount}]
            nutr_map = {f["id"]: f["amount"] for f in nutr_facts if isinstance(f, dict)}

            calories  = nutr_map.get("ENERC") or nutr_raw.get("ENERC") or 0
            fat       = nutr_map.get("FAT")   or nutr_raw.get("FAT")   or 0
            carbs     = nutr_map.get("CHOAVL")or nutr_raw.get("CHOAVL")or 0
            proteins  = nutr_map.get("PRO")   or nutr_raw.get("PRO")   or 0
            fibers    = nutr_map.get("FIBTG") or nutr_raw.get("FIBTG") or 0

            # ── Scores nutritionnels (Nutri-Score & Green-Score) ─────────
            rating_scores = details.get("nutritionalRatingScores") or []
            nutriscore_data = {}
            greenscore_data = {}
            for s in rating_scores:
                if not isinstance(s, dict):
                    continue
                sid = s.get("id", "")
                img = s.get("imageUrl", "")
                svg = s.get("vectorImageUrl", "")
                entry = {
                    "score": s.get("score"),
                    "label": s.get("label"),
                    "description": s.get("description"),
                    "imageUrl": (STATIC + img) if img and not img.startswith("http") else img,
                    "svgUrl":   (STATIC + svg) if svg and not svg.startswith("http") else svg,
                }
                if sid == "nutriscore":
                    nutriscore_data = entry
                elif sid == "greenscore":
                    greenscore_data = entry

            # Fallback lettre depuis nutritionalrating
            nr = details.get("nutritionalrating", {}) or {}
            etiq = nr.get("etiquettable") or {}
            if not nutriscore_data.get("score"):
                ns_letter = etiq.get("note_nutriscore") or details.get("note_nutriscore")
                if ns_letter:
                    ns_letter = ns_letter.upper()
                    nutriscore_data = {"score": ns_letter, "label": f"Nutri-score {ns_letter}"}
            if not greenscore_data.get("score"):
                gs_letter = etiq.get("eco_score_new") or details.get("note_environment")
                if gs_letter:
                    gs_letter = gs_letter.upper()
                    greenscore_data = {"score": gs_letter, "label": f"Green-score {gs_letter}"}

            # Provider du score
            rating_provider = details.get("nutritionalRatingProvider") or {}
            provider_img = rating_provider.get("imageUrl", "")
            provider_entry = {
                "name":     rating_provider.get("name"),
                "label":    rating_provider.get("label"),
                "imageUrl": (STATIC + provider_img) if provider_img and not provider_img.startswith("http") else provider_img,
            } if rating_provider.get("name") else None

            # Allergènes
            allergens = etiq.get("allergenes") or []

            # ── Prix ─────────────────────────────────────────────────────
            price_cents = details.get("pricePerPortion") or recipe.get("cartPricePerCover") or 0
            price_euro  = round(price_cents / 100, 2) if price_cents else 0
            price_level = details.get("pricePerPortionLevel") or 0
            if price_level == 0 and price_euro:
                if price_euro < 2:
                    price_level = 1
                elif price_euro <= 4:
                    price_level = 2
                else:
                    price_level = 3
            price_tag = details.get("pricePerPortionTag") or {}
            price_label = price_tag.get("label") or (
                "Moins de 2€/pers." if price_level == 1 else
                "Entre 2€ et 4€/pers." if price_level == 2 else
                "Plus de 4€/pers." if price_level == 3 else ""
            )

            # ── Régimes ──────────────────────────────────────────────────
            eating_habits = details.get("eatingHabitsCompatibility") or recipe.get("eatingHabitsCompatibility") or {}

            # ── Ustensiles ───────────────────────────────────────────────
            required_tools = []
            for tool in details.get("requiredTools", []):
                if isinstance(tool, dict) and tool.get("name"):
                    tool_img = tool.get("imageUrl", "")
                    required_tools.append({
                        "name": tool.get("name"),
                        "imageUrl": (STATIC + tool_img) if tool_img and not tool_img.startswith("http") else tool_img
                    })

            # ── Métadonnées supplémentaires ──────────────────────────────
            difficulty    = details.get("difficulty")           # 1-3
            origin        = (details.get("origin") or {}).get("name")  # ex: "Italienne"
            likes         = details.get("likes")
            rating        = details.get("aggregateRating")
            family_name   = (details.get("family") or {}).get("name")
            author_name   = (details.get("author") or {}).get("name")
            tags_list     = [t.get("name") for t in (details.get("tags") or []) if isinstance(t, dict) and t.get("name")]
            is_main_course= details.get("isMainCourse")
            co2           = etiq.get("gCO2e")   # grammes CO2 équivalent

            slug = recipe.get("slug") or details.get("slug") or ""

            result.append({
                # ── Identité ──
                "id":          recipe.get("_id", ""),
                "name":        recipe.get("title") or recipe.get("name") or "",
                "description": details.get("description") or recipe.get("description") or "",
                "slug":        slug,
                "url":         f"https://jow.fr/recettes/{slug}" if slug else "",
                "origin":      origin,
                "family":      family_name,
                "author":      author_name,
                "tags":        tags_list,
                "difficulty":  difficulty,
                "isMainCourse": is_main_course,
                "likes":       likes,
                "rating":      round(rating, 2) if rating else None,
                "composition": details.get("composition") or "",

                # ── Médias ──
                "imageUrl":  image_full,
                "pngUrl":    png_url,
                "videoUrl":  video_full,

                # ── Temps ──
                "prepTime":  details.get("preparationTime") or recipe.get("preparationTime") or 0,
                "cookTime":  details.get("cookingTime")     or recipe.get("cookingTime")     or 0,
                "totalTime": (details.get("preparationTime") or recipe.get("preparationTime") or 0)
                           + (details.get("cookingTime")     or recipe.get("cookingTime")     or 0),

                # ── Prix ──
                "pricePerPortionCents": price_cents,
                "pricePerPortionEuro":  price_euro,
                "priceLevel":           price_level,   # 1=€  2=€€  3=€€€
                "priceLabel":           price_label,

                # ── Scores ──
                "nutriScore":      nutriscore_data,
                "greenScore":      greenscore_data,
                "scoreProvider":   provider_entry,
                "allergens":       allergens,
                "co2grams":        co2,

                # ── Nutrition ──
                "nutrition": {
                    "calories":      round(calories),
                    "fat":           round(fat, 1),
                    "carbohydrates": round(carbs, 1),
                    "proteins":      round(proteins, 1),
                    "fibers":        round(fibers, 1),
                },

                # ── Régimes ──
                "eatingHabits": {
                    "vegetarian":  eating_habits.get("vegetarian"),
                    "vegan":       eating_habits.get("vegan"),
                    "glutenFree":  eating_habits.get("glutenFree"),
                    "dairyFree":   eating_habits.get("dairyFree"),
                    "pescatarian": eating_habits.get("pescatarian"),
                    "porkless":    eating_habits.get("porkless"),
                },

                # ── Cuisine ──
                "requiredTools": required_tools,
                "steps":         steps,
                "ingredients":   ingredients,
            })

        return result

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, *args):
        pass
