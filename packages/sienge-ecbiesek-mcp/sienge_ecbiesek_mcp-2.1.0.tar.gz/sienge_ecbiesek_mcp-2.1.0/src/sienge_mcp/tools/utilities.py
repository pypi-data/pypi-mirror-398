"""
Utilities Tools - Ferramentas de utilidade e teste
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


async def test_sienge_connection(make_request, config: Dict, _meta: Optional[Dict[str, Any]] = None) -> Dict:
    """Testa a conexão com a API do Sienge e retorna métricas básicas"""
    try:
        # Tentar endpoint mais simples primeiro
        result = await make_request("GET", "/customer-types")

        if result["success"]:
            auth_method = "Bearer Token" if config.get("SIENGE_API_KEY") else "Basic Auth"
            return {
                "success": True,
                "message": "✅ Conexão com API do Sienge estabelecida com sucesso!",
                "api_status": "Online",
                "auth_method": auth_method,
                "timestamp": datetime.now().isoformat(),
                "latency_ms": result.get("latency_ms"),
                "request_id": result.get("request_id"),
            }
        else:
            return {
                "success": False,
                "message": "❌ Falha ao conectar com API do Sienge",
                "error": result.get("error"),
                "details": result.get("message"),
                "timestamp": datetime.now().isoformat(),
                "latency_ms": result.get("latency_ms"),
                "request_id": result.get("request_id"),
            }
    except Exception as e:
        return {
            "success": False,
            "message": "❌ Erro ao testar conexão",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


async def list_sienge_entities() -> Dict:
    """
    Lista todas as entidades disponíveis no Sienge MCP para busca
    
    Retorna informações sobre os tipos de dados que podem ser consultados
    """
    entities = [
        {
            "type": "customers",
            "name": "Clientes",
            "description": "Clientes cadastrados no sistema",
            "search_fields": ["nome", "documento", "email"],
            "tools": ["get_sienge_customers", "search_sienge_data"]
        },
        {
            "type": "creditors", 
            "name": "Credores/Fornecedores",
            "description": "Fornecedores e credores cadastrados",
            "search_fields": ["nome", "documento"],
            "tools": ["get_sienge_creditors", "get_sienge_creditor_bank_info"]
        },
        {
            "type": "projects",
            "name": "Empreendimentos/Obras", 
            "description": "Projetos e obras cadastrados",
            "search_fields": ["código", "descrição", "nome"],
            "tools": ["get_sienge_projects", "get_sienge_enterprise_by_id"]
        },
        {
            "type": "bills",
            "name": "Títulos a Pagar",
            "description": "Contas a pagar e títulos financeiros",
            "search_fields": ["número", "credor", "valor"],
            "tools": ["get_sienge_bills"]
        },
        {
            "type": "purchase_orders",
            "name": "Pedidos de Compra",
            "description": "Pedidos de compra e solicitações",
            "search_fields": ["id", "descrição", "status"],
            "tools": ["get_sienge_purchase_orders", "get_sienge_purchase_requests"]
        },
        {
            "type": "invoices",
            "name": "Notas Fiscais",
            "description": "Notas fiscais de compra",
            "search_fields": ["número", "série", "fornecedor"],
            "tools": ["get_sienge_purchase_invoice"]
        },
        {
            "type": "stock",
            "name": "Estoque",
            "description": "Inventário e movimentações de estoque",
            "search_fields": ["centro_custo", "recurso"],
            "tools": ["get_sienge_stock_inventory", "get_sienge_stock_reservations"]
        },
        {
            "type": "financial",
            "name": "Financeiro",
            "description": "Contas a receber e movimentações financeiras",
            "search_fields": ["período", "cliente", "valor"],
            "tools": ["get_sienge_accounts_receivable"]
        }
    ]
    
    return {
        "success": True,
        "message": f"✅ {len(entities)} tipos de entidades disponíveis no Sienge",
        "entities": entities,
        "total_tools": sum(len(e["tools"]) for e in entities),
        "usage_example": {
            "search_all": "search_sienge_data('nome_cliente')",
            "search_specific": "search_sienge_data('nome_cliente', entity_type='customers')",
            "direct_access": "get_sienge_customers(search='nome_cliente')"
        }
    }


async def search_sienge_data(
    get_customers_func,
    get_creditors_func,
    get_projects_func,
    get_bills_func,
    get_purchase_orders_func,
    query: str,
    entity_type: Optional[str] = None,
    limit: Optional[int] = 20,
    filters: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Busca universal no Sienge - compatível com ChatGPT/OpenAI MCP
    
    ⚠️ IMPORTANTE: Para buscas mais eficientes e com maior volume de dados, 
    use as ferramentas do Supabase:
    - search_supabase_data() para busca universal no banco
    - query_supabase_database() para consultas diretas
    
    Permite buscar em múltiplas entidades do Sienge de forma unificada.
    
    Args:
        query: Termo de busca (nome, código, descrição, etc.)
        entity_type: Tipo de entidade (customers, creditors, projects, bills, purchase_orders, etc.)
        limit: Máximo de registros (padrão: 20, máximo: 100)
        filters: Filtros específicos por tipo de entidade
    """
    search_results = []
    limit = min(limit or 20, 100)
    
    # Se entity_type específico, buscar apenas nele
    if entity_type:
        result = await _search_specific_entity(
            get_customers_func, get_creditors_func, get_projects_func,
            get_bills_func, get_purchase_orders_func,
            entity_type, query, limit, filters or {}
        )
        if result["success"]:
            # Adicionar sugestão para usar Supabase se busca for específica
            if entity_type in ["customers", "creditors", "enterprises"] and len(result.get("data", [])) > 0:
                result["suggestion"] = f"💡 Para busca mais eficiente em {entity_type}, use: search_supabase_data(search_term='{query}', table_names=['{entity_type}'])"
            return result
        else:
            return {
                "success": False,
                "message": f"❌ Erro na busca em {entity_type}",
                "error": result.get("error"),
                "query": query,
                "entity_type": entity_type,
                "suggestion": f"💡 Tente usar: search_supabase_data(search_term='{query}', table_names=['{entity_type}'])"
            }
    
    # Busca universal em múltiplas entidades
    entities_to_search = [
        ("customers", "clientes"),
        ("creditors", "credores/fornecedores"), 
        ("projects", "empreendimentos/obras"),
        ("bills", "títulos a pagar"),
        ("purchase_orders", "pedidos de compra")
    ]
    
    total_found = 0
    
    for entity_key, entity_name in entities_to_search:
        try:
            entity_result = await _search_specific_entity(
                get_customers_func, get_creditors_func, get_projects_func,
                get_bills_func, get_purchase_orders_func,
                entity_key, query, min(5, limit), {}
            )
            if entity_result["success"] and entity_result.get("count", 0) > 0:
                search_results.append({
                    "entity_type": entity_key,
                    "entity_name": entity_name,
                    "count": entity_result["count"],
                    "results": entity_result["data"][:5],  # Limitar a 5 por entidade na busca universal
                    "has_more": entity_result["count"] > 5
                })
                total_found += entity_result["count"]
        except Exception:
            # Continuar com outras entidades se uma falhar
            continue
    
    if search_results:
        return {
            "success": True,
            "message": f"✅ Busca '{query}' encontrou resultados em {len(search_results)} entidades (total: {total_found} registros)",
            "query": query,
            "total_entities": len(search_results),
            "total_records": total_found,
            "results_by_entity": search_results,
            "suggestion": "Use entity_type para buscar especificamente em uma entidade e obter mais resultados",
            "supabase_suggestion": f"💡 Para busca mais eficiente e completa, use: search_supabase_data(search_term='{query}')"
        }
    else:
        return {
            "success": False,
            "message": f"❌ Nenhum resultado encontrado para '{query}'",
            "query": query,
            "searched_entities": [name for _, name in entities_to_search],
            "suggestion": "Tente termos mais específicos ou use os tools específicos de cada entidade",
            "supabase_suggestion": f"💡 Para busca mais eficiente, use: search_supabase_data(search_term='{query}')"
        }


