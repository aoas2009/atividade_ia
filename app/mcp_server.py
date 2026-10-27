import sys
from pathlib import Path
from typing import Annotated, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from app.tools.financeiro import (
    add_transaction as _add_transaction,
    daily_balance as _daily_balance,
    query_transactions as _query_transactions,
    total_balance as _total_balance,
    update_transaction as _update_transaction,
)
from app.config import DATABASE_URL


mcp = MCPServer(
    name="assessor-financeiro",
    version="1.0.0",
    instructions=(
        "Ferramentas financeiras do Assessor.AI. "
        "Use para registrar transações, consultar histórico e calcular saldos."
    ),
)

LEITURA = ToolAnnotations(readOnlyHint=True)
ESCRITA = ToolAnnotations(readOnlyHint=False, destructiveHint=False)


# ---------------------------------------------------------------------------
# total_balance
# ---------------------------------------------------------------------------

@mcp.tool(
    name="total_balance",
    title="Saldo total",
    description="Saldo de todo o histórico: receitas menos despesas.",
    annotations=LEITURA,
)
def total_balance() -> dict[str, Any]:
    return _total_balance.invoke({})


# ---------------------------------------------------------------------------
# daily_balance
# ---------------------------------------------------------------------------

@mcp.tool(
    name="daily_balance",
    title="Saldo do dia",
    description="Calcula o saldo (entradas - despesas) de uma data específica.",
    annotations=LEITURA,
)
def daily_balance(
    date: Annotated[str, Field(description="Data no formato YYYY-MM-DD.")],
) -> dict[str, Any]:
    return _daily_balance.invoke({"date": date})


# ---------------------------------------------------------------------------
# query_transactions
# ---------------------------------------------------------------------------

@mcp.tool(
    name="query_transactions",
    title="Listar transações",
    description="Lista as transações mais recentes, com filtros opcionais por data e tipo.",
    annotations=LEITURA,
)
def query_transactions(
    limit: Annotated[int, Field(description="Número máximo de registros a retornar.", ge=1, le=200)] = 10,
    date: Annotated[Optional[str], Field(description="Filtrar por dia (YYYY-MM-DD) ou mês (YYYY-MM).")] = None,
    type_filter: Annotated[Optional[str], Field(description="Filtrar por tipo: INCOME | EXPENSES | TRANSFER.")] = None,
) -> dict[str, Any]:
    return _query_transactions.invoke({"limit": limit, "date": date, "type_filter": type_filter})


# ---------------------------------------------------------------------------
# add_transaction
# ---------------------------------------------------------------------------

@mcp.tool(
    name="add_transaction",
    title="Registrar transação",
    description="Registra uma nova transação financeira na tabela transactions.",
    annotations=ESCRITA,
)
def add_transaction(
    amount: Annotated[float, Field(description="Valor da transação (sempre positivo).", gt=0)],
    source_text: Annotated[str, Field(description="Texto original do usuário descrevendo a transação.")],
    occurred_at: Annotated[
        Optional[str],
        Field(description="Timestamp ISO 8601 do ocorrido; se ausente, usa o momento atual."),
    ] = None,
    type_name: Annotated[
        Optional[str],
        Field(description="Tipo: INCOME | EXPENSES | TRANSFER. Padrão: EXPENSES."),
    ] = None,
    category_name: Annotated[
        Optional[str],
        Field(description="Categoria em pt-BR (ex: comida, transporte, saúde)."),
    ] = None,
    description: Annotated[Optional[str], Field(description="Descrição adicional opcional.")] = None,
    payment_method: Annotated[Optional[str], Field(description="Forma de pagamento (ex: pix, cartão).")] = None,
) -> dict[str, Any]:
    return _add_transaction.invoke({
        "amount": amount,
        "source_text": source_text,
        "occurred_at": occurred_at,
        "type_name": type_name,
        "category_name": category_name,
        "description": description,
        "payment_method": payment_method,
    })


# ---------------------------------------------------------------------------
# update_transaction
# ---------------------------------------------------------------------------

@mcp.tool(
    name="update_transaction",
    title="Atualizar transação",
    description=(
        "Atualiza uma transação existente. "
        "Se 'id' for informado, atualiza diretamente. "
        "Caso contrário, localiza pela combinação de match_text + date_local."
    ),
    annotations=ESCRITA,
)
def update_transaction(
    id: Annotated[Optional[int], Field(description="ID da transação a atualizar.")] = None,
    match_text: Annotated[
        Optional[str],
        Field(description="Texto para localizar a transação quando 'id' não for informado."),
    ] = None,
    date_local: Annotated[
        Optional[str],
        Field(description="Data local YYYY-MM-DD (America/Sao_Paulo) usada junto com match_text."),
    ] = None,
    amount: Annotated[Optional[float], Field(description="Novo valor.", gt=0)] = None,
    type_name: Annotated[
        Optional[str],
        Field(description="Novo tipo: INCOME | EXPENSES | TRANSFER."),
    ] = None,
    category_name: Annotated[Optional[str], Field(description="Nova categoria (nome).")] = None,
    description: Annotated[Optional[str], Field(description="Nova descrição.")] = None,
    payment_method: Annotated[Optional[str], Field(description="Novo meio de pagamento.")] = None,
    occurred_at: Annotated[Optional[str], Field(description="Novo timestamp ISO 8601.")] = None,
) -> dict[str, Any]:
    return _update_transaction.invoke({
        "id": id,
        "match_text": match_text,
        "date_local": date_local,
        "amount": amount,
        "type_name": type_name,
        "category_name": category_name,
        "description": description,
        "payment_method": payment_method,
        "occurred_at": occurred_at,
    })


if __name__ == "__main__":
    if not DATABASE_URL:
        print("[assessor-financeiro] DATABASE_URL ausente no .env", file=sys.stderr)

    mcp.run(transport="stdio")
