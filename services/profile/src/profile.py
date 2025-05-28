from supabase import Client
from enum import Enum
from json import dumps as to_json, loads as from_json
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from logging import getLogger, basicConfig, DEBUG

# Initialise logger
logger = getLogger(__name__)
LOGGER_PATH = "profile.log"
open(LOGGER_PATH,"w").close()
basicConfig(filename="profile.log", level=DEBUG)
logger.info("Started profile service.")

# Load environment variables
logger.debug("Loading environment variables...")
load_dotenv()
logger.debug("Finished.")

# Start server and Supabase client
logger.debug("Starting Supabase client..")
def init_client() -> Client:
    import os
    from supabase import create_client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_API_KEY")
    return create_client(url, key)

client: Client = init_client()
logger.debug("Client started successfully.")
logger.debug("Starting HTTP Server...")
server: FastAPI = FastAPI()
logger.debug("Server started successfully.")

# Define useful classes
logger.debug("Creating useful classes...")
class Field(Enum):
    Restrictions = "dietary_restrictions"
    Preferences = "dietary_preferences"
    Tools = "available_tools"
    Ingredients = "available_ingredients"
    Location = "current_location"
    
class ProfileEntry():
    name: str
    description: str

class Profile():
    dietary_restrictions: list[ProfileEntry]
    dietary_preferences: list[ProfileEntry]
    available_tools: list[ProfileEntry]
    available_ingredients: list[ProfileEntry]
    location_idx: int
logger.debug("Done.")

# Server functions
# GET requests ==================================================================================
# 
@server.get("/profile/profile")
async def get_profile(request: Request) -> Response:   
    logger.info("GET Profile requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")
    
        try:
            data = client.table("Profile").select([
                "," + field.value if i > 0 else field.value for i, field in enumerate(Field)
            ]).eq("user", uuid).execute().data

            if len(data) == 0:
                logger.info("No database hits")
                return Response(content="No DB hits.", status_code=204)
            
            logger.info("Request successful.")
            return Response(content=to_json(data[0]), status_code=200)
            
        except Exception as err:
            logger.error(f"Failed to get data from Supabase. Reason: {err}")
            
            return Response(content="Something went wrong!", status_code=500)
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)
        

# Get arbitrary field from Profile table
async def get_field(uuid: str, field: Field, client: Client) -> Response:
    logger.info(f"GET {field.value} requested for user {uuid}")
    try:
        data = client.table("Profile").select(field.value).eq("user", uuid).execute().data

        if len(data) == 0:
            logger.info("No database hits")
            return Response(content="No DB hits.", status_code=204)
        
        logger.info("Request successful.")
        return Response(content=to_json(data[0]), status_code=200)
        
    except Exception as err:
        logger.error(f"Failed to get data from Supabase. Reason: {err}")
        return Response(content="Something went wrong!", status_code=500)
    
@server.get("/profile/preferences")
async def get_preferences(request: Request) -> Response:
    logger.info("GET Preferences requested")
    logger.debug("Extracting data from HTTP Request")
    
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")
        return await get_field(uuid, Field.Preferences, client)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)
    
@server.get("/profile/restrictions")
async def get_restrictions(request: Request) -> Response:
    logger.info("GET Restrictions requested")
    logger.debug("Extracting data from HTTP Request")
    
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")
        return await get_field(uuid, Field.Restrictions, client)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)
    
@server.get("/profile/ingredients")
async def get_ingredients(request: Request) -> Response:
    logger.info("GET Ingredients requested")
    logger.debug("Extracting data from HTTP Request")
    
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")
        return await get_field(uuid, Field.Ingredients, client)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)
    
@server.get("/profile/tools")
async def get_tools(request: Request) -> Response:
    logger.info("GET Tools requested")
    logger.debug("Extracting data from HTTP Request")
    
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")
        return await get_field(uuid, Field.Tools, client)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)

@server.get("/profile/location")
async def get_location(request: Request) -> Response:
    logger.info("GET PREFERENCES requested")
    logger.debug("Extracting data from HTTP Request")
    
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        
        logger.info(f"GET current_location requested for user {uuid}")
        try:
            data = client.table("Profile").select(Field.Location.value).eq("user", uuid).execute().data

            if len(data) == 0:
                logger.info("No database hits")
                return Response(content="No DB hits.", status_code=204)
            
            logger.info("Request successful.")
            location_idx: int = next(iter(data[0].values()))
            print(location_idx)

            logger.debug("Fetching location from location table.")
            location = await get_from_location_table(location_idx)
            if type(location) is Response:
                return location
            else:
                return Response(content=to_json(location), status_code=200)
        
        except Exception as err:
            logger.error(f"Failed to get data from Supabase. Reason: {err}")
            return Response(content="Something went wrong!", status_code=500)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)