async def _search_specific_entity(
    get_customers_func,
    get_creditors_func,
    get_projects_func,
    get_bills_func,
    get_purchase_orders_func,
    entity_type: str, 
    query: str, 
    limit: int, 
    filters: Dict
) -> Dict:
    """Função auxiliar para buscar em uma entidade específica"""
    
    if entity_type == "customers":
        result = await get_customers_func(limit=limit, search=query)
        if result["success"]:
            return {
                "success": True,
                "data": result["customers"],
                "count": result["count"],
                "entity_type": "customers"
            }
    
    elif entity_type == "creditors":
        result = await get_creditors_func(limit=limit, search=query)
        if result["success"]:
            return {
                "success": True,
                "data": result["creditors"],
                "count": result["count"],
                "entity_type": "creditors"
            }
    
    elif entity_type == "projects" or entity_type == "enterprises":
        # Para projetos, usar filtros mais específicos se disponível
        company_id = filters.get("company_id")
        result = await get_projects_func(limit=limit, company_id=company_id)
        if result["success"]:
            # Filtrar por query se fornecida
            projects = result["enterprises"]
            if query:
                projects = [
                    p for p in projects 
                    if query.lower() in str(p.get("description", "")).lower() 
                    or query.lower() in str(p.get("name", "")).lower()
                    or query.lower() in str(p.get("code", "")).lower()
                ]
            return {
                "success": True,
                "data": projects,
                "count": len(projects),
                "entity_type": "projects"
            }
    
    elif entity_type == "bills":
        # Para títulos, usar data padrão se não especificada
        start_date = filters.get("start_date")
        end_date = filters.get("end_date") 
        result = await get_bills_func(
            start_date=start_date, 
            end_date=end_date, 
            limit=limit
        )
        if result["success"]:
            return {
                "success": True,
                "data": result["bills"],
                "count": result["count"],
                "entity_type": "bills"
            }
    
    elif entity_type == "purchase_orders":
        result = await get_purchase_orders_func(limit=limit)
        if result["success"]:
            orders = result["purchase_orders"]
            # Filtrar por query se fornecida
            if query:
                orders = [
                    o for o in orders 
                    if query.lower() in str(o.get("description", "")).lower()
                    or query.lower() in str(o.get("id", "")).lower()
                ]
            return {
                "success": True,
                "data": orders,
                "count": len(orders),
                "entity_type": "purchase_orders"
            }
    
    # Se chegou aqui, entidade não suportada ou erro
    return {
        "success": False,
        "error": f"Entidade '{entity_type}' não suportada ou erro na busca",
        "supported_entities": ["customers", "creditors", "projects", "bills", "purchase_orders"]
    }


