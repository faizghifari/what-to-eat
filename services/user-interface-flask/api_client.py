from functools import wraps
import requests
from flask import session, redirect, url_for, flash

# Service URLs
AUTH_SERVICE_URL = "http://localhost:8000/auth"
MENU_SERVICE_URL = "http://localhost:8000"
RECIPE_SERVICE_URL = "http://localhost:8000"
EAT_TOGETHER_SERVICE_URL = "http://localhost:8000/eat-together"


class APIError(Exception):
    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_uuid" not in session:
            # session["user_uuid"] = "dummy-user-123"  # Dummy UUID for testing
            flash("You must be logged in to access this page")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


class APIClient:
    @staticmethod
    def get_headers():
        return {
            "Authorization": f'Bearer {session.get("access_token", "")}',
            "Content-Type": "application/json",
            "X-User-Uuid": session.get("user_uuid"),
        }

    @staticmethod
    def get_access_token_params():
        return {
            "access_token": session.get("access_token", ""),
        }

    @staticmethod
    def handle_response(response: requests.Response):
        try:
            data = response.json()

            if response.status_code == 401:
                session.clear()
                flash("Session expired. Please login again")
                return redirect(url_for("login"))
            elif response.status_code == 403:
                flash("You do not have permission to perform this action")
                raise APIError("Permission denied", 403)
            elif response.status_code == 404:
                flash("Resource not found")
                raise APIError("Not found", 404)
            elif response.status_code >= 500:
                flash("Server error. Please try again later")
                raise APIError("Server error", response.status_code)
            elif not response.ok:
                flash("An unexpected error occurred")
                raise APIError("Request failed", response.status_code)

            return data
        except ValueError:
            flash("Invalid response from server")
            raise APIError("Invalid response")
        except Exception as e:
            if not isinstance(e, APIError):
                flash("An unexpected error occurred")
                raise APIError("Unexpected error")
            raise

    # Auth Service
    @classmethod
    def login(cls, email, password):
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/login", json={"email": email, "password": password}
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def signup(cls, email, password, password2):
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/signup",
                json={"email": email, "password": password, "password2": password2},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def signout(cls):
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/logout", headers=cls.get_headers()
            )
            cls.handle_response(response)
        except Exception:
            pass  # Always clear session on signout
        finally:
            session.clear()

    # Menu Service
    @classmethod
    def get_all_menus(cls):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/menu",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch menus")
            return []

    @classmethod
    def get_restaurant_menu(cls, restaurant_id):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/restaurant/{restaurant_id}/menu",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch restaurant menu")
            return []

    @classmethod
    def get_menu_details(cls, menu_id):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/menu/{menu_id}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch menu details")
            return None

    @classmethod
    def rate_menu(cls, menu_id, rating, review=""):
        try:
            response = requests.post(
                f"{MENU_SERVICE_URL}/menu/{menu_id}/rate",
                headers=cls.get_headers(),
                json={"rating_value": rating, "comment_text": review},
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to submit rating")
            raise APIError("Rating submission failed")

    @classmethod
    def get_all_restaurants(cls):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/restaurant",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch restaurants")
            return []

    @classmethod
    def get_food_matches(cls):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/restaurant/matches",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch food matches")
            return []

    @classmethod
    def get_restaurant(cls, restaurant_id):
        try:
            response = requests.get(
                f"{MENU_SERVICE_URL}/restaurant/{restaurant_id}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch restaurant details")
            return None

    # Recipe Service
    @classmethod
    def get_recipe_details(cls, recipe_id):
        try:
            response = requests.get(
                f"{RECIPE_SERVICE_URL}/recipe/{recipe_id}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch recipe details")
            return None

    @classmethod
    def get_recipe_matches(cls):
        try:
            response = requests.get(
                f"{RECIPE_SERVICE_URL}/recipe/matches",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch recipe matches")
            return []

    @classmethod
    def get_recipe_matches_web(cls):
        try:
            response = requests.get(
                f"{RECIPE_SERVICE_URL}/recipe/matches_web",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to search internet recipes")
            return []

    # Eat Together Service
    @classmethod
    def create_group(cls, name, description=None):
        try:
            response = requests.post(
                f"{EAT_TOGETHER_SERVICE_URL}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
                json={"name": name, "description": description},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to create group")
            raise APIError("Group creation failed")

    @classmethod
    def get_group_by_code(cls, group_code):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/group/{group_code}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch group")
            return None

    @classmethod
    def get_my_groups(cls):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/me",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch your groups")
            return []

    @classmethod
    def add_member_to_group(cls, group_id, member_id):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/add-member",
                headers=cls.get_headers(),
                params={"member_id": member_id, **cls.get_access_token_params()},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to add member")
            raise APIError("Member addition failed")

    @classmethod
    def remove_member_from_group(cls, group_id, member_id):
        try:
            response = requests.delete(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/remove-member/{member_id}",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to remove member")
            raise APIError("Member removal failed")

    @classmethod
    def update_guest_preferences(cls, group_id, preferences):
        try:
            response = requests.put(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/update-guest",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
                json=preferences,
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to update preferences")
            raise APIError("Preference update failed")

    @classmethod
    def get_group_food_matches(cls, group_id):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/food-matches",
                headers=cls.get_headers(),
                params=cls.get_access_token_params(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch group recommendations")
            return []

    @classmethod
    def search_user_by_email(cls, email):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/user",
                headers=cls.get_headers(),
                params={"email": email, **cls.get_access_token_params()},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to search for user")
            return []
