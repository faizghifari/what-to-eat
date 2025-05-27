from pydantic import BaseModel
from typing import List
from datetime import datetime


"""
Models
"""


class NameDescPair(BaseModel):
    name: str
    description: str


class User(BaseModel):
    uuid: str
    email: str


class GroupMember(BaseModel):
    id: int
    user: User
    role: str


class EatTogetherGroup(BaseModel):
    id: int
    group_name: str
    group_code: str
    guest_preferences: List[List[NameDescPair]]  # List of preferences for each guest
    guest_restrictions: List[List[NameDescPair]]  # List of restrictions for each guest
    leader: User
    created_at: datetime


class Restaurant(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    image_url: str = ""


"""
Requests
"""


class CreateEatTogetherGroupRequest(BaseModel):
    group_name: str
    guest_preferences: List[List[NameDescPair]] = []
    guest_restrictions: List[List[NameDescPair]] = []


class AddMemberRequest(BaseModel):
    member_uuid: str


class UpdateGuestPreferenceRestrictionsRequest(BaseModel):
    guest_preferences: List[List[NameDescPair]] = []
    guest_restrictions: List[List[NameDescPair]] = []


"""
Responses
"""


class EatTogetherMemberResponse(BaseModel):
    group: EatTogetherGroup
    members: List[GroupMember]
