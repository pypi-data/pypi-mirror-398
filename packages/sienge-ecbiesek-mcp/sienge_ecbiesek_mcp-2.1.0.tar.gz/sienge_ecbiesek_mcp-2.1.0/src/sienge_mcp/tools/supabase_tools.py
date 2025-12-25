"""
Supabase Tools - Ferramentas de query e busca no banco de dados
Acesso direto a dados sincronizados do Sienge para queries eficientes
"""

from typing import Dict, List, Optional, Any
import logging
import os

# Logger
log = logging.getLogger("sienge_mcp.supabase")

# Tentar importar supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    log.warning("Cliente Supabase não disponível. Instale: pip install supabase")

# Configurações do Supabase (lidas do .env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_SCHEMA = "sienge_data"  # Schema fixo: sienge_data


# ============ HELPER FUNCTIONS ============

def _get_supabase_client() -> Optional[Any]:
    """Cria e retorna cliente do Supabase se configurado"""
    if not SUPABASE_AVAILABLE:
        return None
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        return client
    except Exception as e:
        log.warning(f"Erro ao criar cliente Supabase: {e}")
        return None


async def _query_supabase_internal(
    table_name: str,
    columns: Optional[str] = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = 100,
    order_by: Optional[str] = None,
    search_term: Optional[str] = None,
    search_columns: Optional[List[str]] = None
) -> Dict:
    """
    Função interna para query no Supabase (usada por todas as tools)
    
    Args:
        table_name: Nome da tabela
        columns: Colunas a retornar (padrão: "*")
        filters: Filtros WHERE como dict {"campo": "valor"}
        limit: Limite de registros (padrão: 100, máximo: 1000)
        order_by: Campo para ordenação (ex: "name", "created_at desc")
        search_term: Termo de busca para busca textual
        search_columns: Colunas onde fazer busca textual
    
    Returns:
        Dict com success, data, count e query_info
    """
    if not SUPABASE_AVAILABLE:
        return {
            "success": False,
            "message": "❌ Cliente Supabase não disponível. Instale: pip install supabase",
            "error": "SUPABASE_NOT_AVAILABLE"
        }
    
    client = _get_supabase_client()
    if not client:
        return {
            "success": False,
            "message": "❌ Cliente Supabase não configurado. Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY",
            "error": "SUPABASE_NOT_CONFIGURED"
        }
    
    # Validar tabela
    valid_tables = [
        "customers", "creditors", "enterprises", "purchase_invoices", 
        "stock_inventories", "accounts_receivable", "sync_meta",
        "installment_payments", "income_installments"
    ]
    
    if table_name not in valid_tables:
        return {
            "success": False,
            "message": f"❌ Tabela '{table_name}' não é válida",
            "error": "INVALID_TABLE",
            "valid_tables": valid_tables
        }
    
    try:
        # Construir query sempre usando schema sienge_data
        schema_client = client.schema(SUPABASE_SCHEMA)
        query = schema_client.table(table_name).select(columns)
        
        # Aplicar filtros
        if filters:
            for field, value in filters.items():
                if isinstance(value, str) and "%" in value:
                    # Busca com LIKE
                    query = query.like(field, value)
                elif isinstance(value, list):
                    # Busca com IN
                    query = query.in_(field, value)
                else:
                    # Busca exata
                    query = query.eq(field, value)
        
        # Aplicar busca textual se especificada
        if search_term and search_columns:
            # Para busca textual, usar OR entre as colunas
            search_conditions = []
            for col in search_columns:
                search_conditions.append(f"{col}.ilike.%{search_term}%")
            if search_conditions:
                query = query.or_(",".join(search_conditions))
        elif search_term:
            # Busca padrão baseada na tabela
            default_search_columns = {
                "customers": ["name", "document", "email"],
                "creditors": ["name", "document"],
                "enterprises": ["name", "description", "code"],
                "purchase_invoices": ["sequential_number", "notes"],
                "stock_inventories": ["cost_center_id", "resource_id"],
                "accounts_receivable": ["bill_id", "customer_id"],
                "installment_payments": ["installment_uid", "payment_uid"],
                "income_installments": []  # Campos numéricos - sem busca textual
            }
            
            search_cols = default_search_columns.get(table_name, ["name"])
            
            # Se não há colunas de texto para buscar, tentar busca numérica
            if not search_cols:
                # Para tabelas com campos numéricos, tentar converter search_term para número
                try:
                    search_num = int(search_term)
                    # Buscar em campos numéricos comuns
                    numeric_conditions = []
                    if table_name == "income_installments":
                        numeric_conditions = [
                            f"bill_id.eq.{search_num}",
                            f"client_id.eq.{search_num}",
                            f"original_amount.eq.{search_num}",
                            f"balance_amount.eq.{search_num}",
                            f"corrected_balance_amount.eq.{search_num}"
                        ]
                    elif table_name == "installment_payments":
                        numeric_conditions = [
                            f"installment_uid.eq.{search_num}",
                            f"payment_uid.eq.{search_num}",
                            f"gross_amount.eq.{search_num}",
                            f"net_amount.eq.{search_num}",
                            f"corrected_net_amount.eq.{search_num}"
                        ]
                    
                    if numeric_conditions:
                        query = query.or_(",".join(numeric_conditions))
                except ValueError:
                    # Se não é número, não fazer busca
                    pass
            else:
                # Busca textual normal
                search_conditions = [f"{col}.ilike.%{search_term}%" for col in search_cols]
                if search_conditions:
                    query = query.or_(",".join(search_conditions))
        
        # Aplicar ordenação
        if order_by:
            if " desc" in order_by.lower():
                field = order_by.replace(" desc", "").replace(" DESC", "")
                query = query.order(field, desc=True)
            else:
                field = order_by.replace(" asc", "").replace(" ASC", "")
                query = query.order(field)
        
        # Aplicar limite
        limit = min(limit or 100, 1000)
        query = query.limit(limit)
        
        # Executar query
        result = query.execute()
        
        if hasattr(result, 'data'):
            data = result.data
        else:
            data = result
        
        return {
            "success": True,
            "message": f"✅ Query executada com sucesso na tabela '{table_name}'",
            "table_name": table_name,
            "data": data,
            "count": len(data) if isinstance(data, list) else 1,
            "query_info": {
                "columns": columns,
                "filters": filters,
                "limit": limit,
                "order_by": order_by,
                "search_term": search_term,
                "search_columns": search_columns
            }
        }
        
    except Exception as e:
        log.error(f"Erro na query Supabase: {e}")
        return {
            "success": False,
            "message": f"❌ Erro ao executar query na tabela '{table_name}'",
            "error": str(e),
            "table_name": table_name
        }


