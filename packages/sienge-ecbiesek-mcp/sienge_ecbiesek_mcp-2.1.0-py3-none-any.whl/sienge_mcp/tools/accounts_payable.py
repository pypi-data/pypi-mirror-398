"""
Accounts Payable Tools - Ferramentas de contas a pagar
Títulos, Parcelas, Anexos, Auditorias, Workflows Completos
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import logging
import traceback

# Logger
log = logging.getLogger("sienge_mcp.ap")


# ============ HELPER FUNCTIONS ============

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
    for k in ("totalAmount", "invoiceTotal", "amount", "total", "grandTotal", "netAmount", "grossAmount"):
        v = invoice.get(k)
        if v is not None:
            try:
                return Decimal(str(v))
            except Exception:
                pass
    return None


def _iso(d: datetime) -> str:
    """Formata datetime para string ISO date"""
    return d.strftime("%Y-%m-%d")


def _as_decimal(val: Any) -> Optional[Decimal]:
    """Converte valor para Decimal com segurança"""
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _get(obj: Any, key: str) -> Any:
    """Get seguro de dicionário"""
    if isinstance(obj, dict):
        return obj.get(key)
    return None


# ============ DESCOBERTA AUTOMÁTICA DE BILL_ID (4 FALLBACKS) ============

async def _try_bill_from_deliveries_attended(make_request, sequential_number: int) -> Optional[int]:
    """
    Fallback #0: Tenta via endpoint deliveries-attended (método original, rápido mas nem sempre funciona)
    """
    try:
        r = await make_request(
            "GET",
            "/purchase-invoices/deliveries-attended",
            params={"sequentialNumber": sequential_number, "limit": 1, "offset": 0}
        )
        if r.get("success"):
            data = r.get("data") or {}
            rows = data.get("results", []) if isinstance(data, dict) else data or []
            if rows:
                bid = rows[0].get("billId")
                try:
                    if bid is not None:
                        log.info("Fallback #0 (deliveries-attended) encontrou billId %s", bid)
                        return int(bid)
                except Exception:
                    pass
    except Exception as e:
        log.debug("Fallback #0 (deliveries-attended) falhou: %s", e)
    return None


async def _try_bill_from_invoice(make_request, sequential_number: int) -> Optional[int]:
    """
    Fallback #1: Tenta encontrar billId dentro do GET /purchase-invoices/{seq}
    Algumas configurações do Sienge expõem o vínculo direto na NF
    """
    try:
        r = await make_request("GET", f"/purchase-invoices/{sequential_number}")
        if not r.get("success"):
            return None
        inv = r.get("data") or {}
        
        # Tenta chaves comuns de billId
        for key in ("billId", "titleId", "financialBillId", "accountsPayableBillId"):
            if inv.get(key):
                try:
                    return int(inv[key])
                except Exception:
                    pass
        
        # Às vezes vem aninhado em objetos
        for parent_key in ("financial", "accountsPayable", "bill", "title"):
            nested = inv.get(parent_key) or {}
            for key in ("billId", "id", "titleId"):
                if nested.get(key):
                    try:
                        return int(nested[key])
                    except Exception:
                        pass
        
        return None
    except Exception as e:
        log.debug("Fallback #1 (NF) falhou para NF %s: %s", sequential_number, e)
        return None


async def _try_bill_via_bills_search(
    make_request,
    creditor_id: int,
    company_id: int,
    invoice_total: Optional[Decimal],
    issue_date: Optional[str],
    movement_date: Optional[str]
) -> Optional[int]:
    """
    Fallback #2: Busca via GET /bills com filtros (creditor, company, período)
    """
    try:
        # Janela de datas (±7 dias do movimento/emissão)
        base = movement_date or issue_date
        params = {
            "creditorId": creditor_id,
            "companyId": company_id,
            "limit": 50,
            "offset": 0
        }
        
        if base:
            try:
                dt = datetime.strptime(base, "%Y-%m-%d")
                params["registeredDateFrom"] = (dt - timedelta(days=7)).strftime("%Y-%m-%d")
                params["registeredDateTo"] = (dt + timedelta(days=7)).strftime("%Y-%m-%d")
            except Exception:
                pass
        
        r = await make_request("GET", "/bills", params=params)
        if not r.get("success"):
            return None
        
        data = r.get("data") or {}
        rows = data.get("results", []) if isinstance(data, dict) else data or []
        if not rows:
            return None
        
        # 1) Casa por total exato da NF
        if invoice_total is not None:
            for b in rows:
                amt = b.get("amount")
                try:
                    if Decimal(str(amt)).quantize(Decimal("0.01")) == invoice_total.quantize(Decimal("0.01")):
                        bid = b.get("id") or b.get("billId")
                        if bid:
                            log.info("Fallback #2 (Bills API) encontrou billId %s por valor exato", bid)
                            return int(bid)
                except Exception:
                    continue
        
        # 2) Caso contrário, retorna o mais recente "Em Aberto"
        for b in rows:
            status_str = str(b.get("status", "")).lower()
            if status_str in ("open", "em aberto", "aberto", "pending", "pendente"):
                bid = b.get("id") or b.get("billId")
                if bid:
                    log.info("Fallback #2 (Bills API) encontrou billId %s (status aberto)", bid)
                    return int(bid)
        
        return None
    except Exception as e:
        log.debug("Fallback #2 (Bills API) falhou: %s", e)
        return None


async def _try_bill_via_bulk_outcome(
    make_bulk_request,
    creditor_id: int,
    company_id: int,
    invoice_total: Optional[Decimal],
    window_days: int = 14
) -> Optional[int]:
    """
    Fallback #3: Bulk Data - Parcelas do Contas a Pagar
    Agrupa parcelas por billId e compara soma com total da NF
    """
    if invoice_total is None:
        log.debug("Fallback #3 (Bulk Data) ignorado: sem total da NF")
        return None
    
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=window_days)).strftime("%Y-%m-%d")
        
        params = {
            "creditorId": creditor_id,
            "companyId": company_id,
            "registeredDateFrom": start_date,
            "registeredDateTo": today,
            "limit": 500,
            "offset": 0
        }
        
        # Tenta diferentes paths do Bulk Data
        for path in ("/bulk-data/outcome", "/bulk-data/v1/outcome", "/accounts-payable/installments"):
            r = await make_bulk_request("GET", path, params=params)
            if not r.get("success"):
                continue
            
            data = r.get("data") or {}
            rows = data.get("results", []) if isinstance(data, dict) else data or []
            if not rows:
                continue
            
            # Agrupa por billId e soma valores
            sums = defaultdict(Decimal)
            for item in rows:
                bid = item.get("billId") or item.get("idBill") or item.get("titleId")
                val = item.get("amount") or item.get("value") or item.get("installmentAmount")
                try:
                    if bid and val is not None:
                        sums[int(bid)] += Decimal(str(val))
                except Exception:
                    pass
            
            # Procura billId cuja soma de parcelas = total da NF
            for bid, total_sum in sums.items():
                if total_sum.quantize(Decimal("0.01")) == invoice_total.quantize(Decimal("0.01")):
                    log.info("Fallback #3 (Bulk Data) encontrou billId %s (soma = NF)", bid)
                    return int(bid)
        
        return None
    except Exception as e:
        log.debug("Fallback #3 (Bulk Data) falhou: %s", e)
        return None


async def resolve_bill_id_for_invoice(
    make_request,
    make_bulk_request,
    sequential_number: int,
    creditor_id: Optional[int] = None,
    company_id: Optional[int] = None
) -> Optional[int]:
    """
    Sistema resiliente de descoberta de billId com 4 estratégias (em ordem):
    
    0. deliveries-attended (original, rápido mas nem sempre funciona)
    1. Dentro da própria NF (quando tenant expõe billId)
    2. Bills API (filtrando por creditor, company, período e valor)
    3. Bulk Data outcome (agrupa parcelas por billId e compara soma)
    
    Args:
        make_request: Função para fazer requisições à API
        make_bulk_request: Função para fazer requisições bulk à API
        sequential_number: Sequential number da NF
        creditor_id: ID do fornecedor (opcional, será buscado da NF se omitido)
        company_id: ID da empresa (opcional, será buscado da NF se omitido)
    
    Returns:
        billId encontrado ou None
    """
    log.info("Iniciando descoberta resiliente de billId para NF %s", sequential_number)
    
    # Fallback #0: deliveries-attended (mantido por compatibilidade)
    bid = await _try_bill_from_deliveries_attended(make_request, sequential_number)
    if bid:
        return bid
    
    # Busca NF para ter metadados (total, datas, creditor, company)
    inv_res = await make_request("GET", f"/purchase-invoices/{sequential_number}")
    if not inv_res.get("success"):
        log.warning("Não foi possível buscar NF %s para descoberta de billId", sequential_number)
        return None
    
    invoice = inv_res.get("data") or {}
    total = _infer_invoice_total(invoice)
    issue_date = invoice.get("issueDate")
    movement_date = invoice.get("movementDate")
    cred = creditor_id or invoice.get("supplierId") or invoice.get("creditorId")
    comp = company_id or invoice.get("companyId")
    
    # Fallback #1: Direto na NF
    bid = await _try_bill_from_invoice(make_request, sequential_number)
    if bid:
        return bid
    
    # Fallback #2 e #3: Precisam de creditor e company
    if not cred or not comp:
        log.warning(
            "Fallbacks #2 e #3 requerem creditorId e companyId. "
            "NF %s não tem esses dados ou não foram fornecidos.",
            sequential_number
        )
        return None
    
    # Fallback #2: Bills API
    bid = await _try_bill_via_bills_search(make_request, int(cred), int(comp), total, issue_date, movement_date)
    if bid:
        return bid
    
    # Fallback #3: Bulk Data (bala de prata)
    bid = await _try_bill_via_bulk_outcome(make_bulk_request, int(cred), int(comp), total)
    if bid:
        return bid
    
    log.warning("Todos os 4 fallbacks falharam para NF %s", sequential_number)
    return None


# ============ TOOLS PRINCIPAIS - ATUALIZAÇÃO DE PARCELAS ============

async def ap_update_auto_bill_installments(
    make_request,
    make_bulk_request,
    sequential_number: int,
    bill_id: Optional[int] = None,
    due_dates: Optional[List[str]] = None,
    days_to_due: Optional[List[int]] = None,
    base_date: Optional[str] = None,
    amounts: Optional[List[float]] = None
) -> Dict:
    """
    Atualiza parcelas do título (criado automaticamente pelo Sienge ao lançar NF)
    
    Args:
        make_request: Função para fazer requisições à API
        make_bulk_request: Função para fazer requisições bulk à API
        sequential_number: Sequential number da nota fiscal
        bill_id: ID do título (opcional; se ausente, descoberto automaticamente)
        due_dates: Lista de datas de vencimento ["2025-11-03", "2025-12-03"]
        days_to_due: Lista de dias até vencimento [30, 60, 90] (relativo a base_date)
        base_date: Data base para days_to_due (padrão: hoje UTC) "YYYY-MM-DD"
        amounts: Lista de valores das parcelas (se omitido, divide igualmente o total da NF)
    
    Returns:
        Dict com success, billId, soma das parcelas, parcelas com daysToDue calculado
    """
    log.info("Atualizando parcelas - NF: %s, bill_id: %s", sequential_number, bill_id)
    
    # 1) Buscar NF (para pegar total se necessário)
    inv = await make_request("GET", f"/purchase-invoices/{sequential_number}")
    if not inv.get("success"):
        return {
            "success": False,
            "message": f"❌ NF {sequential_number} não encontrada",
            "details": inv.get("message"),
            "error": inv.get("error")
        }
    invoice = inv.get("data") or {}
    
    # 2) Descobrir billId com sistema resiliente (4 fallbacks)
    bid = bill_id or await resolve_bill_id_for_invoice(make_request, make_bulk_request, sequential_number)
    if not bid:
        return {
            "success": False,
            "message": "❌ Não foi possível descobrir o billId automaticamente após 4 tentativas.",
            "hint": "Envie 'bill_id' explicitamente. Para melhorar auto-descoberta, garanta que a NF tem creditorId e companyId.",
            "fallbacks_tried": [
                "deliveries-attended (endpoint específico)",
                "Dentro da própria NF (campos billId, financial.billId, etc)",
                "Bills API (busca por creditor, company e valor)",
                "Bulk Data outcome (agrupa parcelas por billId)"
            ]
        }
    
    log.info("BillId identificado: %s", bid)
    
    # 3) Calcular datas de vencimento
    base = datetime.strptime(base_date, "%Y-%m-%d") if base_date else datetime.utcnow()
    
    if due_dates:
        ds = due_dates
    else:
        if not days_to_due:
            return {
                "success": False,
                "message": "❌ Informe 'due_dates' ou 'days_to_due'.",
                "error": "MISSING_DUE_DATES"
            }
        ds = [_iso(base + timedelta(days=int(x))) for x in days_to_due]
    
    # 4) Calcular valores das parcelas
    if amounts:
        vals = [Decimal(str(x)) for x in amounts]
        total = sum(vals)
        if len(vals) != len(ds):
            return {
                "success": False,
                "message": f"❌ 'amounts' ({len(vals)}) e datas ({len(ds)}) devem ter o mesmo tamanho",
                "error": "SIZE_MISMATCH"
            }
    else:
        total_nf = _infer_invoice_total(invoice)
        if total_nf is None:
            return {
                "success": False,
                "message": "❌ Não foi possível inferir o total da NF. Informe 'amounts' explicitamente.",
                "error": "MISSING_INVOICE_TOTAL"
            }
        vals = split_installments_exact(total_nf, len(ds))
        total = sum(vals)
    
    log.info("Calculadas %d parcelas - Total: %s", len(vals), total)
    
    # 5) Montar payload de parcelas
    parcels = [
        {
            "number": i + 1,
            "amount": float(v),
            "dueDate": ds[i]
        }
        for i, v in enumerate(vals)
    ]
    
    # 6) Tentar PUT/POST de parcelas (nem sempre suportado pela API)
    upd = await make_request("PUT", f"/bills/{int(bid)}/installments", json_data={"installments": parcels})
    
    if not upd.get("success"):
        log.warning("PUT não suportado, tentando POST...")
        upd = await make_request("POST", f"/bills/{int(bid)}/installments", json_data={"installments": parcels})
    
    if not upd.get("success"):
        return {
            "success": False,
            "message": "❌ Erro ao atualizar parcelas (API pode não suportar atualização)",
            "billId": bid,
            "details": upd.get("message"),
            "error": upd.get("error"),
            "note": "⚠️ A API Sienge pode não permitir atualização de parcelas após criação do título."
        }
    
    log.info("Parcelas atualizadas com sucesso")
    
    # 7) Buscar parcelas atualizadas + verificar soma
    lst = await make_request("GET", f"/bills/{int(bid)}/installments")
    if not lst.get("success"):
        return {
            "success": False,
            "message": "⚠️ Parcelas podem ter sido atualizadas, mas falhou conferência de leitura",
            "billId": bid,
            "details": lst.get("message")
        }
    
    data = lst.get("data") or {}
    items = data.get("results", []) if isinstance(data, dict) else data or []
    soma = sum(Decimal(str(p.get("amount", 0))) for p in items)
    
    # 8) Calcular daysToDue para cada parcela
    for p in items:
        try:
            dd = datetime.strptime(str(p.get("dueDate")), "%Y-%m-%d")
            p["daysToDue"] = (dd - base).days
        except Exception:
            p["daysToDue"] = None
    
    ok = (soma.quantize(Decimal("0.01")) == total.quantize(Decimal("0.01")))
    
    return {
        "success": ok,
        "message": "✅ Parcelas atualizadas e soma confere" if ok else "⚠️ Parcelas atualizadas, mas soma não confere",
        "billId": bid,
        "invoiceSequential": sequential_number,
        "sumInstallments": float(soma),
        "expectedAmount": float(total),
        "installments": items,
        "calculationBase": _iso(base) if base else None
    }


# ============ TOOLS - ATUALIZAÇÃO DE CABEÇALHO ============

async def ap_patch_bill(
    make_request,
    bill_id: int,
    document_identification_id: Optional[str] = None,
    document_number: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Atualiza campos do Título (cabeçalho) via PATCH
    
    Args:
        make_request: Função para fazer requisições à API
        bill_id: ID do título
        document_identification_id: Tipo do documento (ex: "NF", "DP")
        document_number: Número do documento
        extra_fields: Campos adicionais conforme parametrização do Sienge
    
    Returns:
        Dict com success status e dados do título atualizado
    """
    log.info("Atualizando título %s via PATCH", bill_id)
    
    body = {}
    if document_identification_id is not None:
        body["documentIdentificationId"] = document_identification_id
    if document_number is not None:
        body["documentNumber"] = document_number
    if extra_fields:
        body.update(extra_fields)
    
    if not body:
        return {
            "success": False,
            "message": "❌ Nenhum campo para atualizar no PATCH do Título."
        }
    
    res = await make_request("PATCH", f"/bills/{bill_id}", json_data=body)
    if not res.get("success"):
        return {
            "success": False,
            "message": "❌ Erro ao atualizar o título",
            "billId": bill_id,
            "error": res.get("error"),
            "details": res.get("message"),
        }
    
    # Read-back opcional (confirma estado após 204)
    get_res = await make_request("GET", f"/bills/{bill_id}")
    if get_res.get("success"):
        log.info("Título %s atualizado e confirmado via GET", bill_id)
        return {
            "success": True,
            "message": "✅ Título atualizado com sucesso",
            "billId": bill_id,
            "bill": get_res.get("data")
        }
    
    return {
        "success": True,
        "message": "✅ Título atualizado (204); falha ao ler estado final",
        "billId": bill_id,
        "readbackError": get_res.get("message"),
    }


