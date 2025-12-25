#!/usr/bin/env python3
"""
SIENGE MCP REFATORADO - Arquitetura Modular
FastMCP com Autenticação Flexível (Bearer Token e Basic Auth)

Estrutura:
- server.py: Core (make_request, cache, parse_error) + registros @mcp.tool
- tools/: Módulos especializados (utilities, master_data, purchases, etc.)
"""

from fastmcp import FastMCP
import httpx
from typing import Dict, List, Optional, Any, Union
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import time
import uuid
import asyncio
import logging
import traceback

# Logger
from .utils.logger import get_logger
logger = get_logger()

# Optional dependencies
try:
    from tenacity import AsyncRetrying, wait_exponential, stop_after_attempt, retry_if_exception_type
    TENACITY_AVAILABLE = True
except Exception:
    TENACITY_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastMCP
mcp = FastMCP("Sienge API Integration 🏗️ - Modular Architecture")

# Configurações da API do Sienge
SIENGE_BASE_URL = os.getenv("SIENGE_BASE_URL", "https://api.sienge.com.br")
SIENGE_SUBDOMAIN = os.getenv("SIENGE_SUBDOMAIN", "")
SIENGE_USERNAME = os.getenv("SIENGE_USERNAME", "")
SIENGE_PASSWORD = os.getenv("SIENGE_PASSWORD", "")
SIENGE_API_KEY = os.getenv("SIENGE_API_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_SCHEMA = "sienge_data"


# ============================================================================
# EXCEÇÕES E PARSERS
# ============================================================================

class SiengeAPIError(Exception):
    """Exceção customizada para erros da API do Sienge"""
    pass


def parse_sienge_error(error_message: str) -> Dict[str, Any]:
    """Parser inteligente de erros da API do Sienge com sugestões contextuais"""
    import re
    
    error_patterns = {
        r"Não é possível utilizar centros de custo que não estão vinculados a empresa do título": {
            "type": "COST_CENTER_MISMATCH",
            "suggestion": "O centro de custo do pedido de compra não pertence à empresa da nota fiscal.",
            "action": "Use validate_purchase_order_company() para verificar a empresa correta antes de criar a NF.",
            "severity": "error",
        },
        r"O código da empresa é inválido": {
            "type": "INVALID_COMPANY_ID",
            "suggestion": "O company_id fornecido não existe no Sienge.",
            "action": "Use get_sienge_projects() para listar empresas válidas.",
            "severity": "error",
        },
        r"Documento NF.+já está cadastrado": {
            "type": "DUPLICATE_INVOICE",
            "suggestion": "Esta nota fiscal já foi cadastrada no Sienge.",
            "action": "Use get_sienge_bills() para buscar o título existente.",
            "severity": "warning",
        },
        r"HTTP 401": {
            "type": "UNAUTHORIZED",
            "suggestion": "Credenciais de autenticação inválidas ou expiradas.",
            "action": "Verifique SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no arquivo .env.",
            "severity": "critical",
        },
        r"HTTP 422": {
            "type": "VALIDATION_ERROR",
            "suggestion": "Erro de validação nos dados enviados.",
            "action": "Verifique os campos obrigatórios e formatos dos dados.",
            "severity": "error",
        },
        r"HTTP 429": {
            "type": "RATE_LIMIT",
            "suggestion": "Limite de requisições excedido (rate limit).",
            "action": "Aguarde alguns segundos. O sistema já faz retry automático.",
            "severity": "warning",
        },
    }
    
    for pattern, info in error_patterns.items():
        if re.search(pattern, error_message, re.IGNORECASE):
            return {
                "type": info["type"],
                "suggestion": info["suggestion"],
                "action": info["action"],
                "severity": info["severity"],
                "original_error": error_message,
                "matched": True,
            }
    
    return {
        "type": "UNKNOWN_ERROR",
        "suggestion": "Erro não catalogado no parser.",
        "action": "Verifique os logs detalhados.",
        "severity": "error",
        "original_error": error_message,
        "matched": False,
    }


# ============================================================================
# FUNÇÕES DE REQUISIÇÃO (CORE)
# ============================================================================

async def make_sienge_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    files: Optional[Dict] = None
) -> Dict:
    """
    Função auxiliar para fazer requisições à API do Sienge (v1)
    Suporta Bearer Token e Basic Auth
    Suporta multipart/form-data via parâmetro 'files'
    """
    request_id = str(uuid.uuid4())
    start_ts = time.time()

    # Headers (não adicionar Content-Type para multipart)
    if files:
        headers = {"Accept": "application/json", "X-Request-Id": request_id}
    else:
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-Request-Id": request_id}

    # Configurar autenticação e URL
    auth = None

    if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
        headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
        url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/v1{endpoint}"
    elif SIENGE_USERNAME and SIENGE_PASSWORD:
        auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
        url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/v1{endpoint}"
    else:
        return {
            "success": False,
            "error": "No Authentication",
            "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
            "request_id": request_id,
        }

    try:
        max_attempts = 5
        attempts = 0
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            while True:
                attempts += 1
                try:
                    response = await client.request(
                        method=method, url=url, headers=headers, params=params,
                        json=json_data, files=files, auth=auth
                    )
                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    logger.warning(f"Request error to {url}: {exc} (attempt {attempts}/{max_attempts})")
                    if attempts >= max_attempts:
                        raise
                    await asyncio.sleep(min(2 ** attempts, 60))
                    continue

                # Handle rate limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_seconds = int(retry_after) if retry_after else min(2 ** attempts, 60)
                    logger.warning(f"HTTP 429 from {url}, retrying after {wait_seconds}s")
                    if attempts >= max_attempts:
                        latency_ms = int((time.time() - start_ts) * 1000)
                        return {
                            "success": False, "error": "HTTP 429", "message": response.text,
                            "status_code": 429, "latency_ms": latency_ms, "request_id": request_id
                        }
                    await asyncio.sleep(wait_seconds)
                    continue

                latency_ms = int((time.time() - start_ts) * 1000)

                if response.status_code in [200, 201, 204]:
                    try:
                        if response.status_code == 204:
                            return {
                                "success": True, "data": None, "status_code": response.status_code,
                                "latency_ms": latency_ms, "request_id": request_id
                            }
                        return {
                            "success": True, "data": response.json(), "status_code": response.status_code,
                            "latency_ms": latency_ms, "request_id": request_id
                        }
                    except Exception:
                        return {
                            "success": True, "data": {"message": "Success"}, "status_code": response.status_code,
                            "latency_ms": latency_ms, "request_id": request_id
                        }
                else:
                    logger.warning(f"HTTP {response.status_code} from {url}: {response.text}")
                    error_info = parse_sienge_error(response.text)
                    
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "message": response.text,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "request_id": request_id,
                        "error_type": error_info.get("type"),
                        "suggestion": error_info.get("suggestion"),
                        "recommended_action": error_info.get("action"),
                        "severity": error_info.get("severity"),
                    }

    except httpx.TimeoutException:
        latency_ms = int((time.time() - start_ts) * 1000)
        return {
            "success": False, "error": "Timeout",
            "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s",
            "latency_ms": latency_ms, "request_id": request_id
        }
    except Exception as e:
        latency_ms = int((time.time() - start_ts) * 1000)
        return {
            "success": False, "error": str(e), "message": f"Erro na requisição: {str(e)}",
            "latency_ms": latency_ms, "request_id": request_id
        }


