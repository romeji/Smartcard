from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import traceback

STATIC = "https://static.jow.fr/"


def _format_qty(
    qty,
    unit_name,
    natural_unit_name
):
    """
    Convertit quantityPerCover (kg ou pièce)
    vers une valeur lisible.
    """

    if qty is None or qty == 0:
        return "", unit_name or ""

    natural = (
        natural_unit_name
        or ""
    ).lower()

    if natural == "kilogramme":

        grams = qty * 1000

        if grams < 1000:

            return (
                str(
                    int(
                        round(
                            grams
                        )
                    )
                ),
                "g"
            )

        return (
            str(
                round(
                    qty,
                    2
                )
            ),
            "kg"
        )

    val = (
        int(
            round(qty)
        )
        if qty == int(qty)
        else round(
            qty,
            1
        )
    )

    return (
        str(val),
        unit_name or ""
    )


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):

        self.send_response(200)

        self._cors()

        self.end_headers()

    def do_GET(self):

        parsed = urllib.parse.urlparse(
            self.path
        )

        params = urllib.parse.parse_qs(
            parsed.query
        )

        query = params.get(
            "q",
            [""]
        )[0].strip()

        limit = int(
            params.get(
                "limit",
                ["12"]
            )[0]
        )

        if not query:

            self._json(
                {
                    "error": "Missing query parameter ?q="
                },
                400
            )

            return

        try:

            recipes = self._search_jow(
                query,
                limit
            )

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

    def _get_recipe_details(
        self,
        recipe_id
    ):

        url = (
            f"https://api.jow.fr/public/recipe/{recipe_id}"
        )

        req = urllib.request.Request(

            url,

            headers={

                "Accept": "application/json",

                "User-Agent": "Mozilla/5.0"

            }
        )

        with urllib.request.urlopen(
            req,
            timeout=20
        ) as resp:

            return json.loads(
                resp.read().decode(
                    "utf-8"
                )
            )

    # ← NOUVEAU
    def _build_image_url(
        self,
        recipe,
        details
    ):

        candidates = [

            recipe.get(
                "editorialPictureUrl"
            ),

            recipe.get(
                "imageUrl"
            ),

            details.get(
                "editorialPictureUrl"
            ),

            details.get(
                "imageUrl"
            ),

            details.get(
                "imageWithBackgroundPatternUrl"
            ),

            details.get(
                "pictureUrl"
            ),

            recipe.get(
                "pictureUrl"
            )
        ]

        for img in candidates:

            if not img:
                continue

            if isinstance(
                img,
                dict
            ):

                img = (
                    img.get("url")
                    or img.get("src")
                )

            if not img:
                continue

            img = str(
                img
            ).strip()

            if (
                img.startswith("http://")
                or img.startswith("https://")
            ):

                return img

            if img.startswith("/"):

                return (
                    STATIC
                    + img[1:]
                )

            return (
                STATIC
                + img
            )

        return None

    def _parse_ingredient(
        self,
        item
    ):

        ingredient = item.get(
            "ingredient",
            {}
        )

        natural_unit = (

            ingredient.get(
                "naturalUnit"
            )

            or {}

            if isinstance(
                ingredient.get(
                    "naturalUnit"
                ),
                dict
            )

            else {}

        )

        natural_unit_name = natural_unit.get(
            "name",
            ""
        )

        unit_obj = (
            item.get(
                "unit",
                {}
            )
            or {}
        )

        unit_name = (

            unit_obj.get(
                "name",
                ""
            )

            if isinstance(
                unit_obj,
                dict
            )

            else ""

        )

        qty_raw = (
            item.get(
                "quantityPerCover"
            )
            or 0
        )

        if (
            unit_name
            and unit_name.lower()
            not in (
                "kilogramme",
                "kg"
            )
        ):

            val = qty_raw

            qty_display = (

                str(
                    int(
                        round(val)
                    )
                )

                if val == int(val)

                else str(
                    round(
                        val,
                        1
                    )
                )

            )

            unit_display = unit_name

        else:

            qty_display, unit_display = (

                _format_qty(

                    qty_raw,

                    unit_name,

                    natural_unit_name

                )
            )

        img_url = ingredient.get(
            "imageUrl",
            ""
        )

        img_full = (

            STATIC
            + img_url

            if (
                img_url
                and not img_url.startswith(
                    "http"
                )
            )

            else img_url

        )

        alternatives = []

        for alt in item.get(
            "alternatives",
            []
        ):

            alt_ing = alt.get(
                "ingredient",
                {}
            )

            if alt_ing.get(
                "name"
            ):

                alternatives.append(
                    alt_ing.get(
                        "name"
                    )
                )

        return {

            "name": ingredient.get(
                "name",
                ""
            ),

            "qty": qty_display,

            "unit": unit_display,

            "imageUrl": (
                img_full
                or None
            ),

            "isOptional": item.get(
                "isOptional",
                False
            ),

            "alternatives": alternatives
        }            # ── Images & vidéo ───────────────────────────────────────────

            image_url = self._build_image_url(
                recipe,
                details
            )

            video_url = (
                details.get(
                    "videoUrl"
                )
                or recipe.get(
                    "videoUrl"
                )
            )

            if (
                video_url
                and not video_url.startswith(
                    "http"
                )
            ):

                video_full = (
                    STATIC
                    + video_url
                )

            else:

                video_full = (
                    video_url
                    or None
                )

            # ── Nutrition ───────────────────────────────────────────────

            nutrition = {

                "calories": (
                    details.get(
                        "calories"
                    )
                ),

                "fat": (
                    details.get(
                        "matiereGrasses"
                    )
                ),

                "carbohydrates": (
                    details.get(
                        "glucides"
                    )
                ),

                "proteins": (
                    details.get(
                        "proteines"
                    )
                ),

                "fibers": (
                    details.get(
                        "fibres"
                    )
                )
            }

            eating_habits = details.get(
                "eatingHabitsCompatibility",
                {}
            )

            required_tools = [
                t.get("name")
                for t in details.get(
                    "requiredTools",
                    []
                )
                if t.get("name")
            ]

            result.append({

                "id": recipe.get(
                    "_id",
                    ""
                ),

                "name": (
                    recipe.get(
                        "title"
                    )
                    or recipe.get(
                        "name"
                    )
                    or ""
                ),

                "description": recipe.get(
                    "description",
                    ""
                ),

                "slug": (
                    recipe.get(
                        "slug"
                    )
                    or (
                        details.get(
                            "slugs",
                            {}
                        ).get(
                            "fr"
                        )
                    )
                ),

                "url": (
                    "https://jow.fr/recettes/"
                    + (
                        recipe.get(
                            "slug"
                        )
                        or details.get(
                            "slugs",
                            {}
                        ).get(
                            "fr",
                            ""
                        )
                    )
                ),

                "imageUrl": image_url,

                "videoUrl": video_full,

                "prepTime": (
                    details.get(
                        "preparationTime"
                    )
                    or 0
                ),

                "cookTime": (
                    details.get(
                        "cookingTime"
                    )
                    or 0
                ),

                "totalTime": (
                    details.get(
                        "totalPreparationAndCookingTime"
                    )
                    or 0
                ),

                "pricePerPortion": details.get(
                    "pricePerPortion"
                ),

                "pricePerPortionEuro": round(
                    (
                        details.get(
                            "pricePerPortion"
                        )
                        or 0
                    )
                    / 100,
                    2
                ),

                "nutriScore": (
                    details.get(
                        "note_nutriscore"
                    )
                ),

                "greenScore": (
                    details.get(
                        "note_environment"
                    )
                ),

                "caloriesPerPortion": (
                    details.get(
                        "calories"
                    )
                ),

                "nutrition": nutrition,

                "eatingHabits": eating_habits,

                "requiredTools": required_tools,

                "steps": steps,

                "ingredients": ingredients
            })

        return result

                       # ── Nutrition ────────────────────────────────────────────────

            nutr_raw = details.get("nutritionFactsRaw") or {}
            nutr_facts = details.get("nutritionalFacts") or []

            nutr_map = {
                f.get("id"): f.get("amount")
                for f in nutr_facts
                if isinstance(f, dict)
            }

            calories = nutr_map.get("ENERC") or nutr_raw.get("ENERC") or 0
            fat      = nutr_map.get("FAT")   or nutr_raw.get("FAT")   or 0
            carbs    = nutr_map.get("CHOAVL")or nutr_raw.get("CHOAVL")or 0
            proteins = nutr_map.get("PRO")   or nutr_raw.get("PRO")   or 0
            fibers   = nutr_map.get("FIBTG") or nutr_raw.get("FIBTG") or 0

            # ── Scores nutritionnels ─────────────────────────────────────

            rating_scores = details.get("nutritionalRatingScores") or []

            nutriscore = None
            greenscore = None
            score_provider = None

            for s in rating_scores:

                if not isinstance(s, dict):
                    continue

                sid = s.get("id")

                img = s.get("imageUrl")
                svg = s.get("vectorImageUrl")

                entry = {
                    "score": s.get("score"),
                    "label": s.get("label"),
                    "description": s.get("description"),
                    "imageUrl": (
                        STATIC + img
                        if img and not img.startswith("http")
                        else img
                    ),
                    "svgUrl": (
                        STATIC + svg
                        if svg and not svg.startswith("http")
                        else svg
                    ),
                }

                if sid == "nutriscore":
                    nutriscore = entry

                elif sid == "greenscore":
                    greenscore = entry

            # ── Fallback Nutri/Green score ───────────────────────────────

            etiq = (
                details.get("nutritionalrating", {})
                .get("etiquettable", {})
            )

            ns = (
                etiq.get("note_nutriscore")
                or details.get("note_nutriscore")
            )

            gs = (
                etiq.get("eco_score_new")
                or details.get("eco_score_new")
                or details.get("note_environment")
            )

            if ns and not nutriscore:
                ns = ns.upper()
                nutriscore = {
                    "score": ns,
                    "label": f"Nutri-score {ns}"
                }

            if gs and not greenscore:
                gs = gs.upper()
                greenscore = {
                    "score": gs,
                    "label": f"Green-score {gs}"
                }

            # ── Provider score ───────────────────────────────────────────

            rating_provider = details.get("nutritionalRatingProvider") or {}

            provider_img = rating_provider.get("imageUrl")

            score_provider = {
                "name": rating_provider.get("name"),
                "label": rating_provider.get("label"),
                "imageUrl": (
                    STATIC + provider_img
                    if provider_img and not provider_img.startswith("http")
                    else provider_img
                ),
            } if rating_provider.get("name") else None

            # ── Allergènes ───────────────────────────────────────────────

            allergens = etiq.get("allergenes") or []

            # ── Prix ─────────────────────────────────────────────────────

            price_cents = (
                details.get("pricePerPortion")
                or recipe.get("cartPricePerCover")
                or 0
            )

            price_euro = round(price_cents / 100, 2) if price_cents else 0

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

            eating_habits = (
                details.get("eatingHabitsCompatibility")
                or recipe.get("eatingHabitsCompatibility")
                or {}
            )

            # ── Ustensiles ───────────────────────────────────────────────

            required_tools = []

            for tool in details.get("requiredTools", []):

                if isinstance(tool, dict) and tool.get("name"):

                    tool_img = tool.get("imageUrl")

                    required_tools.append({
                        "name": tool.get("name"),
                        "imageUrl": (
                            STATIC + tool_img
                            if tool_img and not tool_img.startswith("http")
                            else tool_img
                        )
                    })

            # ── Métadonnées ──────────────────────────────────────────────

            difficulty = details.get("difficulty")

            origin = (
                details.get("origin", {}) or {}
            ).get("name")

            likes = details.get("likes")
            rating = details.get("aggregateRating")

            family_name = (
                details.get("family", {}) or {}
            ).get("name")

            author_name = (
                details.get("author", {}) or {}
            ).get("name")

            tags_list = [
                t.get("name")
                for t in (details.get("tags") or [])
                if isinstance(t, dict) and t.get("name")
            ]

            is_main_course = details.get("isMainCourse")

            co2 = etiq.get("gCO2e")

            slug = recipe.get("slug") or details.get("slugs", {}).get("fr") or ""

            # ── RESULT FINAL ─────────────────────────────────────────────

            result.append({

                "id": recipe.get("_id", ""),

                "name": recipe.get("title") or recipe.get("name") or "",

                "description": details.get("description") or recipe.get("description") or "",

                "slug": slug,

                "url": f"https://jow.fr/recettes/{slug}" if slug else "",

                "origin": origin,
                "family": family_name,
                "author": author_name,
                "tags": tags_list,
                "difficulty": difficulty,
                "isMainCourse": is_main_course,
                "likes": likes,
                "rating": round(rating, 2) if rating else None,

                # ── MEDIA (FIX PROPRE) ──
                "imageUrl": image_url,
                "videoUrl": video_full,

                # ── TEMPS ──
                "prepTime": details.get("preparationTime") or recipe.get("preparationTime") or 0,
                "cookTime": details.get("cookingTime") or recipe.get("cookingTime") or 0,
                "totalTime": (
                    (details.get("preparationTime") or recipe.get("preparationTime") or 0)
                    + (details.get("cookingTime") or recipe.get("cookingTime") or 0)
                ),

                # ── PRIX ──
                "pricePerPortionCents": price_cents,
                "pricePerPortionEuro": price_euro,
                "priceLevel": price_level,
                "priceLabel": price_label,

                # ── SCORES ──
                "nutriScore": nutriscore,
                "greenScore": greenscore,
                "scoreProvider": score_provider,
                "allergens": allergens,
                "co2grams": co2,

                # ── NUTRITION ──
                "nutrition": {
                    "calories": round(calories),
                    "fat": round(fat, 1),
                    "carbohydrates": round(carbs, 1),
                    "proteins": round(proteins, 1),
                    "fibers": round(fibers, 1),
                },

                # ── RÉGIMES ──
                "eatingHabits": eating_habits,

                # ── CUISINE ──
                "requiredTools": required_tools,
                "steps": steps,
                "ingredients": ingredients,
            })

        return result
