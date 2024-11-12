from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import FileResponse

load_dotenv()  # TODO: Mejorar

from app.api.routes import router_api  # Importa el enrutador central que agrupa todas las rutas

# Crear una sola instancia de FastAPI
app = FastAPI(title="Panel A.C.I.B API DATABASE")


# Configuración de CORS
origins = [
    "http://localhost:5173",  # Permitir localhost:5173
    "*",# Puedes agregar más orígenes aquí si es necesario
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # O usa ["*"] para permitir todos
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")  # Ajusta la ruta según tu estructura

# Incluir todas las rutas centralizadas en router_api
app.include_router(router_api)

# Ruta de prueba para la raíz
@app.get("/")
async def root():
    return {"message": "Welcome to ProcemonDash API"}
