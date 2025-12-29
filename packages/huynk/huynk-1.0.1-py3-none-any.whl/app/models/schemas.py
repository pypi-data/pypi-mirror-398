"""
Pydantic Models / Schemas
"""

from pydantic import BaseModel
from typing import Dict, List, Any, Optional


class EvaluateRequest(BaseModel):
    """Request model cho endpoint evaluate"""
    claim_path: str
    contract_path: str
    rules_path: str
    rule_ids: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "claim_path": "input/claim/CLM-2025-001.json",
                "contract_path": "input/contract_ocr/MAX.VP.D09.MGC.26.HD1.md",
                "rules_path": "input/rules/rules.xlsx",
                "rule_ids": None
            }
        }


class RuleResult(BaseModel):
    """Kết quả đánh giá một rule"""
    rule_id: str
    rule_name: str
    question: str
    result: str  # DAT, KHONG_DAT, CAN_XEM_XET
    explanation: str
    confidence: float


class TongQuan(BaseModel):
    """Tổng quan kết quả"""
    so_rule_dat: int
    so_rule_khong_dat: int
    so_rule_can_xem_xet: int
    ty_le_dat: str
    avg_confidence: float


class RuleItem(BaseModel):
    """Item trong danh sách rule"""
    rule_id: str
    rule_name: str
    ly_do: str
    confidence: float


class EvaluationSummary(BaseModel):
    """Kết quả đánh giá tổng hợp"""
    claim_id: str
    contract_id: str
    tong_quan: TongQuan
    danh_sach_khong_dat: List[RuleItem]
    danh_sach_can_xem_xet: List[RuleItem]
    diem_luu_y: List[str]
    de_xuat: str
    ket_luan: str
    overall_confidence: float
    chi_tiet_ket_qua: List[RuleResult]