# ============ TOOLS - ANEXOS ============

async def ap_attach_bill(
    make_request,
    bill_id: int,
    description: str,
    file_path: Optional[str] = None,
    file_name: Optional[str] = None,
    file_content_base64: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict:
    """
    Insere anexo no Título via POST multipart/form-data
    
    Args:
        make_request: Função para fazer requisições à API
        bill_id: ID do título
        description: Descrição do anexo (obrigatório)
        file_path: Caminho do arquivo no sistema ou URL (usar OU file_content_base64)
        file_name: Nome do arquivo (obrigatório se usar file_content_base64)
        file_content_base64: Conteúdo do arquivo em Base64
        content_type: MIME type (opcional, detectado automaticamente)
    
    Returns:
        Dict com success status e lista de anexos
    """
    import base64
    import mimetypes
    import os
    from urllib.parse import urlparse
    
    log.info("Anexando arquivo ao título %s", bill_id)
    
    if not description:
        return {
            "success": False,
            "message": "❌ Descrição do anexo é obrigatória."
        }
    
    # Carregar conteúdo
    file_bytes = None
    
    if file_path:
        is_url = file_path.startswith("http://") or file_path.startswith("https://")
        
        if is_url:
            # Download de URL
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    response = await client.get(file_path, headers=headers)
                    response.raise_for_status()
                    file_bytes = response.content
                    
                    parsed_url = urlparse(file_path)
                    file_name = file_name or os.path.basename(parsed_url.path) or f"attachment_{bill_id}.pdf"
                    
                    content_type = content_type or response.headers.get("content-type")
                    if not content_type:
                        ctype, _ = mimetypes.guess_type(file_name)
                        content_type = ctype or "application/octet-stream"
            except Exception as e:
                return {
                    "success": False,
                    "message": f"❌ Erro ao baixar arquivo da URL: {str(e)}",
                    "error": "DOWNLOAD_FAILED"
                }
        else:
            # Arquivo local
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"❌ Arquivo não encontrado: {file_path}",
                    "error": "FILE_NOT_FOUND"
                }
            file_name = file_name or os.path.basename(file_path)
            if not content_type:
                ctype, _ = mimetypes.guess_type(file_name)
                content_type = ctype or "application/octet-stream"
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            log.info("Arquivo carregado: %s (%d bytes)", file_name, len(file_bytes))
    elif file_content_base64 and file_name:
        try:
            file_bytes = base64.b64decode(file_content_base64)
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Erro ao decodificar Base64: {e}",
                "error": "INVALID_BASE64"
            }
        if not content_type:
            ctype, _ = mimetypes.guess_type(file_name)
            content_type = ctype or "application/octet-stream"
        log.info("Arquivo Base64 decodificado: %s (%d bytes)", file_name, len(file_bytes))
    else:
        return {
            "success": False,
            "message": "❌ Informe 'file_path' OU ('file_name' + 'file_content_base64').",
            "error": "MISSING_FILE"
        }
    
    if not file_bytes:
        return {
            "success": False,
            "message": "❌ Não foi possível carregar o arquivo",
            "error": "FILE_LOAD_FAILED"
        }
    
    # Montar multipart
    files = {"file": (file_name, file_bytes, content_type)}
    params = {"description": description}
    
    res = await make_request("POST", f"/bills/{bill_id}/attachments", params=params, files=files)
    
    if not res.get("success"):
        return {
            "success": False,
            "message": "❌ Erro ao inserir anexo",
            "billId": bill_id,
            "fileName": file_name,
            "error": res.get("error"),
            "details": res.get("message"),
        }
    
    log.info("Anexo %s inserido com sucesso no título %s", file_name, bill_id)
    
    # Conferência: listar anexos
    check = await make_request("GET", f"/bills/{bill_id}/attachments")
    attachments = None
    if check.get("success"):
        data = check.get("data") or {}
        attachments = data.get("results", []) if isinstance(data, dict) else data
    
    return {
        "success": True,
        "message": f"✅ Anexo '{file_name}' inserido com sucesso",
        "billId": bill_id,
        "fileName": file_name,
        "attachments": attachments,
        "attachmentsCount": len(attachments) if attachments else None
    }


