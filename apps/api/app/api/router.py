from fastapi import APIRouter

from app.api import auth, boe, comps, deals, full_underwriting, portfolio, risk, workspaces

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(deals.router)
api_router.include_router(boe.router)
api_router.include_router(comps.router)
api_router.include_router(full_underwriting.router)
api_router.include_router(portfolio.router)
api_router.include_router(risk.router)