# ============ TOOLS PRINCIPAIS ============

async def query_supabase_database(
    table_name: str,
    columns: Optional[str] = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = 100,
    order_by: Optional[str] = None,
    search_term: Optional[str] = None,
    search_columns: Optional[List[str]] = None
) -> Dict:
    """
    Executa queries no banco de dados Supabase para buscar dados das tabelas do Sienge
    
    Args:
        table_name: Nome da tabela (customers, creditors, enterprises, purchase_invoices, 
                    stock_inventories, accounts_receivable, installment_payments, income_installments)
        columns: Colunas a retornar (padrão: "*")
        filters: Filtros WHERE como dict {"campo": "valor"}
        limit: Limite de registros (padrão: 100, máximo: 1000)
        order_by: Campo para ordenação (ex: "name", "created_at desc")
        search_term: Termo de busca para busca textual
        search_columns: Colunas onde fazer busca textual (se não especificado, usa campos de texto principais)
    
    Returns:
        Dict com success, data, count e query_info
    
    Nota: As queries são executadas no schema 'sienge_data' (fixo)
    """
    # Validação de parâmetros
    if not table_name or not isinstance(table_name, str):
        return {
            "success": False,
            "message": "❌ Nome da tabela é obrigatório e deve ser uma string",
            "error": "INVALID_TABLE_NAME"
        }
    
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        return {
            "success": False,
            "message": "❌ Limite deve ser um número inteiro positivo",
            "error": "INVALID_LIMIT"
        }
    
    if limit and limit > 1000:
        limit = 1000  # Aplicar limite máximo
    
    log.info("Query Supabase: tabela=%s, search_term=%s, limit=%s", table_name, search_term, limit)
    
    return await _query_supabase_internal(
        table_name=table_name,
        columns=columns,
        filters=filters,
        limit=limit,
        order_by=order_by,
        search_term=search_term,
        search_columns=search_columns
    )


