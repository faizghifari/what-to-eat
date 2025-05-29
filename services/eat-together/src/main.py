import os
import string
import random

from fastapi import FastAPI, HTTPException, Header
from supabase import Client, create_client
from typing import Annotated

from dotenv import load_dotenv

from models import (
    User,
    GroupMember,
    EatTogetherGroup,
    Restaurant,
    Location,
    CreateEatTogetherGroupRequest,
    AddMemberRequest,
    JoinEatTogetherGroupRequest,
    UpdateGuestPreferenceRestrictionsRequest,
    EatTogetherMemberResponse,
    MenuResponse,
    RestaurantMenuResponse,
)

app = FastAPI()

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def hello_world():
    return {"Hello": "World"}


"""
Eat Together Group
"""


@app.post("/eat-together", status_code=201)
def create_group(
    x_user_uuid: Annotated[str, Header()], body: CreateEatTogetherGroupRequest
):
    # Get user email
    user_email = supabase.auth.admin.get_user_by_id(x_user_uuid).user.email

    # Create a random group code
    group_code = "".join([random.choice(string.ascii_uppercase) for _ in range(4)])

    # Insert new group into the database
    new_group = {
        "group_name": body.group_name,
        "group_code": group_code,
        "guest_preferences": (
            [
                [preference.model_dump() for preference in guest]
                for guest in body.guest_preferences
            ]
        ),
        "guest_restrictions": (
            [
                [restrictions.model_dump() for restrictions in guest]
                for guest in body.guest_restrictions
            ]
        ),
        "leader": x_user_uuid,
    }
    eat_together_group = (
        supabase.table("EatTogetherGroup").insert(new_group).execute().data[0]
    )

    # Insert membership for the group leader
    new_membership = {
        "user": x_user_uuid,
        "group": eat_together_group["id"],
        "role": "leader",
    }
    supabase.table("UserGroup").insert(new_membership).execute()

    eat_together_group["leader"] = User(uuid=x_user_uuid, email=user_email or "")
    return EatTogetherGroup(**eat_together_group)


@app.get("/eat-together")
def list_all_groups():
    # Fetch all groups from the database
    groups = supabase.table("EatTogetherGroup").select("*").execute().data

    # Fetch user details for each group leader
    for group in groups:
        user = supabase.auth.admin.get_user_by_id(group["leader"]).user
        group["leader"] = User(uuid=user.id, email=user.email or "")

    return [EatTogetherGroup(**group) for group in groups]


@app.post("/eat-together/join")
def join_group_by_code(
    x_user_uuid: Annotated[str, Header()], body: JoinEatTogetherGroupRequest
):
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup")
        .select("*")
        .eq("group_code", body.group_code)
        .execute()
        .data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Insert membership for the new member
    new_membership = {
        "user": x_user_uuid,
        "group": group["id"],
        "role": "member",
    }
    supabase.table("UserGroup").insert(new_membership).execute()

    # Fetch the updated user group with the new member
    members = (
        supabase.table("UserGroup").select("*").eq("group", group["id"]).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email,
            ),
            role=member["role"],
        )
        for member in members
    ]

    leader_user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    group["leader"] = User(uuid=leader_user.id, email=leader_user.email)
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.delete("/eat-together/leave", status_code=204)
def leave_group(x_user_uuid: Annotated[str, Header()]):
    # Fetch the groups where the user is a member
    membership = (
        supabase.table("UserGroup").select("*").eq("user", x_user_uuid).execute().data
    )

    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of any group")

    group_id = membership[0]["group"]

    # Check if the user is the group leader
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    if x_user_uuid == group["leader"]:
        raise HTTPException(
            status_code=403, detail="Group leader cannot leave the group"
        )

    # Delete the membership
    supabase.table("UserGroup").delete().eq("user", x_user_uuid).eq(
        "group", group_id
    ).execute()

    return None


