"""Persistência de perfil estruturado no MongoDB e índice semântico no Qdrant."""

import uuid
from datetime import datetime, timezone
from pymongo import ASCENDING
from qdrant_client import models

from app.memory import get_db
from app.schemas import PerfilRequest
from app.vectorstore import (
    COLLECTION_PERFIL,
    garantir_collections,
    gerar_embedding,
    qdrant,
)

_indices_perfil_criados = False


def _get_col_perfis():
    """Garante a collection de perfis e seus índices no MongoDB."""
    global _indices_perfil_criados
    col_perfis = get_db()["perfis"]
    if not _indices_perfil_criados:
        col_perfis.create_index([("user_id", ASCENDING)], unique=True)
        _indices_perfil_criados = True
    return col_perfis


def salvar_perfil(dados: PerfilRequest) -> dict:
    """Grava o perfil estruturado no MongoDB e as preferências no Qdrant.

    Disparado pela rota POST /perfil no mesmo ponto. Atualiza sem duplicar cadastro
    e substitui o vetor anterior no Qdrant sem deixar dados antigos.
    """
    # 1. Gravar dados estruturados no MongoDB
    col_perfis = _get_col_perfis()
    agora = datetime.now(timezone.utc)
    documento = {
        "user_id": dados.user_id,
        "renda_mensal": float(dados.renda_mensal),
        "objetivo": dados.objetivo,
        "tolerancia_risco": dados.tolerancia_risco,
        "preferencias": dados.preferencias,
        "atualizado_em": agora,
    }
    col_perfis.update_one(
        {"user_id": dados.user_id},
        {"$set": documento},
        upsert=True,
    )

    # 2. Gravar vetor semântico das preferências no Qdrant
    garantir_collections()
    # Remove pontos antigos do usuário para que preferências anteriores não sobrevivam
    qdrant.delete(
        collection_name=COLLECTION_PERFIL,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=dados.user_id),
                )
            ]
        ),
    )

    ponto_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"perfil_{dados.user_id}"))
    vetor = gerar_embedding(dados.preferencias)
    qdrant.upsert(
        collection_name=COLLECTION_PERFIL,
        points=[
            models.PointStruct(
                id=ponto_id,
                vector=vetor,
                payload={
                    "user_id": dados.user_id,
                    "preferencias": dados.preferencias,
                    "atualizado_em": agora.isoformat(),
                },
            )
        ],
    )

    return {
        "user_id": dados.user_id,
        "renda_mensal": dados.renda_mensal,
        "objetivo": dados.objetivo,
        "tolerancia_risco": dados.tolerancia_risco,
        "preferencias": dados.preferencias,
    }


import re

def _is_browser_dinamico(user_id: str) -> bool:
    """Identifica se o user_id é um UUID ou ID de sessão gerado dinamicamente pelo frontend do chat."""
    if not user_id:
        return False
    return bool(re.match(r"^[0-9a-fA-F-]{36}$", user_id) or user_id.startswith("sess-"))


def obter_perfil(user_id: str) -> dict | None:
    """Consulta direta ao MongoDB para recuperar os dados estruturados do perfil."""
    col_perfis = _get_col_perfis()
    doc = col_perfis.find_one({"user_id": user_id})
    # Se o frontend do chat enviou um UUID dinâmico de localStorage e não possui perfil próprio,
    # vincula ao perfil estável "usuario_teste" cadastrado pela tela de Perfil.
    if not doc and _is_browser_dinamico(user_id):
        doc = col_perfis.find_one({"user_id": "usuario_teste"})
    if not doc:
        return None
    return {
        "user_id": doc["user_id"],
        "renda_mensal": float(doc["renda_mensal"]),
        "objetivo": doc["objetivo"],
        "tolerancia_risco": doc["tolerancia_risco"],
        "preferencias": doc.get("preferencias", ""),
    }


def buscar_preferencias(user_id: str, busca: str, limite: int = 3) -> list[dict]:
    """Busca semântica no Qdrant pelas preferências do usuário filtradas por user_id."""
    garantir_collections()
    vetor = gerar_embedding(busca)
    resultados = qdrant.query_points(
        collection_name=COLLECTION_PERFIL,
        query=vetor,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        ),
        limit=limite,
        with_payload=True,
    )
    if not resultados.points and _is_browser_dinamico(user_id):
        resultados = qdrant.query_points(
            collection_name=COLLECTION_PERFIL,
            query=vetor,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value="usuario_teste"),
                    )
                ]
            ),
            limit=limite,
            with_payload=True,
        )
    return [ponto.payload for ponto in resultados.points if ponto.payload]
