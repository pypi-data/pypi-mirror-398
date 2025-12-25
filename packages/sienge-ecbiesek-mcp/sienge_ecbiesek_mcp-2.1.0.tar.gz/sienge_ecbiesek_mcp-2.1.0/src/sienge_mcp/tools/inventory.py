"""
Inventory Tools - Ferramentas de estoque
Inventário, Reservas, Movimentações
"""

from typing import Dict, List, Optional, Any


# Este módulo contém ~4 tools relacionadas a estoque:
# - get_sienge_stock_inventory
# - get_sienge_stock_reservations
# - get_sienge_stock_movements (se existir)
# - Outras tools de estoque

# As funções serão movidas do server.py mantendo a mesma lógica
# mas recebendo make_request como parâmetro (dependency injection)


async def get_sienge_stock_inventory(
    make_request,
    cost_center_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    limit: Optional[int] = 100
) -> Dict:
    """Consulta inventário de estoque por centro de custo"""
    if not cost_center_id:
        return {
            "success": False,
            "message": "❌ cost_center_id é obrigatório para consultar inventário de estoque",
            "error": "MISSING_PARAMETER",
            "suggestion": "Use get_sienge_cost_centers() para listar os centros de custo disponíveis"
        }
    
    if resource_id:
        endpoint = f"/stock-inventories/{cost_center_id}/items/{resource_id}"
        params = None
    else:
        endpoint = f"/stock-inventories/{cost_center_id}/items"
        params = {"limit": min(limit or 100, 200)} if limit else None

    result = await make_request("GET", endpoint, params=params)

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data
        count = len(items) if isinstance(items, list) else 1

        return {
            "success": True,
            "message": f"✅ Inventário do centro de custo {cost_center_id}",
            "cost_center_id": cost_center_id,
            "inventory": items,
            "count": count,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao consultar estoque do centro {cost_center_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_stock_reservations(make_request, limit: Optional[int] = 50) -> Dict:
    """Lista reservas de estoque"""
    params = {"limit": min(limit or 50, 200)}
    result = await make_request("GET", "/stock-reservations", params=params)

    if result["success"]:
        data = result["data"]
        reservations = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(reservations)} reservas de estoque",
            "reservations": reservations,
            "count": len(reservations),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar reservas de estoque",
        "error": result.get("error"),
        "details": result.get("message"),
    }
