from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/login")
async def autenticar():
    return {"mensagem": "você está autenticado"}