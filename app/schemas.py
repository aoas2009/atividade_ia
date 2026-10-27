from typing import Literal

from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    """O que o navegador envia no POST /chat."""
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_id: str = Field(
        default="usuario_teste",
        min_length=1,
        max_length=128,
        description="Identificador estável do usuário entre sessões.",
        examples=["usuario_teste"],
    )
    pergunta: str = Field(..., min_length=1, max_length=4000, examples=["gastei 50 reais no mercado"])


class ChatResponse(BaseModel):
    """O que a API devolve no POST /chat."""
    resposta:         str
    agentes_chamados: list[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Resposta do encerramento de sessão."""
    session_id: str
    resumo:     str | None = None


class HealthCheck(BaseModel):
    """Resultado de uma dependência ou requisito da aplicação."""

    status: Literal["ok", "not_configured", "unavailable"]
    message: str


class HealthResponse(BaseModel):
    """Contrato do endpoint GET /health."""

    status: Literal["ok", "degraded"]
    checks: dict[str, HealthCheck]


_UUID_RE = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class PerfilRequest(BaseModel):
    """Contrato recebido pela rota POST /perfil."""

    user_id: str = Field(..., min_length=1, max_length=128, examples=["usuario_teste"])
    renda_mensal: float = Field(..., gt=0, le=10_000_000, examples=[4200.0])
    objetivo: str = Field(..., min_length=1, max_length=1000, examples=["juntar para viagem em dezembro"])
    tolerancia_risco: Literal["baixa", "media", "alta"] = Field(..., examples=["baixa"])
    preferencias: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["quero juntar para uma viagem a João Pessoa em dezembro; não quero investimento agressivo."],
    )

    @field_validator("user_id")
    @classmethod
    def user_id_nao_pode_ser_uuid_dinamico(cls, v: str) -> str:
        """Impede que um UUID gerado dinamicamente pelo frontend seja salvo como user_id de perfil."""
        import re
        if re.fullmatch(_UUID_RE, v):
            raise ValueError(
                "user_id não pode ser um UUID gerado automaticamente. "
                "Use um identificador estável (ex: 'joao.silva' ou 'usuario_teste')."
            )
        return v


class PerfilResponse(BaseModel):
    """Contrato retornado pela rota POST /perfil com os dados gravados."""

    user_id: str
    renda_mensal: float
    objetivo: str
    tolerancia_risco: Literal["baixa", "media", "alta"]
    preferencias: str
