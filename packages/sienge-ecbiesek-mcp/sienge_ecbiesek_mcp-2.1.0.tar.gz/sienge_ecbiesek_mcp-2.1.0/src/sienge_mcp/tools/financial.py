"""
Financial Tools - Ferramentas financeiras
Contas a Receber, Bills (Contas a Pagar), Dashboard, Análises
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


# ============ CONTAS A RECEBER (ACCOUNTS RECEIVABLE) ============

async def get_sienge_accounts_receivable(
    make_bulk_request,
    start_date: str,
    end_date: str,
    selection_type: str = "D",
    company_id: Optional[int] = None,
    cost_centers_id: Optional[List[int]] = None,
    correction_indexer_id: Optional[int] = None,
    correction_date: Optional[str] = None,
    change_start_date: Optional[str] = None,
    completed_bills: Optional[str] = None,
    origins_ids: Optional[List[str]] = None,
    bearers_id_in: Optional[List[int]] = None,
    bearers_id_not_in: Optional[List[int]] = None,
) -> Dict:
    """
    Consulta parcelas do contas a receber via API bulk-data

    Args:
        make_bulk_request: Função para fazer requisições bulk à API
        start_date: Data de início do período (YYYY-MM-DD) - OBRIGATÓRIO
        end_date: Data do fim do período (YYYY-MM-DD) - OBRIGATÓRIO
        selection_type: Seleção da data do período (I=emissão, D=vencimento, P=pagamento, B=competência) - padrão: D
        company_id: Código da empresa
        cost_centers_id: Lista de códigos de centro de custo
        correction_indexer_id: Código do indexador de correção
        correction_date: Data para correção do indexador (YYYY-MM-DD)
        change_start_date: Data inicial de alteração do título/parcela (YYYY-MM-DD)
        completed_bills: Filtrar por títulos completos (S)
        origins_ids: Códigos dos módulos de origem (CR, CO, ME, CA, CI, AR, SC, LO, NE, NS, AC, NF)
        bearers_id_in: Filtrar parcelas com códigos de portador específicos
        bearers_id_not_in: Filtrar parcelas excluindo códigos de portador específicos
    """
    params = {"startDate": start_date, "endDate": end_date, "selectionType": selection_type}

    if company_id:
        params["companyId"] = company_id
    if cost_centers_id:
        params["costCentersId"] = cost_centers_id
    if correction_indexer_id:
        params["correctionIndexerId"] = correction_indexer_id
    if correction_date:
        params["correctionDate"] = correction_date
    if change_start_date:
        params["changeStartDate"] = change_start_date
    if completed_bills:
        params["completedBills"] = completed_bills
    if origins_ids:
        params["originsIds"] = origins_ids
    if bearers_id_in:
        params["bearersIdIn"] = bearers_id_in
    if bearers_id_not_in:
        params["bearersIdNotIn"] = bearers_id_not_in

    result = await make_bulk_request("GET", "/income", params=params)

    if result["success"]:
        data = result["data"]
        income_data = data.get("data", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas a receber",
            "income_data": income_data,
            "count": len(income_data),
            "period": f"{start_date} a {end_date}",
            "selection_type": selection_type,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas a receber",
        "error": result.get("error"),
        "details": result.get("message"),
    }


async def get_sienge_accounts_receivable_by_bills(
    make_bulk_request,
    bills_ids: List[int], 
    correction_indexer_id: Optional[int] = None, 
    correction_date: Optional[str] = None
) -> Dict:
    """
    Consulta parcelas dos títulos informados via API bulk-data

    Args:
        make_bulk_request: Função para fazer requisições bulk à API
        bills_ids: Lista de códigos dos títulos - OBRIGATÓRIO
        correction_indexer_id: Código do indexador de correção
        correction_date: Data para correção do indexador (YYYY-MM-DD)
    """
    params = {"billsIds": bills_ids}

    if correction_indexer_id:
        params["correctionIndexerId"] = correction_indexer_id
    if correction_date:
        params["correctionDate"] = correction_date

    result = await make_bulk_request("GET", "/income/by-bills", params=params)

    if result["success"]:
        data = result["data"]
        income_data = data.get("data", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas dos títulos informados",
            "income_data": income_data,
            "count": len(income_data),
            "bills_consulted": bills_ids,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas dos títulos informados",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ BILLS - CONTAS A PAGAR ============

async def get_sienge_bills(
    make_request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    debtor_id: Optional[int] = None,
    creditor_id: Optional[int] = None,
    cost_center_id: Optional[int] = None,
    documents_identification_id: Optional[List[str]] = None,
    document_number: Optional[str] = None,
    status: Optional[str] = None,
    origin_id: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
) -> Dict:
    """
    Consulta títulos a pagar (contas a pagar) - REQUER startDate e endDate obrigatórios

    Args:
        make_request: Função para fazer requisições à API
        start_date: Data inicial obrigatória (YYYY-MM-DD) - padrão últimos 30 dias
        end_date: Data final obrigatória (YYYY-MM-DD) - padrão hoje
        debtor_id: Código da empresa cadastrada no Sienge
        creditor_id: Código do credor cadastrado no Sienge
        cost_center_id: Código do centro de custo cadastrado no Sienge
        documents_identification_id: Lista de códigos do documento (máx 4)
        document_number: Número do documento vinculado ao título (máx 20 caracteres)
        status: Tipo de consistência (S=Completo, N=Incompleto, I=Em inclusão)
        origin_id: Código de origem (AC, RA, AI, CO, CF, CP, ME, MO, DV, RF, FP, FE, GI, LO, SE)
        limit: Quantidade máxima de resultados (padrão: 100, máx: 200)
        offset: Deslocamento na lista (padrão: 0)
    """
    # Se start_date não fornecido, usar últimos 30 dias
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Se end_date não fornecido, usar hoje
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Parâmetros obrigatórios
    params = {"startDate": start_date, "endDate": end_date}

    # Parâmetros opcionais
    if debtor_id:
        params["debtorId"] = int(debtor_id)
    if creditor_id:
        params["creditorId"] = int(creditor_id)
    if cost_center_id:
        params["costCenterId"] = int(cost_center_id)
    if documents_identification_id:
        # Limitar a 4 elementos conforme documentação
        params["documentsIdentificationId"] = documents_identification_id[:4]
    if document_number:
        # Limitar a 20 caracteres conforme documentação
        params["documentNumber"] = document_number[:20]
    if status:
        # Validar valores permitidos: S, N, I
        if status.upper() in ["S", "N", "I"]:
            params["status"] = status.upper()
    if origin_id:
        # Validar valores permitidos
        valid_origins = ["AC", "RA", "AI", "CO", "CF", "CP", "ME", "MO", "DV", "RF", "FP", "FE", "GI", "LO", "SE"]
        if origin_id.upper() in valid_origins:
            params["originId"] = origin_id.upper()
    if limit:
        # Limitar a 200 conforme documentação
        params["limit"] = min(int(limit), 200)
    if offset:
        params["offset"] = int(offset)

    result = await make_request("GET", "/bills", params=params)

    # Se o endpoint /bills não existir (404), retornar mensagem informativa
    # Verificar 404 de múltiplas formas
    if not result.get("success"):
        status_code = result.get("status_code")
        error_str = str(result.get("error", ""))
        message_str = str(result.get("message", "") or result.get("details", ""))
        
        # Verificar se é 404
        is_404 = (
            status_code == 404 or 
            "404" in error_str or 
            "404" in message_str or
            "Resource not found" in message_str
        )
        
        if is_404:
            return {
                "success": False,
                "message": "❌ Endpoint /bills não está disponível nesta instância do Sienge",
                "error": "ENDPOINT_NOT_AVAILABLE",
                "status_code": 404,
                "suggestion": "Use as tools do Supabase para buscar títulos sincronizados: search_supabase_data(search_term='...', table_names=['payable_titles']) ou query_supabase_database(table_name='payable_titles', ...)",
                "note": "O endpoint /bills pode não estar habilitado em todas as instâncias do Sienge. Para sincronização em massa, use o script Sienge-Database/sync_to_supabase.py"
            }
        
        # Se não for 404, retornar erro genérico
        return {
            "success": False,
            "message": "❌ Erro ao buscar títulos a pagar",
            "error": result.get("error"),
            "details": result.get("message"),
            "status_code": status_code,
        }

    if result.get("success"):
        data = result["data"]
        bills = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(bills))
        
        # Limit já foi aplicado na query, não precisa aplicar manualmente

        return {
            "success": True,
            "message": f"✅ Encontrados {len(bills)} títulos a pagar (total: {total_count}) - período: {start_date} a {end_date}",
            "bills": bills,
            "count": len(bills),
            "total_count": total_count,
            "period": {"start_date": start_date, "end_date": end_date},
            "filters": params,
        }

    # Erro genérico
    return {
        "success": False,
        "message": "❌ Erro ao buscar títulos a pagar",
        "error": result.get("error"),
        "details": result.get("message"),
        "status_code": status_code,
    }


# ============ BUSCA FINANCEIRA AVANÇADA ============

async def search_sienge_financial_data(
    get_accounts_receivable_func,
    get_bills_func,
    period_start: str,
    period_end: str, 
    search_type: str = "both",
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    customer_creditor_search: Optional[str] = None
) -> Dict:
    """
    Busca avançada em dados financeiros do Sienge - Contas a Pagar e Receber
    
    Args:
        get_accounts_receivable_func: Função get_sienge_accounts_receivable já configurada
        get_bills_func: Função get_sienge_bills já configurada
        period_start: Data inicial do período (YYYY-MM-DD)
        period_end: Data final do período (YYYY-MM-DD)
        search_type: Tipo de busca ("receivable", "payable", "both")
        amount_min: Valor mínimo (opcional)
        amount_max: Valor máximo (opcional)
        customer_creditor_search: Buscar por nome de cliente/credor (opcional)
    """
    financial_results = {
        "receivable": {"success": False, "data": [], "count": 0, "error": None},
        "payable": {"success": False, "data": [], "count": 0, "error": None}
    }
    
    # Buscar contas a receber
    if search_type in ["receivable", "both"]:
        try:
            receivable_result = await get_accounts_receivable_func(
                start_date=period_start,
                end_date=period_end,
                selection_type="D"  # Por vencimento
            )
            
            if receivable_result["success"]:
                receivable_data = receivable_result["income_data"]
                
                # Aplicar filtros de valor se especificados
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in receivable_data:
                        amount = float(item.get("amount", 0) or 0)
                        if amount_min is not None and amount < amount_min:
                            continue
                        if amount_max is not None and amount > amount_max:
                            continue
                        filtered_data.append(item)
                    receivable_data = filtered_data
                
                # Aplicar filtro de cliente se especificado
                if customer_creditor_search:
                    search_lower = customer_creditor_search.lower()
                    filtered_data = []
                    for item in receivable_data:
                        customer_name = str(item.get("customer_name", "")).lower()
                        if search_lower in customer_name:
                            filtered_data.append(item)
                    receivable_data = filtered_data
                
                financial_results["receivable"] = {
                    "success": True,
                    "data": receivable_data,
                    "count": len(receivable_data),
                    "error": None
                }
            else:
                financial_results["receivable"]["error"] = receivable_result.get("error")
                
        except Exception as e:
            financial_results["receivable"]["error"] = str(e)
    
    # Buscar contas a pagar  
    if search_type in ["payable", "both"]:
        try:
            payable_result = await get_bills_func(
                start_date=period_start,
                end_date=period_end,
                limit=100
            )
            
            if payable_result["success"]:
                payable_data = payable_result["bills"]
                
                # Aplicar filtros de valor se especificados
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in payable_data:
                        amount = float(item.get("amount", 0) or 0)
                        if amount_min is not None and amount < amount_min:
                            continue
                        if amount_max is not None and amount > amount_max:
                            continue
                        filtered_data.append(item)
                    payable_data = filtered_data
                
                # Aplicar filtro de credor se especificado
                if customer_creditor_search:
                    search_lower = customer_creditor_search.lower()
                    filtered_data = []
                    for item in payable_data:
                        creditor_name = str(item.get("creditor_name", "")).lower()
                        if search_lower in creditor_name:
                            filtered_data.append(item)
                    payable_data = filtered_data
                
                financial_results["payable"] = {
                    "success": True,
                    "data": payable_data,
                    "count": len(payable_data),
                    "error": None
                }
            else:
                financial_results["payable"]["error"] = payable_result.get("error")
                
        except Exception as e:
            financial_results["payable"]["error"] = str(e)
    
    # Compilar resultado final
    total_records = financial_results["receivable"]["count"] + financial_results["payable"]["count"]
    has_errors = bool(financial_results["receivable"]["error"] or financial_results["payable"]["error"])
    
    summary = {
        "period": f"{period_start} a {period_end}",
        "search_type": search_type,
        "total_records": total_records,
        "receivable_count": financial_results["receivable"]["count"],
        "payable_count": financial_results["payable"]["count"],
        "filters_applied": {
            "amount_range": f"{amount_min or 'sem mín'} - {amount_max or 'sem máx'}",
            "customer_creditor": customer_creditor_search or "todos"
        }
    }
    
    if total_records > 0:
        return {
            "success": True,
            "message": f"✅ Busca financeira encontrou {total_records} registros no período",
            "summary": summary,
            "receivable": financial_results["receivable"],
            "payable": financial_results["payable"],
            "has_errors": has_errors
        }
    else:
        return {
            "success": False,
            "message": f"❌ Nenhum registro financeiro encontrado no período {period_start} a {period_end}",
            "summary": summary,
            "errors": {
                "receivable": financial_results["receivable"]["error"],
                "payable": financial_results["payable"]["error"]
            }
        }


# ============ DASHBOARD SUMMARY ============

async def get_sienge_dashboard_summary(
    test_connection_func,
    get_customers_func,
    get_projects_func,
    get_bills_func,
    get_customer_types_func,
) -> Dict:
    """
    Obtém um resumo tipo dashboard com informações gerais do Sienge
    Útil para visão geral rápida do sistema
    
    Args:
        test_connection_func: Função test_sienge_connection já configurada
        get_customers_func: Função get_sienge_customers já configurada
        get_projects_func: Função get_sienge_projects já configurada
        get_bills_func: Função get_sienge_bills já configurada
        get_customer_types_func: Função get_sienge_customer_types já configurada
    """
    # Data atual e períodos
    today = datetime.now()
    current_month_start = today.replace(day=1).strftime("%Y-%m-%d")
    current_month_end = today.strftime("%Y-%m-%d")
    
    dashboard_data = {}
    errors = []
    
    # 1. Testar conexão
    try:
        connection_test = await test_connection_func()
        dashboard_data["connection"] = connection_test
    except Exception as e:
        errors.append(f"Teste de conexão: {str(e)}")
        dashboard_data["connection"] = {"success": False, "error": str(e)}
    
    # 2. Contar clientes (amostra)
    try:
        customers_result = await get_customers_func(limit=1)
        if customers_result["success"]:
            dashboard_data["customers_available"] = True
        else:
            dashboard_data["customers_available"] = False
    except Exception as e:
        errors.append(f"Clientes: {str(e)}")
        dashboard_data["customers_available"] = False
    
    # 3. Contar projetos (amostra)
    try:
        projects_result = await get_projects_func(limit=5)
        if projects_result["success"]:
            dashboard_data["projects"] = {
                "available": True,
                "sample_count": len(projects_result["enterprises"]),
                "total_count": projects_result.get("metadata", {}).get("count", "N/A")
            }
        else:
            dashboard_data["projects"] = {"available": False}
    except Exception as e:
        errors.append(f"Projetos: {str(e)}")
        dashboard_data["projects"] = {"available": False, "error": str(e)}
    
    # 4. Títulos a pagar do mês atual
    try:
        bills_result = await get_bills_func(
            start_date=current_month_start,
            end_date=current_month_end,
            limit=10
        )
        if bills_result["success"]:
            dashboard_data["monthly_bills"] = {
                "available": True,
                "count": len(bills_result["bills"]),
                "total_count": bills_result.get("total_count", len(bills_result["bills"]))
            }
        else:
            dashboard_data["monthly_bills"] = {"available": False}
    except Exception as e:
        errors.append(f"Títulos mensais: {str(e)}")
        dashboard_data["monthly_bills"] = {"available": False, "error": str(e)}
    
    # 5. Tipos de clientes
    try:
        customer_types_result = await get_customer_types_func()
        if customer_types_result["success"]:
            dashboard_data["customer_types"] = {
                "available": True,
                "count": len(customer_types_result["customer_types"])
            }
        else:
            dashboard_data["customer_types"] = {"available": False}
    except Exception as e:
        dashboard_data["customer_types"] = {"available": False, "error": str(e)}
    
    # Compilar resultado
    available_modules = sum(1 for key, value in dashboard_data.items() 
                          if key != "connection" and isinstance(value, dict) and value.get("available"))
    
    return {
        "success": True,
        "message": f"✅ Dashboard do Sienge - {available_modules} módulos disponíveis",
        "timestamp": today.isoformat(),
        "period_analyzed": f"{current_month_start} a {current_month_end}",
        "modules_status": dashboard_data,
        "available_modules": available_modules,
        "errors": errors if errors else None,
        "quick_actions": [
            "search_sienge_data('termo_busca') - Busca universal",
            "list_sienge_entities() - Listar tipos de dados", 
            "get_sienge_customers(search='nome') - Buscar clientes",
            "get_sienge_projects() - Listar projetos/obras",
            "search_sienge_financial_data('2024-01-01', '2024-12-31') - Dados financeiros"
        ]
    }
