from fastapi import APIRouter

from api.v1.clash import router as clash_router
from api.v1.douzero import router as douzero_router
from api.v1.ocr import router as ocr_router

api_router = APIRouter()

api_router.include_router(ocr_router, prefix="/ocr")
api_router.include_router(douzero_router, prefix="/douzero")
api_router.include_router(clash_router, prefix="/clash")