async def get_supabase_table_info(table_name: Optional[str] = None) -> Dict:
    """
    Obtém informações sobre as tabelas disponíveis no Supabase ou detalhes de uma tabela específica
    
    Args:
        table_name: Nome da tabela para obter detalhes (opcional)
    
    Returns:
        Dict com informações das tabelas (schema, colunas, indexes, exemplos de uso)
    
    Nota: As tabelas estão no schema 'sienge_data' (fixo)
    """
    if not SUPABASE_AVAILABLE:
        return {
            "success": False,
            "message": "❌ Cliente Supabase não disponível",
            "error": "SUPABASE_NOT_AVAILABLE"
        }
    
    client = _get_supabase_client()
    if not client:
        return {
            "success": False,
            "message": "❌ Cliente Supabase não configurado",
            "error": "SUPABASE_NOT_CONFIGURED"
        }
    
    # Informações das tabelas disponíveis
    tables_info = {
        "customers": {
            "name": "Clientes",
            "description": "Clientes cadastrados no Sienge",
            "columns": ["id", "name", "document", "email", "phone", "customer_type_id", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["name", "document", "email"],
            "indexes": ["document", "name (trigram)", "updated_at"]
        },
        "creditors": {
            "name": "Credores/Fornecedores", 
            "description": "Fornecedores e credores cadastrados",
            "columns": ["id", "name", "document", "bank_info", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["name", "document"],
            "indexes": ["document", "name (trigram)", "updated_at"]
        },
        "enterprises": {
            "name": "Empreendimentos/Obras",
            "description": "Projetos e obras cadastrados",
            "columns": ["id", "code", "name", "description", "company_id", "type", "metadata", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["name", "description", "code"],
            "indexes": ["name (trigram)", "company_id", "updated_at"]
        },
        "purchase_invoices": {
            "name": "Notas Fiscais de Compra",
            "description": "Notas fiscais de compra",
            "columns": ["id", "sequential_number", "supplier_id", "company_id", "movement_date", "issue_date", "series", "notes", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["sequential_number", "notes"],
            "indexes": ["supplier_id", "sequential_number", "updated_at"]
        },
        "installment_payments": {
            "name": "Pagamentos de Parcelas",
            "description": "Pagamentos efetuados para parcelas",
            "columns": [
                "payment_uid", "installment_uid", "operation_type_id", "operation_type_name",
                "gross_amount", "monetary_correction_amount", "interest_amount", "fine_amount",
                "discount_amount", "tax_amount", "net_amount", "calculation_date", "payment_date",
                "sequential_number", "corrected_net_amount", "payment_authentication"
            ],
            "search_fields": ["installment_uid", "payment_uid"],
            "indexes": ["payment_date", "installment_uid", "payment_uid"],
            "amount_columns": ["gross_amount", "net_amount", "corrected_net_amount"]
        },
        "income_installments": {
            "name": "Parcelas de Receita",
            "description": "Parcelas de contas a receber (busca apenas por valores numéricos)",
            "columns": [
                "installment_uid", "bill_id", "installment_id", "company_id", "company_name",
                "business_area_id", "business_area_name", "project_id", "project_name",
                "group_company_id", "group_company_name", "holding_id", "holding_name",
                "subsidiary_id", "subsidiary_name", "business_type_id", "business_type_name",
                "client_id", "client_name", "document_identification_id", "document_identification_name",
                "document_number", "document_forecast", "origin_id", "original_amount",
                "discount_amount", "tax_amount", "indexer_id", "indexer_name", "due_date",
                "issue_date", "bill_date", "installment_base_date", "balance_amount",
                "corrected_balance_amount", "periodicity_type", "embedded_interest_amount",
                "interest_type", "interest_rate", "correction_type", "interest_base_date",
                "defaulter_situation", "sub_judicie", "main_unit", "installment_number",
                "payment_term_id", "payment_term_description", "bearer_id"
            ],
            "search_fields": ["bill_id (numérico)", "client_id (numérico)", "installment_uid"],
            "indexes": ["due_date", "bill_id", "client_id", "installment_uid"],
            "search_note": "Para buscar nesta tabela, use valores numéricos (ex: '123' para bill_id)",
            "amount_columns": ["original_amount", "balance_amount", "corrected_balance_amount"]
        },
        "stock_inventories": {
            "name": "Inventário de Estoque",
            "description": "Inventário e movimentações de estoque",
            "columns": ["id", "cost_center_id", "resource_id", "inventory", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["cost_center_id", "resource_id"],
            "indexes": ["cost_center_id", "resource_id"]
        },
        "accounts_receivable": {
            "name": "Contas a Receber",
            "description": "Contas a receber e movimentações financeiras",
            "columns": ["id", "bill_id", "customer_id", "amount", "due_date", "payment_date", "raw", "updated_at", "last_synced_at", "created_at"],
            "search_fields": ["bill_id", "customer_id"],
            "indexes": ["customer_id", "due_date", "updated_at"]
        },
        "sync_meta": {
            "name": "Metadados de Sincronização",
            "description": "Controle de sincronização entre Sienge e Supabase",
            "columns": ["id", "entity_name", "last_synced_at", "last_record_count", "notes", "created_at"],
            "search_fields": ["entity_name"],
            "indexes": ["entity_name"]
        }
    }
    
    if table_name:
        if table_name in tables_info:
            log.info("Retornando info da tabela: %s", table_name)
            return {
                "success": True,
                "message": f"✅ Informações da tabela '{table_name}'",
                "table_info": tables_info[table_name],
                "table_name": table_name
            }
        else:
            return {
                "success": False,
                "message": f"❌ Tabela '{table_name}' não encontrada",
                "error": "TABLE_NOT_FOUND",
                "available_tables": list(tables_info.keys())
            }
    else:
        log.info("Retornando lista de todas as tabelas (%d)", len(tables_info))
        return {
            "success": True,
            "message": f"✅ {len(tables_info)} tabelas disponíveis no Supabase",
            "schema": SUPABASE_SCHEMA,
            "tables": tables_info,
            "usage_examples": {
                "query_customers": "query_supabase_database('customers', search_term='João')",
                "query_bills_by_date": "query_supabase_database('bills', filters={'due_date': '2024-01-01'})",
                "query_enterprises": "query_supabase_database('enterprises', columns='id,name,description', limit=50)"
            }
        }


async def search_supabase_data(
    search_term: str,
    table_names: Optional[List[str]] = None,
    limit_per_table: Optional[int] = 20
) -> Dict:
    """
    🚀 Busca universal em múltiplas tabelas do Supabase - MAIS EFICIENTE
    
    ⭐ RECOMENDADO para buscas com volume de dados ou quando search_sienge_data não retorna resultados satisfatórios.
    
    Esta ferramenta é mais eficiente que search_sienge_data() porque:
    - Acessa diretamente o banco de dados
    - Busca em múltiplas tabelas simultaneamente
    - Suporte a busca textual e numérica
    - Melhor performance para grandes volumes
    
    Args:
        search_term: Termo de busca
        table_names: Lista de tabelas para buscar (se não especificado, busca em todas)
        limit_per_table: Limite de resultados por tabela (padrão: 20)
    
    Returns:
        Dict com resultados agrupados por tabela
    """
    # Validação de parâmetros
    if not search_term or not isinstance(search_term, str):
        return {
            "success": False,
            "message": "❌ Termo de busca é obrigatório e deve ser uma string",
            "error": "INVALID_SEARCH_TERM"
        }
    
    if limit_per_table is not None and (not isinstance(limit_per_table, int) or limit_per_table <= 0):
        return {
            "success": False,
            "message": "❌ Limite por tabela deve ser um número inteiro positivo",
            "error": "INVALID_LIMIT"
        }
    
    # Validar e processar table_names
    if table_names is not None:
        if not isinstance(table_names, list):
            return {
                "success": False,
                "message": "❌ table_names deve ser uma lista de strings",
                "error": "INVALID_TABLE_NAMES"
            }
        # Filtrar apenas tabelas válidas
        valid_tables = ["customers", "creditors", "enterprises", "purchase_invoices", 
                       "stock_inventories", "accounts_receivable", "sync_meta",
                       "installment_payments", "income_installments"]
        table_names = [t for t in table_names if t in valid_tables]
        if not table_names:
            return {
                "success": False,
                "message": "❌ Nenhuma tabela válida especificada",
                "error": "NO_VALID_TABLES",
                "valid_tables": valid_tables
            }
    else:
        # Tabelas padrão para busca universal
        table_names = ["customers", "creditors", "enterprises", "installment_payments", "income_installments"]
    
    log.info("Busca universal em Supabase: termo='%s', tabelas=%s", search_term, table_names)
    
    results = {}
    total_found = 0
    
    for table_name in table_names:
        try:
            # Chamar a função interna diretamente
            result = await _query_supabase_internal(
                table_name=table_name,
                search_term=search_term,
                limit=limit_per_table or 20
            )
            
            if result["success"]:
                results[table_name] = {
                    "count": result["count"],
                    "data": result["data"][:5] if result["count"] > 5 else result["data"],  # Limitar preview
                    "has_more": result["count"] > 5
                }
                total_found += result["count"]
            else:
                results[table_name] = {
                    "error": result.get("error"),
                    "count": 0
                }
                
        except Exception as e:
            log.error("Erro buscando em %s: %s", table_name, e)
            results[table_name] = {
                "error": str(e),
                "count": 0
            }
    
    if total_found > 0:
        log.info("Busca concluída: %d registros em %d tabelas", total_found, 
                len([t for t in results.values() if t.get('count', 0) > 0]))
        return {
            "success": True,
            "message": f"✅ Busca '{search_term}' encontrou {total_found} registros em {len([t for t in results.values() if t.get('count', 0) > 0])} tabelas",
            "search_term": search_term,
            "total_found": total_found,
            "results_by_table": results,
            "suggestion": "Use query_supabase_database() para buscar especificamente em uma tabela e obter mais resultados"
        }
    else:
        log.info("Busca sem resultados: termo='%s'", search_term)
        return {
            "success": False,
            "message": f"❌ Nenhum resultado encontrado para '{search_term}'",
            "search_term": search_term,
            "searched_tables": table_names,
            "results_by_table": results
        }
