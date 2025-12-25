"""
Purchases Tools - Ferramentas de compras
Pedidos de Compra, Notas Fiscais, Solicitações, Validações
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid
import logging

# Logger
log = logging.getLogger("sienge_mcp.purchases")

# Helper para garantir que logger tenha método info
def _ensure_logger(logger):
    """Garante que logger tenha método info"""
    if hasattr(logger, 'info'):
        return logger
    # Se for dict ou não tiver info, usar log padrão
    return log


# ============ PEDIDOS DE COMPRA ============

async def get_sienge_purchase_orders(
    make_request,
    cache_get,
    cache_set,
    purchase_order_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    authorized: Optional[bool] = None,
    supplier_id: Optional[int] = None,
    building_id: Optional[int] = None,
    buyer_id: Optional[str] = None,
    status_approval: Optional[str] = None,
    consistency: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
) -> Dict:
    """
    Consulta pedidos de compra com filtros avançados.
    
    Parâmetros conforme documentação da API:
    - purchase_order_id: ID do pedido específico (se fornecido, retorna apenas esse pedido)
      ⚠️ NOTA: O número formatado do pedido (ex: "3.717.357" no DANFE) pode ser diferente do ID interno do Sienge.
      Se não encontrar pelo número formatado, tente buscar no Supabase ou use filtros de data/fornecedor.
    - start_date: Data de início (formato yyyy-MM-dd)
    - end_date: Data de fim (formato yyyy-MM-dd)
    - status: PENDING, PARTIALLY_DELIVERED, FULLY_DELIVERED, CANCELED
    - authorized: true/false para pedidos autorizados/desautorizados
    - supplier_id: ID do fornecedor
    - building_id: ID da obra
    - buyer_id: ID do comprador (usuário do Sienge)
    - status_approval: DISAPPROVED, APPROVED
    - consistency: IN_INCLUSION, CONSISTENT, INCONSISTENT
    - limit: Máximo de resultados (padrão: 100, máx: 200)
    - offset: Deslocamento na lista (padrão: 0)
    """
    if purchase_order_id:
        # Cache para buscas por ID específico (TTL curto, pois são dados específicos)
        cache_key = f"purchase_order:{purchase_order_id}"
        try:
            cached = cache_get(cache_key)
            if cached:
                return cached
        except Exception:
            pass
        
        result = await make_request("GET", f"/purchase-orders/{purchase_order_id}")
        if result["success"]:
            response = {
                "success": True,
                "message": f"✅ Pedido {purchase_order_id} encontrado",
                "purchase_order": result["data"]
            }
            try:
                cache_set(cache_key, response, ttl=60)  # Cache por 1 minuto
            except Exception:
                pass
            return response
        
        # Se não encontrou, sugerir alternativas
        return {
            "success": False,
            "message": f"❌ Pedido {purchase_order_id} não encontrado",
            "error": result.get("error"),
            "details": result.get("message"),
            "suggestion": f"💡 O número '{purchase_order_id}' pode ser um número formatado diferente do ID interno do Sienge. Tente:"
                         f"\n1. Buscar no Supabase: search_supabase_data(search_term='{purchase_order_id}', table_names=['purchase_orders'])"
                         f"\n2. Usar filtros de data/fornecedor: get_sienge_purchase_orders(start_date='...', end_date='...', supplier_id=...)",
        }

    params = {"limit": min(limit or 100, 200), "offset": offset or 0}
    
    # Validar e formatar datas
    if start_date:
        start_date_str = str(start_date).strip()
        
        # Workaround: Aceitar formato sem hífens (yyyyMMdd) caso o MCP esteja truncando
        if len(start_date_str) == 8 and start_date_str.isdigit():
            # Formato yyyyMMdd (ex: 20251215)
            params["startDate"] = f"{start_date_str[:4]}-{start_date_str[4:6]}-{start_date_str[6:8]}"
        elif len(start_date_str) >= 10 and start_date_str.count('-') >= 2:
            # Formato yyyy-MM-dd (ex: 2025-12-15)
            parts = start_date_str.split('-')
            if len(parts) >= 3 and len(parts[0]) == 4:
                params["startDate"] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            else:
                params["startDate"] = start_date_str[:10]
        elif len(start_date_str) == 4:
            # Se apenas o ano foi passado, retornar erro
            return {
                "success": False,
                "message": f"❌ Data incompleta recebida para start_date: '{start_date}'. Use o formato completo yyyy-MM-dd (ex: 2025-12-15) ou yyyyMMdd (ex: 20251215). Parece que apenas o ano foi passado.",
                "error": "INVALID_DATE_FORMAT",
                "received": start_date,
                "type": type(start_date).__name__,
                "suggestion": "Tente usar o formato sem hífens: yyyyMMdd (ex: 20251215) se o problema persistir"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Formato de data inválido para start_date: '{start_date}'. Use o formato yyyy-MM-dd (ex: 2025-12-15) ou yyyyMMdd (ex: 20251215)",
                "error": "INVALID_DATE_FORMAT",
                "received": start_date,
                "type": type(start_date).__name__
            }
    
    if end_date:
        end_date_str = str(end_date).strip()
        
        # Workaround: Aceitar formato sem hífens (yyyyMMdd) caso o MCP esteja truncando
        if len(end_date_str) == 8 and end_date_str.isdigit():
            # Formato yyyyMMdd (ex: 20251219)
            params["endDate"] = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:8]}"
        elif len(end_date_str) >= 10 and end_date_str.count('-') >= 2:
            # Formato yyyy-MM-dd (ex: 2025-12-19)
            parts = end_date_str.split('-')
            if len(parts) >= 3 and len(parts[0]) == 4:
                params["endDate"] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            else:
                params["endDate"] = end_date_str[:10]
        elif len(end_date_str) == 4:
            # Se apenas o ano foi passado, retornar erro
            return {
                "success": False,
                "message": f"❌ Data incompleta recebida para end_date: '{end_date}'. Use o formato completo yyyy-MM-dd (ex: 2025-12-19) ou yyyyMMdd (ex: 20251219). Parece que apenas o ano foi passado.",
                "error": "INVALID_DATE_FORMAT",
                "received": end_date,
                "type": type(end_date).__name__,
                "suggestion": "Tente usar o formato sem hífens: yyyyMMdd (ex: 20251219) se o problema persistir"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Formato de data inválido para end_date: '{end_date}'. Use o formato yyyy-MM-dd (ex: 2025-12-19) ou yyyyMMdd (ex: 20251219)",
                "error": "INVALID_DATE_FORMAT",
                "received": end_date,
                "type": type(end_date).__name__
            }
    if status:
        # Validar valores permitidos
        valid_statuses = ["PENDING", "PARTIALLY_DELIVERED", "FULLY_DELIVERED", "CANCELED"]
        if status.upper() in valid_statuses:
            params["status"] = status.upper()
    if authorized is not None:
        params["authorized"] = authorized
    if supplier_id is not None:
        params["supplierId"] = int(supplier_id)
    if building_id is not None:
        params["buildingId"] = int(building_id)
    if buyer_id:
        params["buyerId"] = buyer_id
    if status_approval:
        # Validar valores permitidos
        if status_approval.upper() in ["DISAPPROVED", "APPROVED"]:
            params["statusApproval"] = status_approval.upper()
    if consistency:
        # Validar valores permitidos
        valid_consistency = ["IN_INCLUSION", "CONSISTENT", "INCONSISTENT"]
        if consistency.upper() in valid_consistency:
            params["consistency"] = consistency.upper()

    # Cache para buscas com filtros (chave baseada nos parâmetros)
    cache_key = f"purchase_orders:{start_date}:{end_date}:{status}:{authorized}:{supplier_id}:{building_id}:{limit}:{offset}"
    try:
        cached = cache_get(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    result = await make_request("GET", "/purchase-orders", params=params)

    if result["success"]:
        data = result["data"]
        orders = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(orders))

        filters_applied = {
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "authorized": authorized,
            "supplier_id": supplier_id,
            "building_id": building_id,
            "buyer_id": buyer_id,
            "status_approval": status_approval,
            "consistency": consistency,
            "limit": limit,
            "offset": offset,
        }

        response = {
            "success": True,
            "message": f"✅ Encontrados {len(orders)} pedidos de compra (total: {total_count})",
            "purchase_orders": orders,
            "count": len(orders),
            "total_count": total_count,
            "filters_applied": {k: v for k, v in filters_applied.items() if v is not None},
        }
        
        # Adicionar sugestão de Supabase para buscas amplas
        if not start_date and not end_date and not supplier_id and total_count > 50:
            response["suggestion"] = "💡 Para buscas mais eficientes em grandes volumes, considere usar: search_supabase_data(search_term='...', table_names=['purchase_orders'])"
        
        # Cache por 30 segundos para buscas com filtros
        try:
            cache_set(cache_key, response, ttl=30)
        except Exception:
            pass
        
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar pedidos de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_purchase_order_items(make_request, purchase_order_id: str) -> Dict:
    """Consulta itens de um pedido de compra específico"""
    result = await make_request("GET", f"/purchase-orders/{purchase_order_id}/items")

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontrados {len(items)} itens no pedido {purchase_order_id}",
            "purchase_order_id": purchase_order_id,
            "items": items,
            "count": len(items),
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar itens do pedido {purchase_order_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_purchase_order_by_id(make_request, purchase_order_id: str) -> Dict:
    """Busca um pedido de compra específico por ID"""
    result = await make_request("GET", f"/purchase-orders/{purchase_order_id}")

    if result["success"]:
        data = result["data"]
        return {
            "success": True,
            "message": f"✅ Pedido {purchase_order_id} encontrado",
            "purchase_order": data,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar pedido {purchase_order_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def validate_purchase_order_company(make_request, logger, purchase_order_id: str, company_id: Optional[int] = None) -> Dict:
    """
    Valida se um pedido de compra pode ser usado em uma nota fiscal
    Verifica se o centro de custo do pedido pertence à empresa da NF
    """
    try:
        # 1. Buscar detalhes do pedido
        pedido_result = await make_request("GET", f"/purchase-orders/{purchase_order_id}")
        
        if not pedido_result["success"]:
            return {
                "success": False,
                "message": f"❌ Erro ao buscar pedido {purchase_order_id}",
                "error": pedido_result.get("error"),
                "details": pedido_result.get("message"),
            }
        
        pedido = pedido_result["data"]
        building_id = pedido.get("buildingId")
        
        if not building_id:
            return {
                "success": False,
                "message": f"❌ Pedido {purchase_order_id} não possui buildingId",
                "error": "MISSING_BUILDING_ID",
            }
        
        # 2. Buscar a obra/empreendimento para descobrir a empresa
        obra_result = await make_request("GET", f"/enterprises/{building_id}")
        
        if not obra_result["success"]:
            return {
                "success": False,
                "message": f"❌ Erro ao buscar empreendimento {building_id}",
                "error": obra_result.get("error"),
                "details": obra_result.get("message"),
            }
        
        obra = obra_result["data"]
        obra_company_id = obra.get("companyId")
        
        if not obra_company_id:
            return {
                "success": False,
                "message": f"❌ Empreendimento {building_id} não possui companyId",
                "error": "MISSING_COMPANY_ID",
            }
        
        # 3. Validar compatibilidade
        is_valid = True
        recommendation = f"✅ Pedido {purchase_order_id} pode ser usado"
        
        if company_id is not None:
            is_valid = (obra_company_id == company_id)
            if is_valid:
                recommendation = f"✅ Pedido {purchase_order_id} pode ser usado com empresa {company_id}"
            else:
                recommendation = (
                    f"❌ INCOMPATIBILIDADE: Pedido {purchase_order_id} pertence à empresa {obra_company_id} "
                    f"({obra.get('companyName', 'N/A')}), não à empresa {company_id}. "
                    f"Use company_id: {obra_company_id} ao criar a NF."
                )
        else:
            recommendation = f"✅ Use company_id: {obra_company_id} ({obra.get('companyName', 'N/A')}) ao criar a NF"
        
        return {
            "success": True,
            "valid": is_valid,
            "purchase_order": {
                "id": pedido.get("id"),
                "code": pedido.get("code"),
                "buildingId": building_id,
                "costCenterId": pedido.get("costCenterId"),
                "supplierId": pedido.get("supplierId"),
                "supplierName": pedido.get("supplierName"),
                "totalAmount": pedido.get("totalAmount"),
                "status": pedido.get("status"),
            },
            "building": {
                "id": obra.get("id"),
                "name": obra.get("name"),
                "code": obra.get("code"),
                "companyId": obra_company_id,
                "companyName": obra.get("companyName"),
            },
            "recommendation": recommendation,
            "message": recommendation,
        }
        
    except Exception as e:
        logger.error(f"Erro ao validar pedido {purchase_order_id}: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao validar pedido {purchase_order_id}",
            "error": str(e),
        }


# ============ SOLICITAÇÕES DE COMPRA ============

async def get_sienge_purchase_requests(make_request, purchase_request_id: Optional[str] = None, limit: Optional[int] = 50) -> Dict:
    """Consulta solicitações de compra"""
    if purchase_request_id:
        result = await make_request("GET", f"/purchase-requests/{purchase_request_id}")
        if result["success"]:
            return {
                "success": True,
                "message": f"✅ Solicitação {purchase_request_id} encontrada",
                "purchase_request": result["data"],
            }
        return result

    params = {"limit": min(limit or 50, 200)}
    result = await make_request("GET", "/purchase-requests", params=params)

    if result["success"]:
        data = result["data"]
        requests = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(requests)} solicitações de compra",
            "purchase_requests": requests,
            "count": len(requests),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar solicitações de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def create_sienge_purchase_request(make_request, description: str, project_id: str, items: List[Dict[str, Any]]) -> Dict:
    """Cria nova solicitação de compra"""
    request_data = {
        "description": description,
        "project_id": project_id,
        "items": items,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    result = await make_request("POST", "/purchase-requests", json_data=request_data)

    if result["success"]:
        return {
            "success": True,
            "message": "✅ Solicitação de compra criada com sucesso",
            "request_id": result["data"].get("id"),
            "data": result["data"],
        }

    return {
        "success": False,
        "message": "❌ Erro ao criar solicitação de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def post_sienge_purchase_request(
    make_request,
    building_id: int,
    departament_id: Optional[int] = None,
    requester_user: Optional[str] = None,
    request_date: Optional[str] = None,
    notes: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict:
    """Cria uma solicitação de compra usando o schema nativo da API"""
    payload: Dict[str, Any] = {"buildingId": building_id}
    if departament_id is not None:
        payload["departamentId"] = departament_id
    if requester_user:
        payload["requesterUser"] = requester_user
    payload["requestDate"] = request_date or datetime.utcnow().strftime("%Y-%m-%d")
    if notes:
        payload["notes"] = notes
    if created_by:
        payload["createdBy"] = created_by

    result = await make_request("POST", "/purchase-requests", json_data=payload)

    if result["success"]:
        data = result.get("data", {})
        return {
            "success": True,
            "message": "✅ Solicitação de compra criada",
            "data": data,
            "id": data.get("id"),
        }

    return {
        "success": False,
        "message": "❌ Erro ao criar solicitação de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ NOTAS FISCAIS DE COMPRA ============

async def get_sienge_purchase_invoice(make_request, sequential_number: int) -> Dict:
    """
    Consulta nota fiscal de compra por número sequencial.
    
    O sequential_number é o número interno do Sienge, gerado quando a NF é criada no sistema.
    Este NÃO é o número da NF que aparece no DANFE.
    
    Para buscar pelo número da NF (ex: "1165562"), use as tools do Supabase:
    - search_supabase_data(search_term="1165562", table_names=["purchase_invoices"])
    - query_supabase_database(table_name="purchase_invoices", search_term="1165562")
    
    Args:
        sequential_number: Número sequencial interno do Sienge (gerado ao criar a NF)
    """
    result = await make_request("GET", f"/purchase-invoices/{sequential_number}")

    if result["success"]:
        return {"success": True, "message": f"✅ Nota fiscal {sequential_number} encontrada", "invoice": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao buscar nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_purchase_invoice_items(make_request, sequential_number: int) -> Dict:
    """Consulta itens de uma nota fiscal de compra"""
    result = await make_request("GET", f"/purchase-invoices/{sequential_number}/items")

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontrados {len(items)} itens na nota fiscal {sequential_number}",
            "items": items,
            "count": len(items),
            "metadata": metadata,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar itens da nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def create_sienge_purchase_invoice(
    make_request,
    document_id: str,
    number: str,
    supplier_id: int,
    company_id: int,
    movement_type_id: int,
    movement_date: str,
    issue_date: str,
    series: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict:
    """Cadastra uma nova nota fiscal de compra"""
    invoice_data = {
        "documentId": document_id,
        "number": number,
        "supplierId": supplier_id,
        "companyId": company_id,
        "movementTypeId": movement_type_id,
        "movementDate": movement_date,
        "issueDate": issue_date,
    }

    if series:
        invoice_data["series"] = series
    if notes:
        invoice_data["notes"] = notes

    result = await make_request("POST", "/purchase-invoices", json_data=invoice_data)

    if result["success"]:
        return {"success": True, "message": f"✅ Nota fiscal {number} criada com sucesso", "invoice": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao criar nota fiscal {number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def add_items_to_purchase_invoice(
    make_request,
    sequential_number: int,
    deliveries_order: List[Dict[str, Any]],
    copy_notes_purchase_orders: bool = True,
    copy_notes_resources: bool = False,
    copy_attachments_purchase_orders: bool = True,
) -> Dict:
    """Insere itens em uma nota fiscal a partir de entregas de pedidos de compra"""
    item_data = {
        "deliveriesOrder": deliveries_order,
        "copyNotesPurchaseOrders": copy_notes_purchase_orders,
        "copyNotesResources": copy_notes_resources,
        "copyAttachmentsPurchaseOrders": copy_attachments_purchase_orders,
    }

    result = await make_request(
        "POST", f"/purchase-invoices/{sequential_number}/items/purchase-orders/delivery-schedules", json_data=item_data
    )

    if result["success"]:
        return {
            "success": True,
            "message": f"✅ Itens adicionados à nota fiscal {sequential_number} com sucesso",
            "item": result["data"],
        }

    return {
        "success": False,
        "message": f"❌ Erro ao adicionar itens à nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_purchase_invoices_deliveries_attended(
    make_request,
    bill_id: Optional[int] = None,
    sequential_number: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    invoice_item_number: Optional[int] = None,
    purchase_order_item_number: Optional[int] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
) -> Dict:
    """Lista entregas atendidas entre pedidos de compra e notas fiscais"""
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}

    if bill_id:
        params["billId"] = bill_id
    if sequential_number:
        params["sequentialNumber"] = sequential_number
    if purchase_order_id:
        params["purchaseOrderId"] = purchase_order_id
    if invoice_item_number:
        params["invoiceItemNumber"] = invoice_item_number
    if purchase_order_item_number:
        params["purchaseOrderItemNumber"] = purchase_order_item_number

    result = await make_request("GET", "/purchase-invoices/deliveries-attended", params=params)

    if result["success"]:
        data = result["data"]
        deliveries = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontradas {len(deliveries)} entregas atendidas",
            "deliveries": deliveries,
            "count": len(deliveries),
            "metadata": metadata,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar entregas atendidas",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ ITENS DE REQUISIÇÃO DE COMPRA ============

async def get_sienge_purchase_request_items(
    make_request,
    request_id: int,
    limit: Optional[int] = 200,
) -> Dict:
    """Consulta itens de uma requisição de compra"""
    params = {"limit": min(limit or 200, 200)}
    
    result = await make_request("GET", f"/purchase-requests/{request_id}/items", params=params)

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontrados {len(items)} itens na requisição {request_id}",
            "request_id": request_id,
            "items": items,
            "count": len(items),
            "metadata": metadata,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar itens da requisição {request_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ NOTAS FISCAIS DE COMPRA (BÁSICO) ============

async def get_sienge_purchase_invoices(
    make_request,
    supplier_id: Optional[int] = None,
    limit: Optional[int] = 100,
    sequential_number: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    bill_id: Optional[int] = None,
) -> Dict:
    """
    Busca notas fiscais de compra no Sienge.
    
    Usa o endpoint /purchase-invoices/deliveries-attended que retorna entregas atendidas
    (relação entre pedidos de compra e notas fiscais).
    
    IMPORTANTE: O endpoint exige pelo menos um dos filtros:
    - sequential_number (número sequencial da NF)
    - purchase_order_id (ID do pedido de compra)
    - bill_id (ID do título a pagar)
    
    Se nenhum filtro for fornecido, retorna uma mensagem informativa.
    Para sincronização em massa, use o script em Sienge-Database.
    """
    # O endpoint exige pelo menos um desses parâmetros
    if not any([sequential_number, purchase_order_id, bill_id]):
        return {
            "success": False,
            "message": "❌ É necessário fornecer pelo menos um dos filtros: sequential_number, purchase_order_id ou bill_id",
            "error": "MISSING_REQUIRED_FILTER",
            "suggestion": "Use get_purchase_invoice_by_sequential(sequential_number) para buscar uma NF específica, ou forneça purchase_order_id/bill_id"
        }
    
    params: Dict[str, Any] = {"limit": min(limit or 100, 200)}
    
    if sequential_number:
        params["sequentialNumber"] = sequential_number
    if purchase_order_id:
        params["purchaseOrderId"] = purchase_order_id
    if bill_id:
        params["billId"] = bill_id
    
    result = await make_request("GET", "/purchase-invoices/deliveries-attended", params=params)

    if result["success"]:
        data = result["data"]
        deliveries = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        
        # Extrair informações únicas de notas fiscais dos deliveries
        invoices_map = {}
        for delivery in deliveries:
            seq_num = delivery.get("sequentialNumber") or delivery.get("invoiceSequentialNumber")
            if seq_num:
                if seq_num not in invoices_map:
                    invoices_map[seq_num] = {
                        "sequentialNumber": seq_num,
                        "supplierId": delivery.get("supplierId"),
                        "supplierName": delivery.get("supplierName"),
                        "purchaseOrderId": delivery.get("purchaseOrderId"),
                        "deliveries": []
                    }
                invoices_map[seq_num]["deliveries"].append(delivery)
        
        invoices = list(invoices_map.values())
        
        # Filtrar por supplier_id se especificado
        if supplier_id is not None:
            invoices = [inv for inv in invoices if inv.get("supplierId") == supplier_id]
        
        total_count = metadata.get("count", len(deliveries))

        return {
            "success": True,
            "message": f"✅ Encontradas {len(invoices)} notas fiscais de compra (de {len(deliveries)} entregas)",
            "purchase_invoices": invoices,
            "count": len(invoices),
            "metadata": metadata,
            "filters": params,
            "note": "Dados obtidos via /purchase-invoices/deliveries-attended. Use get_purchase_invoice_by_sequential() para detalhes completos de uma NF específica."
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar notas fiscais de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ HELPER FUNCTIONS - FINANCEIRO ============

def _to_cents(x: Decimal) -> int:
    """Converte Decimal para centavos com arredondamento correto"""
    return int((x * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _from_cents(c: int) -> Decimal:
    """Converte centavos de volta para Decimal com 2 casas decimais"""
    return (Decimal(c) / Decimal(100)).quantize(Decimal("0.01"))


def split_installments_exact(total: Decimal, n: int) -> List[Decimal]:
    """
    Divide total em n parcelas garantindo soma exata
    Distribui o resto (centavos) nas primeiras parcelas
    """
    if n <= 0:
        raise ValueError("n must be >= 1")
    cents = _to_cents(total)
    base, resto = divmod(cents, n)
    parts = [base + (1 if i < resto else 0) for i in range(n)]
    return [_from_cents(p) for p in parts]


def _infer_invoice_total(invoice: Dict[str, Any]) -> Optional[Decimal]:
    """Tenta inferir o total da nota fiscal de diversos campos possíveis"""
    for k in ("totalAmount", "invoiceTotal", "amount", "total", "grandTotal"):
        if k in invoice and invoice[k] is not None:
            try:
                return Decimal(str(invoice[k]))
            except Exception:
                pass
    return None


# ============ PIPELINE COMPLETA DE PROCESSAMENTO ============

async def process_purchase_invoice_pipeline(
    make_request,
    logger_param=None,  # Não usado, mantido para compatibilidade
    invoice: Optional[Dict[str, Any]] = None,
    sequential_number: Optional[int] = None,
    deliveries_order: Optional[List[Dict[str, Any]]] = None,
    installments: Optional[Dict[str, Any]] = None,
    bill_id: Optional[int] = None,
    attachment_path: Optional[str] = None,
    attachment_description: Optional[str] = None,
    attachment_file_name: Optional[str] = None,
    attachment_file_content_base64: Optional[str] = None,
    attachment_content_type: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Pipeline completo de processamento de nota fiscal:
      1) Cria (ou reutiliza) a NF de compra
      2) Adiciona itens (via pedidos + cronogramas) — opcional
      3) Atualiza parcelas do título criado automaticamente pelo Sienge — opcional
      4) Anexa arquivo ao título (DANFE, PDF, etc.) — opcional

    IMPORTANTE: O Sienge cria títulos automaticamente ao lançar NF.
    Este pipeline NÃO cria títulos manualmente por padrão.

    Args:
        make_request: Função para fazer requisições à API
        logger: Logger para rastreamento
        invoice: payload para POST /purchase-invoices (se sequential_number não for passado)
        sequential_number: usar NF já existente
        deliveries_order: lista p/ POST /purchase-invoices/{seq}/items/purchase-orders/delivery-schedules
        installments: {"dueDates": ["2025-11-03","2025-12-03"], "amounts": [920.70, 920.70]} 
                      ou {"daysToDue": [30, 60, 90], "baseDate": "YYYY-MM-DD", "amounts": [...]}
        bill_id: ID do título (opcional; se ausente, auto-descobre)
        attachment_path: Caminho do arquivo local ou URL para anexar ao título
        attachment_description: Descrição do anexo (obrigatório se attachment_path ou attachment_file_content_base64 for fornecido)
        attachment_file_name: Nome do arquivo (obrigatório se usar attachment_file_content_base64)
        attachment_file_content_base64: Conteúdo do arquivo em Base64
        attachment_content_type: MIME type do arquivo (opcional, detectado automaticamente)
        options: {"dryRun": bool, "resumeIfExists": bool, "copyNotesPurchaseOrders": bool,
                  "copyNotesResources": bool, "copyAttachmentsPurchaseOrders": bool,
                  "forceCreateBill": bool (use apenas se Sienge não criar automaticamente)}
    """
    corr_id = str(uuid.uuid4())
    opts = options or {}
    dry = bool(opts.get("dryRun", False))
    resume = bool(opts.get("resumeIfExists", True))

    # Usar logger padrão do módulo (evita problemas de serialização)
    logger = log
    
    out: Dict[str, Any] = {"success": True, "correlationId": corr_id, "steps": []}
    logger.info(f"Pipeline iniciado - correlationId: {corr_id}, dryRun: {dry}")

    # 1) NF: criar ou reutilizar
    nf_seq = sequential_number
    nf_obj: Optional[Dict[str, Any]] = None

    if nf_seq is None and invoice:
        if dry:
            out["steps"].append({"step": "create_invoice", "dryRun": True, "payload": invoice})
        else:
            r = await make_request("POST", "/purchase-invoices", json_data=invoice)
            if not r.get("success"):
                out.update(success=False)
                out["steps"].append({"step":"create_invoice","ok":False,"error":r.get("error"),"details":r.get("message")})
                return out
            nf_obj = r.get("data") or {}
            nf_seq = nf_obj.get("sequentialNumber") or nf_obj.get("id")
            out["steps"].append({"step":"create_invoice","ok":True,"sequentialNumber":nf_seq})
            logger.info(f"NF criada - sequentialNumber: {nf_seq}")
    elif nf_seq is not None and resume:
        if dry:
            out["steps"].append({"step":"load_invoice","dryRun":True,"sequentialNumber":nf_seq})
        else:
            r = await make_request("GET", f"/purchase-invoices/{nf_seq}")
            if not r.get("success"):
                out.update(success=False)
                out["steps"].append({"step":"load_invoice","ok":False,"sequentialNumber":nf_seq,"error":r.get("error"),"details":r.get("message")})
                return out
            nf_obj = r.get("data") or {}
            out["steps"].append({"step":"load_invoice","ok":True,"sequentialNumber":nf_seq})
            logger.info(f"NF carregada - sequentialNumber: {nf_seq}")

    if nf_seq is None:
        out.update(success=False)
        out["steps"].append({"step":"create_or_load_invoice","ok":False,"error":"Sem sequential_number e sem invoice"})
        return out

    # 2) Itens via pedidos/cronogramas (opcional)
    if deliveries_order:
        payload_items = {
            "deliveriesOrder": deliveries_order,
            "copyNotesPurchaseOrders": bool(opts.get("copyNotesPurchaseOrders", True)),
            "copyNotesResources": bool(opts.get("copyNotesResources", False)),
            "copyAttachmentsPurchaseOrders": bool(opts.get("copyAttachmentsPurchaseOrders", True)),
        }
        if dry:
            out["steps"].append({"step":"add_items_from_purchase_orders","dryRun":True,"payload":payload_items})
        else:
            r = await make_request("POST", f"/purchase-invoices/{nf_seq}/items/purchase-orders/delivery-schedules", json_data=payload_items)
            if not r.get("success"):
                out.update(success=False)
                out["steps"].append({"step":"add_items_from_purchase_orders","ok":False,"error":r.get("error"),"details":r.get("message")})
                return out
            out["steps"].append({"step":"add_items_from_purchase_orders","ok":True})
            logger.info(f"Itens adicionados à NF {nf_seq}")
    else:
        out["steps"].append({"step":"add_items_from_purchase_orders","skipped":True})

    # 3) Atualizar parcelas do título (se installments for fornecido)
    if installments and nf_seq:
        try:
            # Importar função de accounts_payable
            from . import accounts_payable
            
            # Preparar parâmetros para ap_update_auto_bill_installments
            due_dates = installments.get("dueDates")
            days_to_due = installments.get("daysToDue")
            base_date = installments.get("baseDate")
            amounts = installments.get("amounts")
            
            if dry:
                out["steps"].append({
                    "step": "update_installments",
                    "dryRun": True,
                    "installments": installments
                })
            else:
                # Usar make_bulk_request se disponível (passado via options)
                # Se não estiver disponível, usar make_request como fallback
                make_bulk_request_func = opts.get("make_bulk_request")
                if make_bulk_request_func is None:
                    # Se não foi passado, usar make_request como fallback
                    make_bulk_request_func = make_request
                
                installments_result = await accounts_payable.ap_update_auto_bill_installments(
                    make_request,
                    make_bulk_request_func,
                    nf_seq,
                    bill_id,
                    due_dates,
                    days_to_due,
                    base_date,
                    amounts
                )
                
                out["steps"].append({
                    "step": "update_installments",
                    "result": installments_result
                })
                
                if installments_result.get("success"):
                    out["billId"] = installments_result.get("billId")
                    logger.info(f"Parcelas atualizadas - billId: {installments_result.get('billId')}")
                else:
                    logger.warning(f"Falha ao atualizar parcelas: {installments_result.get('message')}")
        except ImportError:
            logger.warning("Módulo accounts_payable não disponível para atualização de parcelas")
            out["steps"].append({
                "step": "update_installments",
                "skipped": True,
                "reason": "accounts_payable module not available"
            })
        except Exception as e:
            logger.error(f"Erro ao atualizar parcelas: {e}", exc_info=True)
            out["steps"].append({
                "step": "update_installments",
                "error": str(e)
            })
    else:
        out["steps"].append({"step": "update_installments", "skipped": True})

    # 4) Anexar arquivo ao título (se fornecido)
    attachment_bill_id = bill_id or out.get("billId")
    
    # Se não temos bill_id ainda, tentar descobrir via sequential_number
    if not attachment_bill_id and nf_seq:
        try:
            from . import accounts_payable
            make_bulk_request_func = opts.get("make_bulk_request", make_request)
            
            # Tentar descobrir bill_id usando resolve_bill_id_for_invoice
            resolved_bill_id = await accounts_payable.resolve_bill_id_for_invoice(
                make_request,
                make_bulk_request_func,
                nf_seq
            )
            if resolved_bill_id:
                attachment_bill_id = resolved_bill_id
                out["billId"] = resolved_bill_id
                logger.info(f"BillId descoberto para anexo: {resolved_bill_id}")
        except Exception as e:
            logger.debug(f"Não foi possível descobrir bill_id para anexo: {e}")
    
    if (attachment_path or attachment_file_content_base64) and attachment_bill_id:
        if not attachment_description:
            logger.warning("attachment_description não fornecido, usando descrição padrão")
            attachment_description = f"Anexo NF {nf_seq}"
        
        try:
            from . import accounts_payable
            
            if dry:
                out["steps"].append({
                    "step": "attach_file",
                    "dryRun": True,
                    "billId": attachment_bill_id,
                    "file": attachment_path or f"Base64 file: {attachment_file_name}"
                })
            else:
                attach_result = await accounts_payable.ap_attach_bill(
                    make_request,
                    attachment_bill_id,
                    attachment_description,
                    attachment_path,
                    attachment_file_name,
                    attachment_file_content_base64,
                    attachment_content_type
                )
                
                out["steps"].append({
                    "step": "attach_file",
                    "result": attach_result
                })
                
                if attach_result.get("success"):
                    logger.info(f"Arquivo anexado com sucesso ao título {attachment_bill_id}")
                else:
                    logger.warning(f"Falha ao anexar arquivo: {attach_result.get('message')}")
        except ImportError:
            logger.warning("Módulo accounts_payable não disponível para anexar arquivo")
            out["steps"].append({
                "step": "attach_file",
                "skipped": True,
                "reason": "accounts_payable module not available"
            })
        except Exception as e:
            logger.error(f"Erro ao anexar arquivo: {e}", exc_info=True)
            out["steps"].append({
                "step": "attach_file",
                "error": str(e)
            })
    elif (attachment_path or attachment_file_content_base64) and not attachment_bill_id:
        logger.warning("Anexo solicitado mas bill_id não disponível (NF pode não ter título criado ainda)")
        out["steps"].append({
            "step": "attach_file",
            "skipped": True,
            "reason": "bill_id not available"
        })
    else:
        out["steps"].append({"step": "attach_file", "skipped": True})

    # 5) Pipeline completo - retornar resultado
    out["success"] = True
    out["invoiceSequential"] = nf_seq
    logger.info(f"Pipeline concluído com sucesso - NF: {nf_seq}")
    return out