# ============ TOOLS - ORQUESTRADOR FINALIZE ============

async def ap_finalize_bill(
    make_request,
    bill_id: int,
    patch_body: Optional[Dict[str, Any]] = None,
    attachment: Optional[Dict[str, Any]] = None,
    audit: bool = True
) -> Dict:
    """
    Orquestrador: faz PATCH do título, insere anexo e audita status/anexos
    
    Args:
        make_request: Função para fazer requisições à API
        bill_id: ID do título
        patch_body: Campos para atualizar via PATCH
        attachment: Dados do anexo (description, file_path ou file_content_base64 + file_name)
        audit: Se True, audita status e anexos ao final
    
    Returns:
        Dict com steps executados e auditoria final
    """
    log.info("Finalizando título %s (PATCH + Anexo + Auditoria)", bill_id)
    
    out = {"billId": bill_id, "steps": []}
    
    # 1) PATCH (se houver)
    if patch_body:
        patch_result = await ap_patch_bill(
            make_request,
            bill_id,
            document_identification_id=patch_body.get("documentIdentificationId"),
            document_number=patch_body.get("documentNumber"),
            extra_fields={k: v for k, v in patch_body.items() 
                         if k not in ("documentIdentificationId", "documentNumber")}
        )
        out["steps"].append({"step": "patch", "result": patch_result})
        if not patch_result.get("success"):
            out["success"] = False
            out["message"] = "❌ Falha no PATCH do título."
            return out
    
    # 2) Anexo (se houver)
    if attachment:
        attach_result = await ap_attach_bill(
            make_request,
            bill_id,
            description=attachment.get("description", "Anexo"),
            file_path=attachment.get("file_path"),
            file_name=attachment.get("file_name"),
            file_content_base64=attachment.get("file_content_base64"),
            content_type=attachment.get("content_type")
        )
        out["steps"].append({"step": "attachment", "result": attach_result})
        if not attach_result.get("success"):
            out["success"] = False
            out["message"] = "❌ Falha ao anexar arquivo."
            return out
    
    # 3) Auditoria rápida
    if audit:
        bill_res = await make_request("GET", f"/bills/{bill_id}")
        atts_res = await make_request("GET", f"/bills/{bill_id}/attachments")
        
        status = None
        document_number = None
        if bill_res.get("success"):
            b = bill_res.get("data") or {}
            status = b.get("status")
            document_number = b.get("documentNumber")
        
        att_count = None
        att_list = None
        if atts_res.get("success"):
            data = atts_res.get("data") or {}
            lst = data.get("results", []) if isinstance(data, dict) else data
            att_count = len(lst or [])
            att_list = [{"name": a.get("name"), "description": a.get("description")} 
                       for a in (lst or [])]
        
        out["audit"] = {
            "status": status,
            "documentNumber": document_number,
            "attachmentsCount": att_count,
            "attachments": att_list
        }
    
    out["success"] = True
    out["message"] = "✅ Título finalizado (PATCH/anexo executados com sucesso)."
    log.info("Título %s finalizado com sucesso", bill_id)
    return out