@app.get("/eat-together/group/{group_code}")
def get_group_by_code(group_code: str):
    # Fetch the group by code
    group = (
        supabase.table("EatTogetherGroup")
        .select("*")
        .eq("group_code", group_code)
        .execute()
        .data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Fetch the group with members and leader details
    members = (
        supabase.table("UserGroup").select("*").eq("group", group["id"]).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email
                or "",
            ),
            role=member["role"],
        )
        for member in members
    ]

    group["leader"] = User(
        uuid=group["leader"],
        email=supabase.auth.admin.get_user_by_id(group["leader"]).user.email or "",
    )
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.get("/eat-together/me")
def get_my_group(x_user_uuid: Annotated[str, Header()]):
    # Fetch the groups where the user is a member
    membership = (
        supabase.table("UserGroup").select("*").eq("user", x_user_uuid).execute().data
    )

    if not membership:
        return {}

    group_id = membership[0]["group"]

    # Fetch the groups with their details
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )

    group = group[0]

    # Fetch the user group with members and leader details
    members = (
        supabase.table("UserGroup").select("*").eq("group", group_id).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email
                or "",
            ),
            role=member["role"],
        )
        for member in members
    ]

    group["leader"] = User(
        uuid=group["leader"],
        email=supabase.auth.admin.get_user_by_id(group["leader"]).user.email or "",
    )
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.post("/eat-together/{group_id}/add-member", status_code=201)
def add_member_to_group(
    x_user_uuid: Annotated[str, Header()], group_id: int, body: AddMemberRequest
):
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Check if the member exists
    member_response = supabase.auth.admin.get_user_by_id(body.member_uuid)
    if not member_response:
        raise HTTPException(status_code=404, detail="User not found")

    member = member_response.user

    # Check if the user is the group leader
    if x_user_uuid != group["leader"]:
        raise HTTPException(status_code=403, detail="User is not the group leader")

    # Check if the user is already a member of the group
    existing_membership = (
        supabase.table("UserGroup")
        .select("*")
        .eq("user", body.member_uuid)
        .eq("group", group_id)
        .execute()
        .data
    )
    if existing_membership:
        raise HTTPException(
            status_code=409, detail="User is already a member of this group"
        )

    # Insert membership for the new member
    new_membership = {
        "user": member.id,
        "group": group_id,
        "role": "member",
    }
    supabase.table("UserGroup").insert(new_membership).execute()

    # Fetch the updated user group with the new member
    members = (
        supabase.table("UserGroup").select("*").eq("group", group_id).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email,
            ),
            role=member["role"],
        )
        for member in members
    ]

    leader_user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    group["leader"] = User(uuid=leader_user.id, email=leader_user.email)
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.delete("/eat-together/{group_id}/remove-member/{member_id}", status_code=204)
def remove_member_from_group(
    x_user_uuid: Annotated[str, Header()], group_id: int, member_id: str
):
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Check if the member exists
    member = supabase.table("UserGroup").select("*").eq("id", member_id).execute().data
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    member = member[0]

    # Check if the user is the group leader
    if x_user_uuid != group["leader"]:
        raise HTTPException(status_code=403, detail="User is not the group leader")

    # Check if the member to be removed is not the group leader
    if member["user"] == group["leader"]:
        raise HTTPException(status_code=403, detail="Cannot remove the group leader")

    # Delete the membership
    supabase.table("UserGroup").delete().eq("user", member["user"]).eq(
        "group", group_id
    ).execute()

    # Fetch the updated user group with remaining members
    members = (
        supabase.table("UserGroup").select("*").eq("group", group_id).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email
                or "",
            ),
            role=member["role"],
        )
        for member in members
    ]

    leader_user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    group["leader"] = User(uuid=leader_user.id, email=leader_user.email or "")
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.put("/eat-together/{group_id}/update-guest")
def update_guest_preferences_restrictions(
    x_user_uuid: Annotated[str, Header()],
    group_id: int,
    body: UpdateGuestPreferenceRestrictionsRequest,
):
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Update the group guest preferences and restrictions
    group["guest_preferences"] = [
        [preference.model_dump() for preference in guest]
        for guest in body.guest_preferences
    ]

    group["guest_restrictions"] = [
        [restriction.model_dump() for restriction in guest]
        for guest in body.guest_restrictions
    ]

    supabase.table("EatTogetherGroup").update(group).eq("id", group_id).execute()

    # Fetch the updated user group with members and leader details
    members = (
        supabase.table("UserGroup").select("*").eq("group", group_id).execute().data
    )

    members = [
        GroupMember(
            id=member["id"],
            user=User(
                uuid=member["user"],
                email=supabase.auth.admin.get_user_by_id(member["user"]).user.email
                or "",
            ),
            role=member["role"],
        )
        for member in members
    ]

    leader_user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    group["leader"] = User(uuid=leader_user.id, email=leader_user.email or "")
    return EatTogetherMemberResponse(
        group=EatTogetherGroup(**group),
        members=members,
    )


