from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
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

    def _get_recipe_details(self, recipe_id):

        url = f"https://api.jow.fr/public/recipe/{recipe_id}"

        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(req, timeout=20) as resp:

            return json.loads(
                resp.read().decode("utf-8")
            )

    def _extract_steps(self, recipe):

        fields_found = []
        steps = []

        candidate_fields = [
            "steps",
            "preparationSteps",
            "recipeSteps",
            "instructions",
            "directions",
            "method",
            "preparation"
        ]

        for field in candidate_fields:

            value = recipe.get(field)

            if not value:
                continue

            fields_found.append(field)

            if isinstance(value, list):

                for item in value:

                    if isinstance(item, dict):

                        text = (
                            item.get("label")
                            or item.get("description")
                            or item.get("text")
                            or item.get("title")
                            or item.get("content")
                        )

                        if text:
                            steps.append(text)

                    elif isinstance(item, str):

                        steps.append(item)

            elif isinstance(value, str):

                steps.append(value)

            if steps:
                break

        return steps, fields_found

    def _search_jow(self, query, limit=12):

        search_url = (
            "https://api.jow.fr/public/recipe/quicksearch"
        )

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

        with urllib.request.urlopen(
            req,
            timeout=20
        ) as resp:

            raw = json.loads(
                resp.read().decode("utf-8")
            )

        data = raw.get("data", {})
        recipes = data.get("content", [])

        STATIC = "https://static.jow.fr/"

        result = []

        for recipe in recipes:

            if not isinstance(recipe, dict):
                continue

            recipe_id = recipe.get("_id")

            details = {}

            if recipe_id:

                try:
                    details = self._get_recipe_details(
                        recipe_id
                    )

                except Exception:
                    details = {}

            steps, step_fields = (
                self._extract_steps(details)
            )

            def parse_ingredient(item):

                ingredient = item.get(
                    "ingredient",
                    {}
                )

                quantity = (
                    item.get("quantityPerCover")
                    or item.get("quantity")
                    or ""
                )

                unit = ""

                if isinstance(
                    item.get("unit"),
                    dict
                ):
                    unit = (
                        item["unit"].get("name")
                        or ""
                    )

                return {
                    "name": ingredient.get(
                        "name",
                        ""
                    ),
                    "qty": str(quantity),
                    "unit": unit,
                    "isOptional": item.get(
                        "isOptional",
                        False
                    )
                }

            image_url = (
                recipe.get("editorialPictureUrl")
                or recipe.get("imageUrl")
            )

            video_url = (
                recipe.get("videoUrl")
            )

            nutrition = details.get(
                "nutritionalValues",
                {}
            )

            eating_habits = details.get(
                "eatingHabitsCompatibility",
                {}
                )

            required_tools = [
                tool.get("name")
                for tool in details.get(
                    "requiredTools",
                    []
                )
                if tool.get("name")
            ]

            result.append({

                "id": recipe.get("_id", ""),

                "name": (
                    recipe.get("title")
                    or recipe.get("name")
                    or ""
                ),

                "description": recipe.get(
                    "description",
                    ""
                ),

                "slug": recipe.get(
                    "slug",
                    ""
                ),

                "url": (
                    "https://jow.fr/recettes/"
                    + recipe.get(
                        "slug",
                        ""
                    )
                ),

                "imageUrl": (
                    STATIC + image_url
                    if image_url
                    else None
                ),

                "videoUrl": (
                    video_url
                    if (
                        video_url
                        and video_url.startswith(
                            "http"
                        )
                    )
                    else (
                        STATIC + video_url
                        if video_url
                        else None
                    )
                ),

                "prepTime": (
                    details.get(
                        "preparationTime"
                    )
                    or recipe.get(
                        "preparationTime",
                        0
                    )
                    or 0
                ),

                "cookTime": (
                    details.get(
                        "cookingTime"
                    )
                    or recipe.get(
                        "cookingTime",
                        0
                    )
                    or 0
                ),

                "totalTime": (
                    (
                        details.get(
                            "preparationTime"
                        )
                        or recipe.get(
                            "preparationTime",
                            0
                        )
                        or 0
                    )
                    +
                    (
                        details.get(
                            "cookingTime"
                        )
                        or recipe.get(
                            "cookingTime",
                            0
                        )
                        or 0
                    )
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
                    ) / 100,
                    2
                ),

                "nutriScore": details.get(
                    "note_nutriscore"
                ),

                "greenScore": details.get(
                    "note_environment"
                ),

                "caloriesPerPortion": (
                    details.get(
                        "calories"
                    )
                    or nutrition.get(
                        "calories"
                    )
                ),

                "nutrition": {
                    "calories": (
                        details.get(
                            "calories"
                        )
                        or nutrition.get(
                            "calories"
                        )
                    ),

                    "fat": (
                        nutrition.get(
                            "fat"
                        )
                        or nutrition.get(
                            "lipids"
                        )
                    ),

                    "carbohydrates": nutrition.get(
                        "carbohydrates"
                    ),

                    "proteins": nutrition.get(
                        "proteins"
                    ),

                    "fibers": nutrition.get(
                        "fibers"
                    )
                },

                "eatingHabits": {
                    "vegetarian": eating_habits.get(
                        "vegetarian"
                    ),

                    "vegan": eating_habits.get(
                        "vegan"
                    ),

                    "glutenFree": eating_habits.get(
                        "glutenFree"
                    ),

                    "dairyFree": eating_habits.get(
                        "dairyFree"
                    ),

                    "pescatarian": eating_habits.get(
                        "pescatarian"
                    ),

                    "porkless": eating_habits.get(
                        "porkless"
                    )
                },

                "requiredTools": required_tools,

                "steps": steps,

                "debugStepFields": (
                    step_fields
                ),

                "ingredients": [

                    parse_ingredient(c)

                    for c in details.get(
                        "constituents",
                        recipe.get(
                            "constituents",
                            []
                        )
                    )

                    if c.get(
                        "ingredient",
                        {}
                    ).get("name")
                ]
            })

        return result

    def _json(
        self,
        data,
        code=200
    ):

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

    def log_message(
        self,
        *args
    ):
        pass
