from fastapi import APIRouter

from app.perfil import salvar_perfil
from app.schemas import PerfilRequest, PerfilResponse

router = APIRouter(tags=["perfil"])


@router.post("/perfil", response_model=PerfilResponse)
@router.post("/perfil/", response_model=PerfilResponse, include_in_schema=False)
def cadastrar_perfil(dados: PerfilRequest) -> PerfilResponse:
    """Recebe os dados da tela Perfil, valida o contrato e persiste no MongoDB e Qdrant."""
    resultado = salvar_perfil(dados)
    return PerfilResponse(**resultado)
