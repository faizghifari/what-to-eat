from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    jsonify,
)
import os
from api_client import APIClient, APIError, login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)


# Routes
@app.route("/")
def index():
    if "user_uuid" in session:
        return redirect(url_for("food_home"))
    return render_template("index.html")

    # Temporary bypass authentication
    # if "user_uuid" not in session:
    #     session["user_uuid"] = "dummy-user-123"  # Dummy UUID for testing
    return redirect(url_for("food_home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            result = APIClient.login(email, password)
            if (
                result.get("x_user_uid")
                and result.get("access_token")
                and result.get("refresh_token")
            ):
                session["user_uuid"] = result["x_user_uid"]
                session["access_token"] = result["access_token"]
                session["refresh_token"] = result["refresh_token"]

                return redirect(url_for("food_home"))
            flash("Invalid email or password")
        except Exception:
            flash("Login failed. Please try again.")

        # Temporary bypass authentication
        # session["user_uuid"] = "dummy-user-123"  # Dummy UUID for testing
        # return redirect(url_for("food_home"))
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("confirm-password")
        try:
            result = APIClient.signup(email, password, password2)
            if (
                result.get("x_user_uid")
                and result.get("access_token")
                and result.get("refresh_token")
            ):
                session["user_uuid"] = result["x_user_uid"]
                session["access_token"] = result["access_token"]
                session["refresh_token"] = result["refresh_token"]

                return redirect(url_for("food_home"))
            flash("Registration failed. Please try again.")
        except Exception as e:
            flash("Registration failed. Please try again.")

        # Temporary bypass authentication
        # session["user_uuid"] = "dummy-user-123"  # Dummy UUID for testing
        # return redirect(url_for("food_home"))
    return render_template("signup.html")


@app.route("/food")
@login_required
def food_home():
    try:
        restaurants = APIClient.get_all_restaurants()
        recommended_menus = APIClient.get_food_matches()
        return render_template(
            "food_home.html",
            restaurants=restaurants,
            recommended_menus=recommended_menus,
        )
    except Exception:  # Use Exception instead of bare except
        flash("Failed to load recommendations")
        return render_template("food_home.html", restaurants=[], recommended_menus=[])


@app.route("/food/restaurant/<int:id>")
@login_required
def restaurant_matches(id):
    try:
        restaurant = APIClient.get_restaurant(id)
        menu_items = APIClient.get_restaurant_menu(id)
        return render_template(
            "restaurant_matches.html", restaurant=restaurant, menu_items=menu_items
        )
    except Exception:
        flash("Failed to load restaurant information")
        return redirect(url_for("food_home"))


@app.route("/food/menu/<int:id>")
@login_required
def menu_detail(id):
    try:
        menu = APIClient.get_menu_details(id)
        return render_template("menu_detail.html", menu=menu)
    except Exception:
        flash("Failed to load menu information")
        return redirect(url_for("food_home"))


@app.route("/recipe")
@login_required
def recipe_home():
    try:
        recipes = APIClient.get_recipe_matches()
        return render_template("recipe_home.html", recipes=recipes)
    except Exception:
        flash("Failed to load recipes")
        return render_template("recipe_home.html", recipes=[])


@app.route("/recipe/search")
@login_required
def search_recipes():
    try:
        recipes = APIClient.get_recipe_matches_web()
        return jsonify(recipes)
    except Exception:
        return jsonify({"error": "Failed to search recipes"})


@app.route("/recipe/<int:id>")
@login_required
def recipe_detail(id):
    try:
        recipe = APIClient.get_recipe_details(id)
        return render_template("recipe_detail.html", recipe=recipe)
    except Exception:
        flash("Failed to load recipe information")
        return redirect(url_for("recipe_home"))


@app.route("/tools-ingredients")
@login_required
def tools_ingredients():
    return render_template("tools_ingredients.html")


@app.route("/preferences")
@login_required
def preferences():
    return render_template("preferences.html")


@app.route("/eat-together")
@login_required
def eat_together():
    try:
        groups = APIClient.get_my_groups()
        return render_template("eat_together.html", groups=groups)
    except Exception:
        flash("Failed to load groups")
        return render_template("eat_together.html", groups=[])


@app.route("/eat-together/group/<int:id>/settings")
@login_required
def group_settings(id):
    try:
        group = APIClient.get_group_by_code(id)
        return render_template("group_settings.html", group=group)
    except Exception:
        flash("Failed to load group settings")
        return redirect(url_for("eat_together"))


@app.route("/eat-together/group/<int:id>/recommendations")
@login_required
def group_recommendations(id):
    try:
        matches = APIClient.get_group_food_matches(id)
        return render_template("group_recommendations.html", matches=matches)
    except Exception:
        flash("Failed to load recommendations")
        return redirect(url_for("eat_together"))


# API endpoints for AJAX calls
@app.route("/api/menu/<int:id>/rate", methods=["POST"])
@login_required
def rate_menu(id):
    try:
        data = request.get_json()
        if not data or "rating" not in data:
            return jsonify({"error": "Rating is required"}), 400
        APIClient.rate_menu(id, data["rating"])
        return jsonify({"success": True})
    except APIError:
        return jsonify({"error": "Failed to submit rating"}), 400


@app.route("/api/recipe/<int:id>/rate", methods=["POST"])
@login_required
def rate_recipe(id):
    try:
        data = request.get_json()
        if not data or "rating" not in data:
            return jsonify({"error": "Rating is required"}), 400
        APIClient.rate_menu(
            id, data["rating"]
        )  # Using rate_menu instead of nonexistent create_user_recipe_rating
        return jsonify({"success": True})
    except APIError:
        return jsonify({"error": "Failed to submit rating"}), 400


@app.route("/api/group/create", methods=["POST"])
@login_required
def create_group():
    try:
        data = request.get_json()
        if not data or "name" not in data:
            return jsonify({"error": "Name is required"}), 400
        description = data.get("description")
        group = APIClient.create_group(data["name"], description)
        return jsonify({"success": True, "group": group})
    except APIError:
        return jsonify({"error": "Failed to create group"}), 400


@app.route("/api/group/<int:id>/add-member", methods=["POST"])
@login_required
def add_member(id):
    try:
        data = request.get_json()
        if not data or "member_id" not in data:
            return jsonify({"error": "Member ID is required"}), 400
        APIClient.add_member_to_group(id, data["member_id"])
        return jsonify({"success": True})
    except APIError:
        return jsonify({"error": "Failed to add member"}), 400


@app.route("/api/group/<int:id>/remove-member/<int:member_id>", methods=["DELETE"])
@login_required
def remove_member(id, member_id):
    try:
        APIClient.remove_member_from_group(id, member_id)
        return jsonify({"success": True})
    except APIError:
        return jsonify({"error": "Failed to remove member"}), 400


@app.route("/api/user/search")
@login_required
def search_user():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400
        users = APIClient.search_user_by_email(email)
        return jsonify({"users": users})
    except APIError:
        return jsonify({"error": "Failed to search user"}), 400


@app.route("/signout")
def signout():
    # Clear the session
    session.clear()
    flash("You have been signed out")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