async def get_sienge_data_paginated(
    get_customers_func,
    get_creditors_func,
    get_projects_func,
    get_bills_func,
    entity_type: str,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None
) -> Dict:
    """
    Busca dados do Sienge com paginação avançada - compatível com ChatGPT
    
    Args:
        entity_type: Tipo de entidade (customers, creditors, projects, bills, etc.)
        page: Número da página (começando em 1)
        page_size: Registros por página (máximo 50)
        filters: Filtros específicos da entidade
        sort_by: Campo para ordenação (se suportado)
    """
    page_size = min(page_size, 50)
    offset = (page - 1) * page_size
    
    filters = filters or {}
    
    # Mapear para os tools existentes com offset
    if entity_type == "customers":
        search = filters.get("search")
        customer_type_id = filters.get("customer_type_id")
        result = await get_customers_func(
            limit=page_size,
            offset=offset, 
            search=search,
            customer_type_id=customer_type_id
        )
        
    elif entity_type == "creditors":
        search = filters.get("search")
        result = await get_creditors_func(
            limit=page_size,
            offset=offset,
            search=search
        )
        
    elif entity_type == "projects":
        result = await get_projects_func(
            limit=page_size,
            offset=offset,
            company_id=filters.get("company_id"),
            enterprise_type=filters.get("enterprise_type")
        )
        
    elif entity_type == "bills":
        result = await get_bills_func(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            creditor_id=filters.get("creditor_id"),
            status=filters.get("status"),
            limit=page_size
        )
        
    else:
        return {
            "success": False,
            "message": f"❌ Tipo de entidade '{entity_type}' não suportado para paginação",
            "supported_types": ["customers", "creditors", "projects", "bills"]
        }
    
    if result["success"]:
        # Calcular informações de paginação
        total_count = result.get("total_count", result.get("count", 0))
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        return {
            "success": True,
            "message": f"✅ Página {page} de {total_pages} - {entity_type}",
            "data": result.get(entity_type, result.get("data", [])),
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_records": total_count,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            },
            "entity_type": entity_type,
            "filters_applied": filters
        }
    
    return result