# ============ TOOLS - CONSULTA ============

async def ap_list_installments(make_request, bill_id: int) -> Dict:
    """
    Lista parcelas de um título (somente leitura)
    
    Args:
        make_request: Função para fazer requisições à API
        bill_id: ID do título
    
    Returns:
        Dict com lista de parcelas, contagem e metadata
    """
    log.info("Listando parcelas do título: %s", bill_id)
    res = await make_request("GET", f"/bills/{bill_id}/installments")
    
    if res.get("success"):
        data = res.get("data")
        items = data.get("results", []) if isinstance(data, dict) else data or []
        meta = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        
        return {
            "success": True,
            "installments": items,
            "count": len(items),
            "metadata": meta
        }
    
    return {
        "success": False,
        "message": f"❌ Erro ao listar parcelas do título {bill_id}",
        "error": res.get("error"),
        "details": res.get("message")
    }


async def ap_audit_bill_completeness(make_request, bill_id: int) -> Dict:
    """
    Audita completude do título: valores, parcelas, anexos
    
    Args:
        make_request: Função para fazer requisições à API
        bill_id: ID do título
    
    Returns:
        Dict com auditoria completa
    """
    # Ler título
    bill = await make_request("GET", f"/bills/{bill_id}")
    if not bill.get("success"):
        return {"success": False, "message": "Erro ao ler título", "details": bill.get("message")}
    
    total = _as_decimal(_get(bill["data"], "totalInvoiceAmount"))
    
    # Listar parcelas
    res_inst = await make_request("GET", f"/bills/{bill_id}/installments", params={"limit": 200, "offset": 0})
    if not res_inst.get("success"):
        return {"success": False, "message": "Erro ao listar parcelas", "details": res_inst.get("message")}
    
    data_inst = res_inst.get("data") or {}
    inst_list = data_inst.get("results", []) if isinstance(data_inst, dict) else data_inst or []
    
    soma = sum([_as_decimal(i.get("amount")) or Decimal("0") for i in inst_list], Decimal("0"))
    
    # Listar anexos
    atts = await make_request("GET", f"/bills/{bill_id}/attachments", params={"limit": 10, "offset": 0})
    att_list = []
    if atts.get("success"):
        data = atts.get("data") or {}
        att_list = data.get("results", []) if isinstance(data, dict) else data or []
    has_att = bool(att_list)
    
    return {
        "success": True,
        "bill": bill["data"],
        "sumInstallments": float(soma),
        "matchesTotal": (total is None) or (soma == total),
        "hasAttachment": has_att,
        "attachments": att_list,
        "notes": "⚠️ Valores de parcelas NÃO são alteráveis por API; use dueDate quando preciso.",
    }