@app.get("/eat-together/{group_id}/food-matches")
def get_food_matches(x_user_uuid: Annotated[str, Header()], group_id: int):
    """
    Randomly select a restaurant based on members of the group preferences and restrictions and also
    guest preferences and restrictions.
    """
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group[0]

    # Get all group members
    members = (
        supabase.table("UserGroup").select("*").eq("group", group_id).execute().data
    )
    member_uuids = [member["user"] for member in members]

    # Collect all preferences and restrictions from group members
    all_preferences = set()
    all_restrictions = set()
    for uuid in member_uuids:
        profile = supabase.table("Profile").select("*").eq("user", uuid).execute().data
        if profile:
            profile = profile[0]
            if profile.get("dietary_preferences"):
                all_preferences.update(
                    [p["name"].lower() for p in profile["dietary_preferences"]]
                )
            if profile.get("dietary_restrictions"):
                all_restrictions.update(
                    [r["name"].lower() for r in profile["dietary_restrictions"]]
                )

    # Add guest preferences and restrictions from group
    for guest_prefs in group.get("guest_preferences", []):
        all_preferences.update([p["name"].lower() for p in guest_prefs])
    for guest_rests in group.get("guest_restrictions", []):
        all_restrictions.update([r["name"].lower() for r in guest_rests])

    # Get all menus
    menus = supabase.table("Menu").select("*").execute().data
    matches_restaurant_menus = {}
    for menu in menus:
        main_ingredients = set(
            [i["name"].lower() for i in menu.get("main_ingredients", [])]
        )
        # Skip if any restriction is present
        if main_ingredients & all_restrictions:
            continue
        # Skip if none of the preferences are present
        if all_preferences and not (main_ingredients & all_preferences):
            continue
        if menu["restaurant"] not in matches_restaurant_menus:
            matches_restaurant_menus[menu["restaurant"]] = [menu]
        else:
            matches_restaurant_menus[menu["restaurant"]].append(menu)

    if not matches_restaurant_menus:
        raise HTTPException(status_code=404, detail="No matching restaurants found")

    # Get all matching restaurants
    restaurant_ids = list(matches_restaurant_menus.keys())
    restaurants = (
        supabase.table("Restaurant")
        .select("*")
        .in_("id", restaurant_ids)
        .execute()
        .data
    )

    response = []
    for restaurant in restaurants:
        for menu in matches_restaurant_menus[restaurant["id"]]:
            average_rating = (
                supabase.table("Rating")
                .select("rating_value")
                .eq("menu", menu["id"])
                .execute()
            ).data
            average_rating_value = (
                sum(rating["rating_value"] for rating in average_rating)
                / len(average_rating)
                if average_rating
                else 0
            )

            menu["average_rating"] = average_rating_value
            menu["restaurant"] = None

        restaurant["location"] = Location(
            **(
                supabase.table("Location")
                .select("*")
                .eq("id", restaurant["location"])
                .execute()
            ).data[0]
        )

        response.append(
            RestaurantMenuResponse(
                restaurant=Restaurant(**restaurant),
                menus=[
                    MenuResponse(**menu)
                    for menu in matches_restaurant_menus[restaurant["id"]]
                ],
                food_matches=len(matches_restaurant_menus[restaurant["id"]]),
            )
        )

    return response


@app.delete("/eat-together/{group_id}", status_code=204)
def delete_group(group_id: int):
    # Check if the group exists
    group = (
        supabase.table("EatTogetherGroup").select("*").eq("id", group_id).execute().data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Delete all memberships associated with the group
    supabase.table("UserGroup").delete().eq("group", group_id).execute()

    # Delete the group
    supabase.table("EatTogetherGroup").delete().eq("id", group_id).execute()

    return None


"""
User
"""


@app.get("/user")
def search_user(email: str):
    # Search for a user by email
    users = supabase.auth.admin.list_users()
    for user in users:
        if user.email and email in user.email:
            return User(uuid=user.id, email=user.email or "")
    raise HTTPException(status_code=404, detail="User not found")
