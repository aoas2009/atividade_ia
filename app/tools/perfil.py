"""Ferramentas para o especialista financeiro acessar o perfil cadastrado do usuário."""

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.perfil import buscar_preferencias, obter_perfil


@tool
def consultar_perfil(config: RunnableConfig) -> str:
    """Consulta os dados estruturados do perfil cadastrado do usuário (renda mensal, objetivo e tolerância a risco).

    Use esta ferramenta sempre que precisar de dados cadastrais para calcular quanto guardar,
    avaliar o orçamento ou ancorar conselhos financeiros.
    """
    configuravel = (config or {}).get("configurable", {})
    user_id = configuravel.get("user_id") or "usuario_teste"

    perfil = obter_perfil(user_id)
    if not perfil:
        return (
            "Nenhum perfil cadastrado para este usuário. "
            "Oriente o usuário a acessar a tela de Perfil (perfil.html) para preencher seu cadastro."
        )

    return (
        f"Perfil financeiro do usuário:\n"
        f"- Renda mensal: R$ {perfil['renda_mensal']:.2f}\n"
        f"- Objetivo: {perfil['objetivo']}\n"
        f"- Tolerância a risco: {perfil['tolerancia_risco']}"
    )


@tool
def buscar_preferencias_perfil(busca: str, config: RunnableConfig) -> str:
    """Busca semanticamente nas preferências e restrições textuais livres do perfil do usuário.

    Use esta ferramenta quando a dúvida envolver tipos específicos de investimentos (ex: cripto,
    ações, renda fixa), restrições de liquidez, gostos ou preferências pessoais de aplicação.
    """
    configuravel = (config or {}).get("configurable", {})
    user_id = configuravel.get("user_id") or "usuario_teste"

    resultados = buscar_preferencias(user_id, busca=busca, limite=3)
    if not resultados:
        return "Nenhuma preferência cadastrada relevante encontrada para este usuário."

    textos = [r["preferencias"] for r in resultados if "preferencias" in r]
    if not textos:
        return "Nenhuma preferência cadastrada relevante encontrada para este usuário."

    linhas = [f"- {t}" for t in textos]
    return "Preferências do usuário:\n" + "\n".join(linhas)


TOOLS_PERFIL = [consultar_perfil, buscar_preferencias_perfil]