async def get_from_location_table(idx: int) -> str | Response:
    try:
        data = client.table("Location").select("*").eq("id", str(idx)).execute().data
        
        if len(data) == 0:
            logger.info("No database hits")
            return Response(content="No DB hits.", status_code=204)

        return data[0]

    except Exception as err:
            logger.error(f"Failed to get data from Supabase. Reason: {err}")
            return Response(content="Something went wrong!", status_code=500)

#=================================================================================================
# PUT requests
@server.put("/profile/profile")
async def edit_profile(request: Request) -> Response:   
    logger.info("EDIT Profile requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        profile: dict[str, str | int] = from_json(body_raw.decode("utf-8"))

        try:
            _success = client.table("Profile").update(profile).eq("user", uuid).execute()
            logger.info("Request successful.")
            return Response(status_code=200)
            
        except Exception as err:
            logger.error(f"Failed to get data from Supabase. Reason: {err}")
            return Response(content="Something went wrong!", status_code=500)
        
    except Exception as err:
        logger.error(f"Failed to get User ID from Request Header. Reason: {err}")
        return Response(content="Failed to retrieve user id", status_code=400)

async def edit_field(uuid: str, field: Field, value: str) -> Response:
    logger.debug(f"Editing field: {field.value} to {value}")
    try:
        _success = client.table("Profile").update({field.value: value}).eq('user',uuid).execute()
        logger.info("PUT request successful")
        return Response(status_code=200)
    except Exception as err:
        logger.error(f"failed to update value: {err}")
        return Response(content="Failed to update value", status_code=500)

@server.put("/profile/location")
async def edit_location(request: Request) -> Response:
    logger.info("EDIT Location requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        json_body: dict[str, str|int] = from_json(body_raw.decode("utf-8"))
        #logger.debug(f"Body: {json_body}")
        location_idx: str = str(json_body[Field.Location.value])
        logger.debug(f"Location idx: {type(location_idx)}")
        return await edit_field(uuid, Field.Location, location_idx)
        
    except Exception as err:
        logger.error(f"failed to update location. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)
    
@server.put("/profile/preferences")
async def edit_preferences(request: Request) -> Response:
    logger.info("EDIT Preferences requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        json_body: dict[str, str|int] = from_json(body_raw.decode("utf-8"))
        #logger.debug(f"Body: {json_body}")
        preferences: str = json_body[Field.Preferences.value]
        #logger.debug(f"Location idx: {type(location_idx)}")
        return await edit_field(uuid, Field.Preferences, preferences)
        
    except Exception as err:
        logger.error(f"failed to update preferences. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)


@server.put("/profile/restrictions")
async def edit_restrictions(request: Request) -> Response:
    logger.info("EDIT Restrictions requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        json_body: dict[str, str|int] = from_json(body_raw.decode("utf-8"))
        #logger.debug(f"Body: {json_body}")
        restrictions: str = json_body[Field.Restrictions.value]
        
        return await edit_field(uuid, Field.Restrictions, restrictions)
        
    except Exception as err:
        logger.error(f"failed to update restrictions. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)

@server.put("/profile/tools")
async def edit_tools(request: Request) -> Response:
    logger.info("EDIT Tools requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        json_body: dict[str, str|int] = from_json(body_raw.decode("utf-8"))
        #logger.debug(f"Body: {json_body}")
        tools: str = str(json_body[Field.Tools.value])
        return await edit_field(uuid, Field.Tools, tools)
        
    except Exception as err:
        logger.error(f"failed to update location. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)

@server.put("/profile/ingredients")
async def edit_ingredients(request: Request) -> Response:
    logger.info("EDIT Ingredientse requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        body_raw: bytes = await request.body()
        json_body: dict[str, str|int] = from_json(body_raw.decode("utf-8"))
        #logger.debug(f"Body: {json_body}")
        ingredients: str = str(json_body[Field.Ingredients.value])
        return await edit_field(uuid, Field.Ingredients, ingredients)
        
    except Exception as err:
        logger.error(f"failed to update location. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)

#=============================================================================================
# POST
@server.post("/profile/new")
async def new_user(request: Request) -> Response:
    logger.info("NEW user requested")

    logger.debug("Extracting data from HTTP Request")
    try:
        uuid: str = request.headers.get("X-User-Uuid")
        logger.debug("Success.")

        # Create new profile
        _result = client.table("Profile").insert({"user":uuid,Field.Location.value:16}).execute()

        return Response(status_code=200)
        
    except Exception as err:
        logger.error(f"failed to update location. Reason: {err}")
        return Response(content="Failed to update value", status_code=500)
    
