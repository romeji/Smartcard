import json
import traceback
import urllib.parse
import urllib.request
import urllib.error


STATIC = "https://static.jow.fr/"


def handler(request):

    try:
        query = request.args.get("q", "").strip()
        limit = int(request.args.get("limit", "12"))

        if not query:
            return response(
                {
                    "error": "Missing query parameter ?q="
                },
                400
            )

        recipes = search_jow(query, limit)

        return response({
            "query": query,
            "recipes": recipes
        })

    except Exception as e:

        return response(
            {
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            500
        )


def response(data, status=200):

    return (
        json.dumps(
            data,
            ensure_ascii=False
        ),
        status,
        {
            "Content-Type":
            "application/json; charset=utf-8",

            "Access-Control-Allow-Origin":
            "*",

            "Access-Control-Allow-Methods":
            "GET, OPTIONS",

            "Access-Control-Allow-Headers":
            "Content-Type"
        }
    )


def search_jow(query, limit=12):

    url = (
        "https://api.jow.fr/public/recipe/quicksearch"
    )

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
            "Origin": "https://jow.fr",
            "Referer": "https://jow.fr/",
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=20
    ) as r:

        raw = json.loads(
            r.read().decode("utf-8")
        )

    recipes = (
        raw
        .get("data", {})
        .get("content", [])
    )

    result = []

    for recipe in recipes:

        if not isinstance(recipe, dict):
            continue

        recipe_id = recipe.get("_id")

        detail = {}

        if recipe_id:
            detail = fetch_recipe_detail(
                recipe_id
            )

        steps = extract_steps(
            detail
        )

        result.append({

            "id":
            recipe_id,

            "name":
            recipe.get(
                "title",
                ""
            ),

            "description":
            recipe.get(
                "description",
                ""
            ),

            "slug":
            recipe.get(
                "slug",
                ""
            ),

            "url":
            (
                "https://jow.fr/recettes/"
                +
                recipe.get(
                    "slug",
                    ""
                )
            ),

            "imageUrl":
            build_static(
                recipe.get(
                    "editorialPictureUrl"
                )
                or
                recipe.get(
                    "imageUrl"
                )
            ),

            "videoUrl":
            build_static(
                recipe.get(
                    "videoUrl"
                )
            ),

            "prepTime":
            recipe.get(
                "preparationTime",
                0
            ),

            "cookTime":
            recipe.get(
                "cookingTime",
                0
            ),

            "totalTime":
            (
                recipe.get(
                    "preparationTime",
                    0
                )
                +
                recipe.get(
                    "cookingTime",
                    0
                )
            ),

            "steps": steps,
            "debugDetail": detail,

            "ingredients": [

                {
                    "name":
                    c.get(
                        "ingredient",
                        {}
                    ).get(
                        "name",
                        ""
                    ),

                    "qty":
                    str(
                        c.get(
                            "ingredient",
                            {}
                        ).get(
                            "quantityPerCover",
                            ""
                        )
                    ),

                    "unit": "",

                    "isOptional":
                    c.get(
                        "isOptional",
                        False
                    )
                }

                for c in recipe.get(
                    "constituents",
                    []
                )

                if c.get(
                    "ingredient",
                    {}
                ).get(
                    "name"
                )
            ]
        })

    return result


def fetch_recipe_detail(recipe_id):

    try:

        url = (
            f"https://api.jow.fr/public/recipe/{recipe_id}"
        )

        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Origin": "https://jow.fr",
                "Referer": "https://jow.fr/"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=20
        ) as r:

            raw = json.loads(
                r.read().decode("utf-8")
            )

            return {
                "__debug": raw
            }

    except Exception as e:

        return {
            "__error": str(e)
        }


def extract_steps(data):

    candidates = [

        "steps",
        "recipeSteps",
        "instructions",
        "method",
        "directions",
        "preparationSteps"

    ]

    result = []

    for field in candidates:

        value = data.get(field)

        if isinstance(
            value,
            list
        ):

            for s in value:

                if isinstance(
                    s,
                    str
                ):
                    result.append(
                        s
                    )

                elif isinstance(
                    s,
                    dict
                ):

                    text = (
                        s.get(
                            "label"
                        )
                        or
                        s.get(
                            "text"
                        )
                        or
                        s.get(
                            "description"
                        )
                        or
                        s.get(
                            "title"
                        )
                    )

                    if text:
                        result.append(
                            text
                        )

            if result:
                return result

    data_node = (
        data.get(
            "data",
            {}
        )
    )

    if data_node:
        return extract_steps(
            data_node
        )

    return []


def build_static(path):

    if not path:
        return None

    if path.startswith(
        "http"
    ):
        return path

    return STATIC + path
