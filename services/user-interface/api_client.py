import requests
from functools import wraps
from flask import session, redirect, url_for, flash

# Service URLs
AUTH_SERVICE_URL = "http://localhost:8000/auth"
MENU_SERVICE_URL = "http://localhost:8000"
RECIPE_SERVICE_URL = "http://localhost:8000"
EAT_TOGETHER_SERVICE_URL = "http://localhost:8000/eat-together"
PROFILE_SERVICE_URL = "http://localhost:8000/profile"


class APIError(Exception):
    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_uuid" not in session:
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
            "access-token": session.get("access_token", ""),
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
            if response.ok:
                return {}

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
                json={"email": email, "password_1": password, "password_2": password2},
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
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to search internet recipes")
            return []

    # Eat Together Service
    @classmethod
    def create_group(cls, name, guest_preferences=[], guest_restrictions=[]):
        try:
            response = requests.post(
                f"{EAT_TOGETHER_SERVICE_URL}",
                headers=cls.get_headers(),
                json={
                    "group_name": name,
                    "guest_preferences": guest_preferences,
                    "guest_restrictions": guest_restrictions,
                },
            )
            return cls.handle_response(response)
        except requests.RequestException as e:
            flash(f"Failed to create group - {str(e)}")
            raise APIError("Group creation failed")

    @classmethod
    def delete_group(cls, group_id):
        try:
            response = requests.delete(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}",
                headers=cls.get_headers(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to delete group")
            raise APIError("Group deletion failed")

    @classmethod
    def get_group_by_id(cls, group_id):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}",
                headers=cls.get_headers(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch group")
            return None

    @classmethod
    def get_my_group(cls):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/me",
                headers=cls.get_headers(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to fetch your group")
            return None

    @classmethod
    def add_member_to_group(cls, group_id, member_id):
        try:
            response = requests.get(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/add-member",
                headers=cls.get_headers(),
                params={"member_id": member_id},
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
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to remove member")
            raise APIError("Member removal failed")

    @classmethod
    def join_group(cls, group_code):
        try:
            response = requests.post(
                f"{EAT_TOGETHER_SERVICE_URL}/join",
                headers=cls.get_headers(),
                json={"group_code": group_code},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to join group")
            raise APIError("Group join failed")

    @classmethod
    def leave_group(cls):
        try:
            response = requests.delete(
                f"{EAT_TOGETHER_SERVICE_URL}/leave",
                headers=cls.get_headers(),
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to leave group")
            raise APIError("Group leave failed")

    @classmethod
    def update_guest(cls, group_id, preferences, restrictions):
        try:
            response = requests.put(
                f"{EAT_TOGETHER_SERVICE_URL}/{group_id}/update-guest",
                headers=cls.get_headers(),
                json={
                    "guest_preferences": preferences,
                    "guest_restrictions": restrictions,
                },
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
                params={"email": email},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Failed to search for user")
            return []

    # Profile Service
    @classmethod
    def get_profile(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def get_preferences(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/preferences", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def get_restrictions(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/restrictions", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def get_ingredients(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/ingredients", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def get_tools(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/tools", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def get_location(cls):
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/location", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def edit_profile(cls, profile_data):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/profile",
                headers=cls.get_headers(),
                json=profile_data,
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def update_preferences(cls, preferences):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/preferences",
                headers=cls.get_headers(),
                json={"dietary_preferences": preferences},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def update_restrictions(cls, restrictions):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/restrictions",
                headers=cls.get_headers(),
                json={"dietary_restrictions": restrictions},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def update_tools(cls, tools):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/tools",
                headers=cls.get_headers(),
                json={"available_tools": tools},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def update_ingredients(cls, ingredients):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/ingredients",
                headers=cls.get_headers(),
                json={"available_ingredients": ingredients},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def update_location(cls, location):
        try:
            response = requests.put(
                f"{PROFILE_SERVICE_URL}/location",
                headers=cls.get_headers(),
                json={"current_location": location},
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")

    @classmethod
    def create_new_profile(cls):
        try:
            response = requests.post(
                f"{PROFILE_SERVICE_URL}/new", headers=cls.get_headers()
            )
            return cls.handle_response(response)
        except requests.RequestException:
            flash("Connection error. Please try again later")
            raise APIError("Connection error")