# ============ TOOLS DEPRECATED - CRIAÇÃO MANUAL ============

async def ap_create_bill(make_request, bill: Dict[str, Any], force_create: bool = False) -> Dict:
    """
    [DEPRECATED] Cria título manualmente (use apenas se Sienge não criar automaticamente)
    
    O Sienge cria títulos automaticamente ao lançar NF. Esta tool existe apenas como fallback.
    """
    if not force_create:
        return {
            "success": False,
            "message": "⚠️ DEPRECATED: O Sienge cria títulos automaticamente ao lançar NF.",
            "hint": "Use 'ap_update_auto_bill_installments' para atualizar o título criado automaticamente.",
            "note": "Se realmente precisa criar manualmente, passe force_create=True"
        }
    
    log.warning("Criação manual de título (force_create=True) - documentId: %s", bill.get("documentId"))
    
    try:
        res = await make_request("POST", "/bills", json_data=bill)
        
        if res.get("success"):
            data = res.get("data") or {}
            bill_id = data.get("id") or data.get("billId")
            return {
                "success": True,
                "message": "✅ Título criado manualmente",
                "bill": data,
                "billId": bill_id,
                "warning": "⚠️ Este título foi criado manualmente, não pelo processo automático do Sienge"
            }
        
        return {
            "success": False,
            "message": "❌ Erro ao criar título",
            "error": res.get("error"),
            "details": res.get("message")
        }
    except Exception as e:
        log.error("Exceção em ap_create_bill: %s", e, exc_info=True)
        return {
            "success": False,
            "message": "❌ Exceção interna",
            "error": type(e).__name__,
            "details": str(e)
        }