async def make_sienge_bulk_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None
) -> Dict:
    """Função auxiliar para fazer requisições à API bulk-data do Sienge"""
    request_id = str(uuid.uuid4())
    start_ts = time.time()

    headers = {"Content-Type": "application/json", "Accept": "application/json", "X-Request-Id": request_id}

    auth = None
    if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
        headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
        url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/bulk-data/v1{endpoint}"
    elif SIENGE_USERNAME and SIENGE_PASSWORD:
        auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
        url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/bulk-data/v1{endpoint}"
    else:
        return {
            "success": False,
            "error": "No Authentication",
            "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
            "request_id": request_id,
        }

    try:
        max_attempts = 5
        attempts = 0
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            while True:
                attempts += 1
                try:
                    response = await client.request(
                        method=method, url=url, headers=headers, params=params,
                        json=json_data, auth=auth
                    )
                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    logger.warning(f"Bulk request error: {exc} (attempt {attempts}/{max_attempts})")
                    if attempts >= max_attempts:
                        raise
                    await asyncio.sleep(min(2 ** attempts, 60))
                    continue

                if response.status_code == 429:
                    wait_seconds = min(2 ** attempts, 60)
                    logger.warning(f"HTTP 429 from bulk {url}, retrying after {wait_seconds}s")
                    if attempts >= max_attempts:
                        latency_ms = int((time.time() - start_ts) * 1000)
                        return {
                            "success": False, "error": "HTTP 429", "message": response.text,
                            "status_code": 429, "latency_ms": latency_ms, "request_id": request_id
                        }
                    await asyncio.sleep(wait_seconds)
                    continue

                latency_ms = int((time.time() - start_ts) * 1000)

                if response.status_code in [200, 201, 204]:
                    try:
                        if response.status_code == 204:
                            return {
                                "success": True, "data": None, "status_code": response.status_code,
                                "latency_ms": latency_ms, "request_id": request_id
                            }
                        return {
                            "success": True, "data": response.json(), "status_code": response.status_code,
                            "latency_ms": latency_ms, "request_id": request_id
                        }
                    except Exception:
                        return {
                            "success": True, "data": {"message": "Success"}, "status_code": response.status_code,
                            "latency_ms": latency_ms, "request_id": request_id
                        }
                else:
                    logger.warning(f"HTTP {response.status_code} from bulk {url}: {response.text}")
                    error_info = parse_sienge_error(response.text)
                    
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "message": response.text,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "request_id": request_id,
                        "error_type": error_info.get("type"),
                        "suggestion": error_info.get("suggestion"),
                        "recommended_action": error_info.get("action"),
                        "severity": error_info.get("severity"),
                    }

    except httpx.TimeoutException:
        latency_ms = int((time.time() - start_ts) * 1000)
        return {
            "success": False, "error": "Timeout",
            "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s",
            "latency_ms": latency_ms, "request_id": request_id
        }
    except Exception as e:
        latency_ms = int((time.time() - start_ts) * 1000)
        return {
            "success": False, "error": str(e), "message": f"Erro na requisição bulk-data: {str(e)}",
            "latency_ms": latency_ms, "request_id": request_id
        }


# ============================================================================
# CACHE IN-MEMORY
# ============================================================================

_SIMPLE_CACHE: Dict[str, Dict[str, Any]] = {}


def _simple_cache_set(key: str, value: Dict[str, Any], ttl: int = 60) -> None:
    """Armazena valor no cache in-memory com TTL"""
    expire_at = int(time.time()) + int(ttl)
    _SIMPLE_CACHE[key] = {"value": value, "expire_at": expire_at}
    
    if len(_SIMPLE_CACHE) % 100 == 0:
        _cache_cleanup()


