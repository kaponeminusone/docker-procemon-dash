from fastapi import APIRouter 
from app.api.v1 import auth, configuration, stadistics, users, inputs, indicators, process, send as email, latex, logs, execution

router_api = APIRouter()

# Incluye las rutas de users
router_api.include_router(auth.router, prefix="/auth", tags=["Auth"])
router_api.include_router(users.router, prefix="/users", tags=["Users"])
router_api.include_router(inputs.router, prefix="/inputs", tags=["Inputs"])
router_api.include_router(indicators.router, prefix="/indicators", tags=["Indicators"])
router_api.include_router(process.router, prefix="/process", tags=["Process"])
router_api.include_router(execution.router, prefix="/execution", tags=["Execution"])
router_api.include_router(logs.router, prefix="/logs", tags=["Logs"])
router_api.include_router(stadistics.router, prefix="/stadistics", tags=["Stadistics"])
router_api.include_router(email.router, prefix="/email", tags=["Email"])
router_api.include_router(latex.router, prefix="/latex", tags=["LaTeX"])
router_api.include_router(configuration.router)
