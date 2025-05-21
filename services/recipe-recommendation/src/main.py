import sys
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Recipe Recommendation Service")

from crud_endpoints import router as crud_router
from recommendation_endpoints import router as rec_router

app.include_router(crud_router)
app.include_router(rec_router)