def _simple_cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Recupera valor do cache in-memory"""
    item = _SIMPLE_CACHE.get(key)
    if not item:
        return None
    if int(time.time()) > item.get("expire_at", 0):
        try:
            del _SIMPLE_CACHE[key]
        except KeyError:
            pass
        return None
    return item.get("value")


def _cache_cleanup() -> None:
    """Remove entradas expiradas do cache"""
    now = int(time.time())
    expired_keys = [k for k, v in _SIMPLE_CACHE.items() if now > v.get("expire_at", 0)]
    for k in expired_keys:
        try:
            del _SIMPLE_CACHE[k]
        except KeyError:
            pass
    if expired_keys:
        logger.debug(f"Cache cleanup: removidas {len(expired_keys)} entradas")


def _cache_invalidate(pattern: str) -> None:
    """Invalida entradas do cache que correspondem ao padrão"""
    keys_to_delete = [k for k in _SIMPLE_CACHE.keys() if pattern in k]
    for k in keys_to_delete:
        try:
            del _SIMPLE_CACHE[k]
        except KeyError:
            pass
    if keys_to_delete:
        logger.debug(f"Cache invalidated: {len(keys_to_delete)} entradas com padrão '{pattern}'")


async def _fetch_all_paginated(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    page_size: int = 200,
    max_records: Optional[int] = None,
    results_key: str = "results",
    use_bulk: bool = False,
) -> List[Dict[str, Any]]:
    """Helper para buscar todas as páginas de um endpoint paginado (limit/offset)"""
    params = dict(params or {})
    all_items: List[Dict[str, Any]] = []
    offset = int(params.get("offset", 0) or 0)
    page_size = min(int(page_size), 200)

    while True:
        params["limit"] = page_size
        params["offset"] = offset

        requester = make_sienge_bulk_request if use_bulk else make_sienge_request
        result = await requester("GET", endpoint, params=params)

        if not result.get("success"):
            return {"success": False, "error": result.get("error"), "message": result.get("message")}

        data = result.get("data")

        if use_bulk:
            items = data.get("data", []) if isinstance(data, dict) else data
        else:
            items = data.get(results_key, []) if isinstance(data, dict) else data

        if not isinstance(items, list):
            all_items.append(items)
            break

        all_items.extend(items)

        if max_records and len(all_items) >= int(max_records):
            return all_items[: int(max_records)]

        if len(items) < page_size:
            break

        offset += len(items) if len(items) > 0 else page_size

    return all_items


def _get_auth_info_internal() -> Dict:
    """Função interna para verificar configuração de autenticação"""
    if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
        return {
            "auth_method": "Bearer Token",
            "configured": True,
            "base_url": SIENGE_BASE_URL,
            "api_key_configured": True
        }
    elif SIENGE_USERNAME and SIENGE_PASSWORD:
        return {
            "auth_method": "Basic Auth",
            "configured": True,
            "base_url": SIENGE_BASE_URL,
            "subdomain": SIENGE_SUBDOMAIN,
            "username": SIENGE_USERNAME,
        }
    else:
        return {
            "auth_method": "None",
            "configured": False,
            "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
        }


# ============================================================================
# IMPORTAR MÓDULOS DAS TOOLS
# ============================================================================

from .tools import utilities
from .tools import master_data
from .tools import inventory
from .tools import purchases
from .tools import financial
from .tools import accounts_payable
from .tools import supabase_tools


# ============================================================================
# REGISTRAR TOOLS COM @mcp.tool
# ============================================================================

# ────────────────────────────────────────────────────────────────────────────
# UTILITIES (4 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def test_sienge_connection() -> Dict:
    """Testa conexão com API do Sienge e valida autenticação"""
    config = {
        "SIENGE_API_KEY": SIENGE_API_KEY,
        "SIENGE_USERNAME": SIENGE_USERNAME,
        "SIENGE_PASSWORD": SIENGE_PASSWORD,
    }
    return await utilities.test_sienge_connection(make_sienge_request, config)


@mcp.tool
async def list_sienge_entities() -> Dict:
    """Lista todas as entidades disponíveis na API do Sienge"""
    return await utilities.list_sienge_entities()


@mcp.tool
async def search_sienge_data(query: str, entity_types: Optional[List[str]] = None, limit_per_entity: int = 10) -> Dict:
    """Busca universal em múltiplas entidades do Sienge"""
    # Criar wrappers para as funções de busca
    async def get_customers_wrapper(**kwargs):
        return await master_data.get_sienge_customers(
            make_sienge_request, _simple_cache_get, _simple_cache_set, _fetch_all_paginated,
            kwargs.get("limit", 50), kwargs.get("offset", 0), kwargs.get("search"), None, False, None
        )
    
    async def get_creditors_wrapper(**kwargs):
        return await master_data.get_sienge_creditors(
            make_sienge_request, _simple_cache_get, _simple_cache_set, _fetch_all_paginated,
            kwargs.get("limit", 50), kwargs.get("offset", 0), kwargs.get("search"), False, None
        )
    
    async def get_projects_wrapper(**kwargs):
        return await master_data.get_sienge_projects(
            make_sienge_request,
            kwargs.get("limit", 100),
            kwargs.get("offset", 0),
            kwargs.get("company_id"),
            None,  # enterprise_type
            None,  # receivable_register
            False  # only_buildings_enabled
        )
    
    async def get_bills_wrapper(**kwargs):
        # Para bills, precisamos usar a tool de financial
        from .tools import financial
        return await financial.get_sienge_bills(
            make_sienge_request,
            kwargs.get("start_date", "2024-01-01"),
            kwargs.get("end_date", "2024-12-31"),
            kwargs.get("creditor_id"),
            kwargs.get("limit", 100)
        )
    
    async def get_purchase_orders_wrapper(**kwargs):
        from .tools import purchases
        return await purchases.get_sienge_purchase_orders(
            make_sienge_request,
            kwargs.get("supplier_id"),
            kwargs.get("building_id"),
            kwargs.get("limit", 100)
        )
    
    # Converter entity_types (lista) para entity_type (string única) se necessário
    entity_type = entity_types[0] if entity_types and len(entity_types) == 1 else None
    
    return await utilities.search_sienge_data(
        get_customers_wrapper,
        get_creditors_wrapper,
        get_projects_wrapper,
        get_bills_wrapper,
        get_purchase_orders_wrapper,
        query,
        entity_type,
        limit_per_entity,
        None
    )


@mcp.tool
async def get_sienge_data_paginated(
    entity_type: str,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None
) -> Dict:
    """
    Busca dados paginados do Sienge.
    
    Args:
        entity_type: Tipo de entidade (customers, creditors, projects, bills)
        page: Número da página (começando em 1)
        page_size: Registros por página (máximo 50)
        filters: Filtros específicos da entidade
        sort_by: Campo para ordenação (se suportado)
    """
    # Criar wrappers para as funções de busca
    async def get_customers_wrapper(**kwargs):
        return await master_data.get_sienge_customers(
            make_sienge_request, _simple_cache_get, _simple_cache_set, _fetch_all_paginated,
            kwargs.get("limit", 50), kwargs.get("offset", 0), kwargs.get("search"), None, False, None
        )
    
    async def get_creditors_wrapper(**kwargs):
        return await master_data.get_sienge_creditors(
            make_sienge_request, _simple_cache_get, _simple_cache_set, _fetch_all_paginated,
            kwargs.get("limit", 50), kwargs.get("offset", 0), kwargs.get("search"), False, None
        )
    
    async def get_projects_wrapper(**kwargs):
        return await master_data.get_sienge_projects(
            make_sienge_request,
            kwargs.get("limit", 100),
            kwargs.get("offset", 0),
            kwargs.get("company_id"),
            None,  # enterprise_type
            None,  # receivable_register
            False  # only_buildings_enabled
        )
    
    async def get_bills_wrapper(**kwargs):
        from .tools import financial
        return await financial.get_sienge_bills(
            make_sienge_request,
            kwargs.get("start_date", "2024-01-01"),
            kwargs.get("end_date", "2024-12-31"),
            None,  # debtor_id
            kwargs.get("creditor_id"),
            None,  # cost_center_id
            None,  # documents_identification_id
            None,  # document_number
            None,  # status
            None,  # origin_id
            kwargs.get("limit", 100),
            kwargs.get("offset", 0)
        )
    
    return await utilities.get_sienge_data_paginated(
        get_customers_wrapper,
        get_creditors_wrapper,
        get_projects_wrapper,
        get_bills_wrapper,
        entity_type,
        page,
        page_size,
        filters,
        sort_by
    )


# ────────────────────────────────────────────────────────────────────────────
# MASTER DATA (10 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def get_sienge_customers(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    fetch_all: bool = False,
    max_records: Optional[int] = None,
) -> Dict:
    """
    Busca clientes no Sienge.
    
    Por padrão usa paginação simples (limit/offset). Se fetch_all=True,
    usa o helper _fetch_all_paginated para varrer todas as páginas.
    """
    return await master_data.get_sienge_customers(
        make_sienge_request,
        _simple_cache_get,
        _simple_cache_set,
        _fetch_all_paginated,
        limit,
        offset,
        search,
        None,          # customer_type_id
        fetch_all,
        max_records,
    )


@mcp.tool
async def get_sienge_creditors(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    fetch_all: bool = False,
    max_records: Optional[int] = None,
) -> Dict:
    """
    Busca credores/fornecedores no Sienge.
    
    Usa cache in-memory e pode varrer todas as páginas se fetch_all=True.
    """
    return await master_data.get_sienge_creditors(
        make_sienge_request,
        _simple_cache_get,
        _simple_cache_set,
        _fetch_all_paginated,
        limit,
        offset,
        search,
        fetch_all,
        max_records,
    )


@mcp.tool
async def get_sienge_projects(company_id: Optional[int] = None, limit: int = 100) -> Dict:
    """Busca projetos/empreendimentos no Sienge"""
    return await master_data.get_sienge_projects(make_sienge_request, limit, 0, company_id, None, None, False)


@mcp.tool
async def get_sienge_enterprises(company_id: Optional[int] = None, limit: int = 100) -> Dict:
    """Busca empreendimentos/obras no Sienge (alias para get_sienge_projects)"""
    return await master_data.get_sienge_projects(make_sienge_request, limit, 0, company_id, None, None, False)


@mcp.tool
async def get_sienge_payment_categories(limit: int = 200) -> Dict:
    """Busca categorias de plano financeiro"""
    return await master_data.get_sienge_payment_categories(
        make_sienge_request,
        _simple_cache_get,
        _simple_cache_set
    )


@mcp.tool
async def get_sienge_cost_centers(limit: int = 200, offset: int = 0) -> Dict:
    """Busca centros de custo no Sienge ordenados pelo código id"""
    return await master_data.get_sienge_cost_centers(make_sienge_request, limit, offset)


@mcp.tool
async def get_sienge_project_units(project_id: int, limit: int = 200) -> Dict:
    """Busca unidades de um empreendimento"""
    # TODO: Implementar get_sienge_project_units em master_data.py ou usar endpoint específico
    # Por enquanto, retornar erro informativo
    return {
        "success": False,
        "message": f"❌ Função get_sienge_project_units ainda não implementada",
        "error": "NOT_IMPLEMENTED",
        "suggestion": f"Use get_sienge_enterprise_groupings(enterprise_id={project_id}) para obter agrupamentos de unidades"
    }


@mcp.tool
async def get_sienge_enterprise_groupings(enterprise_id: int, limit: int = 100) -> Dict:
    """Busca agrupamentos de unidades de um empreendimento"""
    # A função não aceita limit, mas mantemos o parâmetro para compatibilidade
    return await master_data.get_sienge_enterprise_groupings(make_sienge_request, enterprise_id)


@mcp.tool
async def get_sienge_customer_types() -> Dict:
    """Busca tipos de cliente"""
    return await master_data.get_sienge_customer_types(make_sienge_request)


# ────────────────────────────────────────────────────────────────────────────
# INVENTORY (2 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def get_sienge_stock_inventory(
    cost_center_id: Optional[Union[int, str]] = None,
    resource_id: Optional[Union[int, str]] = None,
    limit: Union[int, str] = 100
) -> Dict:
    """Busca inventário de estoque por centro de custo"""
    # Converter para int se necessário (workaround para serialização do MCP)
    if cost_center_id is not None:
        try:
            cost_center_id = int(cost_center_id)
        except (ValueError, TypeError):
            cost_center_id = None
    
    if resource_id is not None:
        try:
            resource_id = int(resource_id)
        except (ValueError, TypeError):
            resource_id = None
    
    if limit is not None:
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 100
    
    return await inventory.get_sienge_stock_inventory(make_sienge_request, cost_center_id, resource_id, limit)


@mcp.tool
async def get_sienge_stock_reservations(limit: int = 100) -> Dict:
    """Busca reservas de estoque"""
    return await inventory.get_sienge_stock_reservations(make_sienge_request, limit)


# ────────────────────────────────────────────────────────────────────────────
# PURCHASES (14 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def get_sienge_purchase_orders(
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
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """
    Busca pedidos de compra.
    
    Parâmetros opcionais:
    - purchase_order_id: ID do pedido de compra específico (se fornecido, retorna apenas esse pedido)
    - start_date: Data de início (formato yyyy-MM-dd, ex: 2018-03-01 ou yyyyMMdd, ex: 20180301)
    - end_date: Data de fim (formato yyyy-MM-dd, ex: 2018-03-11 ou yyyyMMdd, ex: 20180311)
    
    ⚠️ NOTA: Se o formato yyyy-MM-dd não funcionar devido a problemas no MCP,
    use o formato sem hífens: yyyyMMdd (ex: 20251215 para 15/12/2025)
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
    return await purchases.get_sienge_purchase_orders(
        make_sienge_request,
        _simple_cache_get,
        _simple_cache_set,
        purchase_order_id,
        start_date,
        end_date,
        status,
        authorized,
        supplier_id,
        building_id,
        buyer_id,
        status_approval,
        consistency,
        limit,
        offset
    )


