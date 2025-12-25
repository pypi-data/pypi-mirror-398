"""
Master Data Tools - Ferramentas de cadastros básicos
Clientes, Credores, Projetos/Obras, Unidades, etc.
"""

from typing import Dict, List, Optional, Any


# Será registrado como @mcp.tool no server.py
async def get_sienge_customers(
    make_request, cache_get, cache_set, fetch_all_func,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    search: Optional[str] = None,
    customer_type_id: Optional[str] = None,
    fetch_all: Optional[bool] = False,
    max_records: Optional[int] = None,
) -> Dict:
    """Busca clientes no Sienge com filtros"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}

    if search:
        params["search"] = search
    if customer_type_id:
        params["customer_type_id"] = customer_type_id

    cache_key = f"customers:{limit}:{offset}:{search}:{customer_type_id}"
    try:
        cached = cache_get(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    if fetch_all:
        items = await fetch_all_func("/customers", params=params, page_size=200, max_records=max_records)
        if isinstance(items, dict) and not items.get("success", True):
            return {"success": False, "error": items.get("error"), "message": items.get("message")}

        customers = items
        response = {
            "success": True,
            "message": f"✅ Encontrados {len(customers)} clientes (fetch_all)",
            "customers": customers,
            "count": len(customers),
            "filters_applied": params,
        }
        try:
            cache_set(cache_key, response, ttl=30)
        except Exception:
            pass
        return response

    result = await make_request("GET", "/customers", params=params)

    if result["success"]:
        data = result["data"]
        customers = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(customers))

        response = {
            "success": True,
            "message": f"✅ Encontrados {len(customers)} clientes (total: {total_count})",
            "customers": customers,
            "count": len(customers),
            "filters_applied": params,
        }
        try:
            cache_set(cache_key, response, ttl=30)
        except Exception:
            pass
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar clientes",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_customer_types(make_request) -> Dict:
    """Lista tipos de clientes disponíveis"""
    result = await make_request("GET", "/customer-types")

    if result["success"]:
        data = result["data"]
        types = data.get("results", []) if isinstance(data, dict) else data
        return {
            "success": True,
            "message": f"✅ Encontrados {len(types)} tipos de cliente",
            "customer_types": types,
            "count": len(types),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar tipos de cliente",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_payment_categories(make_request, cache_get, cache_set) -> Dict:
    """Lista planos financeiros (payment categories) disponíveis no Sienge"""
    try:
        cached = cache_get("payment_categories")
        if cached:
            return cached
    except Exception:
        pass

    result = await make_request("GET", "/payment-categories")

    if result["success"]:
        data = result["data"]
        categories = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(categories))

        response = {
            "success": True,
            "message": f"✅ Encontrados {len(categories)} planos financeiros (total: {total_count})",
            "payment_categories": categories,
            "count": len(categories),
        }
        try:
            cache_set("payment_categories", response, ttl=300)
        except Exception:
            pass
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar planos financeiros",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_creditors(
    make_request, cache_get, cache_set, fetch_all_func,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    search: Optional[str] = None,
    fetch_all: Optional[bool] = False,
    max_records: Optional[int] = None,
) -> Dict:
    """Busca credores/fornecedores"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    if search:
        params["search"] = search

    cache_key = f"creditors:{limit}:{offset}:{search}:{fetch_all}:{max_records}"
    try:
        cached = cache_get(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    if fetch_all:
        items = await fetch_all_func("/creditors", params=params, page_size=200, max_records=max_records)
        if isinstance(items, dict) and not items.get("success", True):
            return {"success": False, "error": items.get("error"), "message": items.get("message")}

        creditors = items
        response = {
            "success": True,
            "message": f"✅ Encontrados {len(creditors)} credores (fetch_all)",
            "creditors": creditors,
            "count": len(creditors),
        }
        try:
            cache_set(cache_key, response, ttl=30)
        except Exception:
            pass
        return response

    result = await make_request("GET", "/creditors", params=params)

    if result["success"]:
        data = result["data"]
        creditors = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(creditors))

        response = {
            "success": True,
            "message": f"✅ Encontrados {len(creditors)} credores (total: {total_count})",
            "creditors": creditors,
            "count": len(creditors),
        }
        try:
            cache_set(cache_key, response, ttl=30)
        except Exception:
            pass
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar credores",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_creditor_bank_info(make_request, creditor_id: str) -> Dict:
    """Consulta informações bancárias de um credor"""
    result = await make_request("GET", f"/creditors/{creditor_id}/bank-informations")

    if result["success"]:
        return {
            "success": True,
            "message": f"✅ Informações bancárias do credor {creditor_id}",
            "creditor_id": creditor_id,
            "bank_info": result["data"],
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar info bancária do credor {creditor_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_projects(
    make_request,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    company_id: Optional[int] = None,
    enterprise_type: Optional[int] = None,
    receivable_register: Optional[str] = None,
    only_buildings_enabled: Optional[bool] = False,
) -> Dict:
    """Busca empreendimentos/obras no Sienge"""
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}

    if company_id:
        params["companyId"] = company_id
    if enterprise_type:
        params["type"] = enterprise_type
    if receivable_register:
        params["receivableRegister"] = receivable_register
    if only_buildings_enabled:
        params["onlyBuildingsEnabledForIntegration"] = only_buildings_enabled

    result = await make_request("GET", "/enterprises", params=params)

    if result["success"]:
        data = result["data"]
        enterprises = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontrados {len(enterprises)} empreendimentos",
            "enterprises": enterprises,
            "count": len(enterprises),
            "metadata": metadata,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar empreendimentos",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_project_by_id(make_request, project_id: int) -> Dict:
    """Busca um empreendimento/projeto específico por ID"""
    result = await make_request("GET", f"/enterprises/{project_id}")

    if result["success"]:
        data = result["data"]
        return {
            "success": True,
            "message": f"✅ Empreendimento {project_id} encontrado",
            "enterprise": data,
            "project": data,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar empreendimento {project_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_enterprise_by_id(make_request, enterprise_id: int) -> Dict:
    """Busca um empreendimento específico por ID no Sienge"""
    result = await make_request("GET", f"/enterprises/{enterprise_id}")

    if result["success"]:
        return {"success": True, "message": f"✅ Empreendimento {enterprise_id} encontrado", "enterprise": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao buscar empreendimento {enterprise_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_enterprise_groupings(make_request, enterprise_id: int) -> Dict:
    """Busca agrupamentos de unidades de um empreendimento específico"""
    result = await make_request("GET", f"/enterprises/{enterprise_id}/groupings")

    if result["success"]:
        groupings = result["data"]
        return {
            "success": True,
            "message": f"✅ Agrupamentos do empreendimento {enterprise_id} encontrados",
            "groupings": groupings,
            "count": len(groupings) if isinstance(groupings, list) else 0,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar agrupamentos do empreendimento {enterprise_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_cost_centers(
    make_request,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
) -> Dict:
    """Busca centros de custo no Sienge ordenados pelo código id"""
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}
    
    result = await make_request("GET", "/cost-centers", params=params)
    
    if result["success"]:
        data = result["data"]
        cost_centers = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(cost_centers))
        
        return {
            "success": True,
            "message": f"✅ Encontrados {len(cost_centers)} centros de custo (total: {total_count})",
            "cost_centers": cost_centers,
            "count": len(cost_centers),
            "total_count": total_count,
            "metadata": metadata,
        }
    
    return {
        "success": False,
        "message": "❌ Erro ao buscar centros de custo",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_units(make_request, limit: Optional[int] = 50, offset: Optional[int] = 0) -> Dict:
    """Consulta unidades cadastradas no Sienge"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    result = await make_request("GET", "/units", params=params)

    if result["success"]:
        data = result["data"]
        units = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(units))

        return {
            "success": True,
            "message": f"✅ Encontradas {len(units)} unidades (total: {total_count})",
            "units": units,
            "count": len(units),
            "metadata": metadata,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar unidades",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_unit_cost_tables(
    make_request,
    unit_id: int,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict:
    """Consulta tabelas de custos de uma unidade"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    result = await make_request("GET", f"/units/{unit_id}/cost-tables", params=params)

    if result["success"]:
        data = result["data"]
        tables = data.get("results", []) if isinstance(data, dict) else data
        return {
            "success": True,
            "message": f"✅ Tabelas de custos da unidade {unit_id}",
            "unit_id": unit_id,
            "cost_tables": tables,
            "count": len(tables) if isinstance(tables, list) else 0,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar tabelas de custos da unidade {unit_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }
