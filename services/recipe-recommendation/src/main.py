import sys
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from crud_endpoints import router as crud_router
from recommendation_endpoints import router as rec_router

app = FastAPI(title="Recipe Recommendation Service")

app.include_router(crud_router)
app.include_router(rec_router)