@mcp.tool
async def get_sienge_purchase_order_items(order_id: int) -> Dict:
    """Busca itens de um pedido de compra"""
    return await purchases.get_sienge_purchase_order_items(make_sienge_request, str(order_id))


@mcp.tool
async def get_sienge_purchase_invoices(
    supplier_id: Optional[int] = None,
    limit: int = 100,
    sequential_number: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    bill_id: Optional[int] = None,
) -> Dict:
    """
    Busca notas fiscais de compra.
    
    IMPORTANTE: É necessário fornecer pelo menos um dos filtros:
    - sequential_number: número sequencial da NF
    - purchase_order_id: ID do pedido de compra  
    - bill_id: ID do título a pagar
    
    Para buscar uma NF específica, use get_purchase_invoice_by_sequential().
    """
    return await purchases.get_sienge_purchase_invoices(
        make_sienge_request,
        supplier_id,
        limit,
        sequential_number,
        purchase_order_id,
        bill_id
    )


@mcp.tool
async def create_sienge_purchase_invoice(
    document_id: str,
    number: str,
    supplier_id: int,
    company_id: int,
    movement_type_id: int,
    movement_date: str,
    issue_date: str,
    series: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict:
    """Cria nota fiscal de compra"""
    return await purchases.create_sienge_purchase_invoice(
        make_sienge_request,
        document_id,
        number,
        supplier_id,
        company_id,
        movement_type_id,
        movement_date,
        issue_date,
        series,
        notes
    )


@mcp.tool
async def add_items_to_purchase_invoice(
    invoice_sequential_number: int,
    deliveries_order: List[Dict[str, Any]],
    copy_notes_purchase_orders: bool = True,
    copy_attachments_purchase_orders: bool = True
) -> Dict:
    """Adiciona itens à nota fiscal de compra via delivery schedules"""
    return await purchases.add_items_to_purchase_invoice(
        make_sienge_request,
        invoice_sequential_number,
        deliveries_order,
        copy_notes_purchase_orders,
        copy_attachments_purchase_orders
    )


@mcp.tool
async def validate_purchase_order_company(
    purchase_order_id: int,
    company_id: Optional[int] = None
) -> Dict:
    """Valida empresa de pedido de compra antes de criar NF (previne HTTP 422)"""
    return await purchases.validate_purchase_order_company(
        make_sienge_request,
        logger,
        str(purchase_order_id),
        company_id
    )


@mcp.tool
async def get_purchase_invoice_by_sequential(sequential_number: int) -> Dict:
    """
    Busca nota fiscal de compra por sequential number.
    
    O sequential_number é o número interno do Sienge, gerado quando a NF é criada.
    Este NÃO é o número da NF que aparece no DANFE.
    
    Para buscar pelo número da NF (ex: "1165562"), use as tools do Supabase:
    - search_supabase_data(search_term="1165562", table_names=["purchase_invoices"])
    - query_supabase_database(table_name="purchase_invoices", search_term="1165562")
    
    Args:
        sequential_number: Número sequencial interno do Sienge
    """
    return await purchases.get_sienge_purchase_invoice(make_sienge_request, sequential_number)


@mcp.tool
async def get_sienge_purchase_requests(limit: int = 100) -> Dict:
    """Busca requisições de compra"""
    return await purchases.get_sienge_purchase_requests(make_sienge_request, limit)


@mcp.tool
async def get_sienge_purchase_request_items(request_id: int, limit: int = 200) -> Dict:
    """Busca itens de uma requisição de compra"""
    return await purchases.get_sienge_purchase_request_items(make_sienge_request, request_id, limit)


@mcp.tool
async def get_sienge_purchase_order_deliveries_attended(
    sequential_number: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    bill_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """Busca entregas atendidas de pedidos de compra"""
    return await purchases.get_sienge_purchase_invoices_deliveries_attended(
        make_sienge_request,
        bill_id,
        sequential_number,
        purchase_order_id,
        None,  # invoice_item_number
        None,  # purchase_order_item_number
        limit,
        offset
    )


@mcp.tool
async def process_purchase_invoice_pipeline(
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
    options: Optional[Dict[str, Any]] = None
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
    # Adicionar make_bulk_request às options se não estiver presente
    if options is None:
        options = {}
    if "make_bulk_request" not in options:
        options["make_bulk_request"] = make_sienge_bulk_request
    
    return await purchases.process_purchase_invoice_pipeline(
        make_sienge_request,
        logger,
        invoice,
        sequential_number,
        deliveries_order,
        installments,
        bill_id,
        attachment_path,
        attachment_description,
        attachment_file_name,
        attachment_file_content_base64,
        attachment_content_type,
        options
    )


# ────────────────────────────────────────────────────────────────────────────
# FINANCIAL (5 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def get_sienge_accounts_receivable(
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
    Busca contas a receber via bulk-data.
    
    Parâmetros obrigatórios:
    - start_date: Data de início (formato yyyy-MM-dd, ex: 2025-12-01)
    - end_date: Data de fim (formato yyyy-MM-dd, ex: 2025-12-31)
    
    Parâmetros opcionais:
    - selection_type: Tipo de seleção (I=emissão, D=vencimento, P=pagamento, B=competência) - padrão: D
    - company_id: Código da empresa
    - cost_centers_id: Lista de códigos de centro de custo
    - correction_indexer_id: Código do indexador de correção
    - correction_date: Data para correção do indexador (yyyy-MM-dd)
    - change_start_date: Data inicial de alteração (yyyy-MM-dd)
    - completed_bills: Filtrar por títulos completos (S)
    - origins_ids: Códigos dos módulos de origem (CR, CO, ME, CA, CI, AR, SC, LO, NE, NS, AC, NF)
    - bearers_id_in: Filtrar parcelas com códigos de portador específicos
    - bearers_id_not_in: Filtrar parcelas excluindo códigos de portador específicos
    """
    return await financial.get_sienge_accounts_receivable(
        make_sienge_bulk_request,
        start_date,
        end_date,
        selection_type,
        company_id,
        cost_centers_id,
        correction_indexer_id,
        correction_date,
        change_start_date,
        completed_bills,
        origins_ids,
        bearers_id_in,
        bearers_id_not_in
    )


@mcp.tool
async def get_sienge_accounts_receivable_by_bills(
    bills_ids: List[int],
    correction_indexer_id: Optional[int] = None,
    correction_date: Optional[str] = None
) -> Dict:
    """
    Busca contas a receber por lista de bill_ids.
    
    Parâmetros obrigatórios:
    - bills_ids: Lista de IDs dos títulos a receber
    
    Parâmetros opcionais:
    - correction_indexer_id: Código do indexador de correção
    - correction_date: Data para correção do indexador (formato yyyy-MM-dd)
    """
    return await financial.get_sienge_accounts_receivable_by_bills(
        make_sienge_bulk_request,
        bills_ids,
        correction_indexer_id,
        correction_date
    )


@mcp.tool
async def get_sienge_bills(
    start_date: str,
    end_date: str,
    debtor_id: Optional[int] = None,
    creditor_id: Optional[int] = None,
    cost_center_id: Optional[int] = None,
    documents_identification_id: Optional[List[str]] = None,
    document_number: Optional[str] = None,
    status: Optional[str] = None,
    origin_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """
    Busca títulos a pagar (bills) com filtros obrigatórios de data.
    
    Parâmetros obrigatórios:
    - start_date: Data inicial (formato ISO 8601 yyyy-MM-dd, ex: 2018-01-01)
    - end_date: Data final (formato ISO 8601 yyyy-MM-dd, ex: 2018-01-01)
    
    Parâmetros opcionais:
    - debtor_id: Código da empresa cadastrada no Sienge
    - creditor_id: Código do credor cadastrado no Sienge
    - cost_center_id: Código do centro de custo cadastrado no Sienge
    - documents_identification_id: Lista de códigos do documento (máx 4)
    - document_number: Número do documento vinculado ao título (máx 20 caracteres)
    - status: Tipo de consistência (S=Completo, N=Incompleto, I=Em inclusão)
    - origin_id: Código de origem (AC, RA, AI, CO, CF, CP, ME, MO, DV, RF, FP, FE, GI, LO, SE)
    - limit: Quantidade máxima de resultados (padrão: 100, máx: 200)
    - offset: Deslocamento na lista (padrão: 0)
    
    IMPORTANTE: O endpoint /bills pode não estar disponível em todas as instâncias do Sienge.
    Se retornar erro 404, o endpoint não está habilitado na sua instância.
    Nesse caso, use as tools do Supabase para buscar títulos sincronizados.
    """
    return await financial.get_sienge_bills(
        make_sienge_request,
        start_date,
        end_date,
        debtor_id,
        creditor_id,
        cost_center_id,
        documents_identification_id,
        document_number,
        status,
        origin_id,
        limit,
        offset
    )


@mcp.tool
async def search_sienge_financial_data(
    period_start: str,
    period_end: str,
    search_type: str = "both",
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    customer_creditor_search: Optional[str] = None
) -> Dict:
    """
    Busca avançada em dados financeiros (contas a receber e pagar).
    
    Parâmetros obrigatórios:
    - period_start: Data inicial do período (formato yyyy-MM-dd, ex: 2025-12-01)
    - period_end: Data final do período (formato yyyy-MM-dd, ex: 2025-12-31)
    
    Parâmetros opcionais:
    - search_type: Tipo de busca ("receivable", "payable", "both") - padrão: "both"
    - amount_min: Valor mínimo para filtrar
    - amount_max: Valor máximo para filtrar
    - customer_creditor_search: Buscar por nome de cliente/credor
    """
    async def get_accounts_receivable_wrapper(start_date: str, end_date: str, selection_type: str = "D"):
        return await financial.get_sienge_accounts_receivable(
            make_sienge_bulk_request,
            start_date,
            end_date,
            selection_type
        )
    
    async def get_bills_wrapper(start_date: str, end_date: str, limit: int = 100):
        return await financial.get_sienge_bills(
            make_sienge_request,
            start_date,
            end_date,
            None, None, None, None, None, None, None,
            limit,
            0
        )
    
    return await financial.search_sienge_financial_data(
        get_accounts_receivable_wrapper,
        get_bills_wrapper,
        period_start,
        period_end,
        search_type,
        amount_min,
        amount_max,
        customer_creditor_search
    )


@mcp.tool
async def get_sienge_dashboard_summary() -> Dict:
    """Dashboard com resumo completo do Sienge (conexão, clientes, projetos, etc.)"""
    config = {
        "SIENGE_API_KEY": SIENGE_API_KEY,
        "SIENGE_USERNAME": SIENGE_USERNAME,
        "SIENGE_PASSWORD": SIENGE_PASSWORD,
    }
    
    async def test_connection_wrapper():
        return await utilities.test_sienge_connection(make_sienge_request, config)
    
    async def get_customers_wrapper(limit: int = 50):
        return await master_data.get_sienge_customers(
            make_sienge_request, _simple_cache_get, _simple_cache_set, _fetch_all_paginated,
            limit, 0, None, None, False, None
        )
    
    async def get_projects_wrapper(limit: int = 100):
        return await master_data.get_sienge_projects(
            make_sienge_request, limit, 0, None, None, None, False
        )
    
    async def get_bills_wrapper(limit: int = 100):
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return await financial.get_sienge_bills(
            make_sienge_request,
            yesterday,  # start_date
            today,  # end_date
            None,  # debtor_id
            None,  # creditor_id
            None,  # cost_center_id
            None,  # documents_identification_id
            None,  # document_number
            None,  # status
            None,  # origin_id
            limit,  # limit
            0  # offset
        )
    
    async def get_customer_types_wrapper():
        return await master_data.get_sienge_customer_types(make_sienge_request)
    
    return await financial.get_sienge_dashboard_summary(
        test_connection_wrapper,
        get_customers_wrapper,
        get_projects_wrapper,
        get_bills_wrapper,
        get_customer_types_wrapper
    )


@mcp.tool
async def create_purchase_invoice_simple(
    document_id: str,
    number: str,
    supplier_id: int,
    company_id: int,
    movement_type_id: int,
    movement_date: str,
    issue_date: str,
    series: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict:
    """
    Versão simplificada: Cria nota fiscal de compra com parâmetros individuais.
    Use esta tool para criar a NF, depois use add_items_to_purchase_invoice para adicionar itens.
    """
    invoice = {
        "documentId": document_id,
        "number": number,
        "supplierId": supplier_id,
        "companyId": company_id,
        "movementTypeId": movement_type_id,
        "movementDate": movement_date,
        "issueDate": issue_date,
    }
    if series:
        invoice["series"] = series
    if notes:
        invoice["notes"] = notes
    
    result = await make_sienge_request("POST", "/purchase-invoices", json_data=invoice)
    
    if result.get("success"):
        data = result.get("data", {})
        seq_num = data.get("sequentialNumber") or data.get("id")
        return {
            "success": True,
            "message": f"✅ Nota fiscal {number} criada com sucesso",
            "sequentialNumber": seq_num,
            "invoice": data
        }
    
    return {
        "success": False,
        "message": f"❌ Erro ao criar nota fiscal {number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ────────────────────────────────────────────────────────────────────────────
# ACCOUNTS PAYABLE (10 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def ap_update_auto_bill_installments(
    sequential_number: int,
    bill_id: Optional[int] = None,
    due_dates: Optional[List[str]] = None,
    days_to_due: Optional[List[int]] = None,
    base_date: Optional[str] = None,
    amounts: Optional[List[float]] = None
) -> Dict:
    """Atualiza parcelas do título criado automaticamente pelo Sienge ao lançar NF"""
    return await accounts_payable.ap_update_auto_bill_installments(
        make_sienge_request,
        make_sienge_bulk_request,
        sequential_number,
        bill_id,
        due_dates,
        days_to_due,
        base_date,
        amounts
    )


@mcp.tool
async def ap_patch_bill(
    bill_id: int,
    document_identification_id: Optional[str] = None,
    document_number: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None
) -> Dict:
    """Atualiza campos do título via PATCH"""
    return await accounts_payable.ap_patch_bill(
        make_sienge_request,
        bill_id,
        document_identification_id,
        document_number,
        extra_fields
    )


@mcp.tool
async def ap_attach_bill(
    bill_id: int,
    description: str,
    file_path: Optional[str] = None,
    file_name: Optional[str] = None,
    file_content_base64: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict:
    """Anexa arquivo ao título via multipart/form-data"""
    return await accounts_payable.ap_attach_bill(
        make_sienge_request,
        bill_id,
        description,
        file_path,
        file_name,
        file_content_base64,
        content_type
    )


@mcp.tool
async def ap_finalize_bill(
    bill_id: int,
    patch_body: Optional[Dict[str, Any]] = None,
    attachment: Optional[Dict[str, Any]] = None,
    audit: bool = True
) -> Dict:
    """Orquestrador: PATCH + anexo + auditoria em um único comando"""
    return await accounts_payable.ap_finalize_bill(
        make_sienge_request,
        bill_id,
        patch_body,
        attachment,
        audit
    )


@mcp.tool
async def ap_list_installments(bill_id: int) -> Dict:
    """Lista parcelas de um título"""
    return await accounts_payable.ap_list_installments(make_sienge_request, bill_id)


@mcp.tool
async def ap_audit_bill_completeness(bill_id: int) -> Dict:
    """Audita completude do título: valores, parcelas, anexos"""
    return await accounts_payable.ap_audit_bill_completeness(make_sienge_request, bill_id)


@mcp.tool
async def ap_create_bill(bill: Dict[str, Any], force_create: bool = False) -> Dict:
    """[DEPRECATED] Cria título manualmente (Sienge cria automaticamente ao lançar NF)"""
    return await accounts_payable.ap_create_bill(make_sienge_request, bill, force_create)


# ────────────────────────────────────────────────────────────────────────────
# SUPABASE (3 tools)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
async def query_supabase_database(
    table_name: str,
    columns: Optional[str] = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = 100,
    order_by: Optional[str] = None,
    search_term: Optional[str] = None,
    search_columns: Optional[List[str]] = None
) -> Dict:
    """Executa queries no banco de dados Supabase"""
    return await supabase_tools.query_supabase_database(
        table_name,
        columns,
        filters,
        limit,
        order_by,
        search_term,
        search_columns
    )


@mcp.tool
async def get_supabase_table_info(table_name: Optional[str] = None) -> Dict:
    """Obtém informações sobre as tabelas disponíveis no Supabase"""
    return await supabase_tools.get_supabase_table_info(table_name)


@mcp.tool
async def search_supabase_data(
    search_term: str,
    table_names: Optional[List[str]] = None,
    limit_per_table: Optional[int] = 20
) -> Dict:
    """Busca universal em múltiplas tabelas do Supabase (mais eficiente que API)"""
    return await supabase_tools.search_supabase_data(search_term, table_names, limit_per_table)


# ────────────────────────────────────────────────────────────────────────────
# UTILITY TOOL
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool
def get_auth_info() -> Dict:
    """Retorna informações sobre a configuração de autenticação"""
    return _get_auth_info_internal()


@mcp.tool
def add(a: int, b: int) -> int:
    """Soma dois números (função de teste)"""
    return a + b


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Entry point for the Sienge MCP Server"""
    print("* Iniciando Sienge MCP Server (Arquitetura Modular)")
    print("=" * 60)

    auth_info = _get_auth_info_internal()
    print(f"* Autenticacao: {auth_info['auth_method']}")
    print(f"* Configurado: {auth_info['configured']}")
    print(f"* Base URL: {auth_info.get('base_url', 'N/A')}")

    if not auth_info["configured"]:
        print("\n* ERRO: Autenticacao nao configurada!")
        print("\nConfigure as variaveis de ambiente:")
        print("- SIENGE_API_KEY (Bearer Token) OU")
        print("- SIENGE_USERNAME + SIENGE_PASSWORD + SIENGE_SUBDOMAIN (Basic Auth)")
        print("")
        print("Exemplo no Windows PowerShell:")
        print('$env:SIENGE_USERNAME="seu_usuario"')
        print('$env:SIENGE_PASSWORD="sua_senha"')
        print('$env:SIENGE_SUBDOMAIN="sua_empresa"')
    else:
        print("\n* Servidor MCP pronto para uso!")
        print("* Tools registradas: 48")

    print("=" * 60)
    mcp.run()


if __name__ == "__main__":
    main()
