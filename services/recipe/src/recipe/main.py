from fastapi import FastAPI

from recipe.crud_endpoints import router as crud_router
from recipe.recommendation_endpoints import router as rec_router

app = FastAPI(title="Recipe Recommendation Service")

app.include_router(rec_router)
app.include_router(crud_router)
