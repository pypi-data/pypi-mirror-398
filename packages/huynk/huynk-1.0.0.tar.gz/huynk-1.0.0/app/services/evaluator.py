"""
Rule Evaluator Service
Business logic for evaluating insurance claims
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

from app.models.schemas import RuleResult, EvaluationSummary
from app.services.openai_client import get_openai_client


class RuleEvaluator:
    """Service đánh giá hồ sơ bảo hiểm theo các rules"""

    def __init__(
        self,
        claim_data: Dict,
        contract_content: str,
        rules_df: pd.DataFrame
    ):
        self.claim_data = claim_data
        self.contract_content = contract_content
        self.rules_df = rules_df
        self.openai_client = get_openai_client()

    def _build_rule_prompt(self, rule: pd.Series) -> str:
        """Tạo prompt để đánh giá một rule"""

        # Truncate contract if too long
        max_length = 50000
        contract_excerpt = self.contract_content[:max_length]
        if len(self.contract_content) > max_length:
            contract_excerpt += "\n... [Nội dung đã được cắt bớt] ..."

        prompt = f"""Bạn là chuyên gia đánh giá hồ sơ bảo hiểm. Hãy đánh giá rule sau dựa trên dữ liệu hồ sơ và hợp đồng.

## THÔNG TIN RULE
- Rule ID: {rule['rule_id']}
- Nhóm: {rule['nhom_thong_tin']}
- Đầu mục: {rule['dau_muc']}
- Câu hỏi cần trả lời: {rule['chi_tiet']}
- Dữ liệu đầu vào cần kiểm tra: {rule['du_lieu_dau_vao_bt']}
- Logic xử lý: {rule['logic_xu_ly_bt']}
- Kết quả mong đợi: {rule['ket_qua_tra_ve_bt']}

## DỮ LIỆU HỒ SƠ YÊU CẦU BỒI THƯỜNG (CLAIM)
```json
{json.dumps(self.claim_data, ensure_ascii=False, indent=2)}
```

## NỘI DUNG HỢP ĐỒNG BẢO HIỂM
```
{contract_excerpt}
```

## YÊU CẦU
Dựa vào thông tin trên, hãy đánh giá rule này và trả lời:
1. Kết quả: DAT (rule được thỏa mãn) / KHONG_DAT (rule không thỏa mãn) / CAN_XEM_XET (cần xem xét thêm do thiếu thông tin)
2. Giải thích chi tiết lý do
3. Độ tin cậy (confidence): 0.0 đến 1.0

## OUTPUT FORMAT (JSON only)
```json
{{
    "rule_id": "{rule['rule_id']}",
    "rule_name": "{rule['dau_muc']}",
    "question": "{rule['chi_tiet']}",
    "result": "DAT | KHONG_DAT | CAN_XEM_XET",
    "explanation": "Giải thích chi tiết...",
    "confidence": 0.0
}}
```
"""
        return prompt

    def evaluate_rule(self, rule: pd.Series) -> RuleResult:
        """Đánh giá một rule cụ thể"""
        prompt = self._build_rule_prompt(rule)

        try:
            result_data = self.openai_client.evaluate_rule(prompt)

            return RuleResult(
                rule_id=result_data.get('rule_id', rule['rule_id']),
                rule_name=result_data.get('rule_name', str(rule['dau_muc'])),
                question=result_data.get('question', str(rule['chi_tiet'])),
                result=result_data.get('result', 'CAN_XEM_XET'),
                explanation=result_data.get('explanation', ''),
                confidence=float(result_data.get('confidence', 0.5))
            )

        except Exception as e:
            print(f"Error evaluating rule {rule['rule_id']}: {e}")
            return RuleResult(
                rule_id=rule['rule_id'],
                rule_name=str(rule['dau_muc']),
                question=str(rule['chi_tiet']),
                result='CAN_XEM_XET',
                explanation=f"Lỗi khi đánh giá: {str(e)}",
                confidence=0.0
            )

    def evaluate_all_rules(self) -> List[RuleResult]:
        """Đánh giá tất cả các rules"""
        results = []
        total = len(self.rules_df)

        for idx, rule in self.rules_df.iterrows():
            print(f"[{idx+1}/{total}] Đang đánh giá rule {rule['rule_id']}: {rule['dau_muc']}")
            result = self.evaluate_rule(rule)
            results.append(result)
            print(f"  -> Kết quả: {result.result} (confidence: {result.confidence})")

        return results

    def generate_summary(self, results: List[RuleResult]) -> Dict[str, Any]:
        """Tổng hợp kết quả đánh giá"""

        # Thống kê
        so_rule_dat = sum(1 for r in results if r.result == 'DAT')
        so_rule_khong_dat = sum(1 for r in results if r.result == 'KHONG_DAT')
        so_rule_can_xem_xet = sum(1 for r in results if r.result == 'CAN_XEM_XET')
        total = len(results)

        # Tính confidence trung bình
        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0

        # Danh sách không đạt
        danh_sach_khong_dat = [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "ly_do": r.explanation,
                "confidence": r.confidence
            }
            for r in results if r.result == 'KHONG_DAT'
        ]

        # Danh sách cần xem xét
        danh_sach_can_xem_xet = [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "ly_do": r.explanation,
                "confidence": r.confidence
            }
            for r in results if r.result == 'CAN_XEM_XET'
        ]

        # Điểm lưu ý
        diem_luu_y = [
            f"Rule {r.rule_id} có độ tin cậy thấp ({r.confidence:.2f}): {r.rule_name}"
            for r in results if r.confidence < 0.7
        ]

        # Kết luận tổng thể
        if so_rule_khong_dat > 0:
            ket_luan = "KHONG_DAT"
            de_xuat = "Cần xem xét lại các rule không đạt trước khi phê duyệt hồ sơ"
        elif so_rule_can_xem_xet > total * 0.3:
            ket_luan = "CAN_XEM_XET_THEM"
            de_xuat = "Có nhiều rule cần xem xét thêm, cần bổ sung thông tin"
        else:
            ket_luan = "DAT"
            de_xuat = "Hồ sơ đạt yêu cầu, có thể tiến hành phê duyệt"

        return {
            "claim_id": self.claim_data.get('claim_id', 'N/A'),
            "contract_id": self.claim_data.get('contract_id', 'N/A'),
            "tong_quan": {
                "so_rule_dat": so_rule_dat,
                "so_rule_khong_dat": so_rule_khong_dat,
                "so_rule_can_xem_xet": so_rule_can_xem_xet,
                "ty_le_dat": f"{(so_rule_dat / total * 100):.1f}%" if total > 0 else "0%",
                "avg_confidence": round(avg_confidence, 2)
            },
            "danh_sach_khong_dat": danh_sach_khong_dat,
            "danh_sach_can_xem_xet": danh_sach_can_xem_xet,
            "diem_luu_y": diem_luu_y,
            "de_xuat": de_xuat,
            "ket_luan": ket_luan,
            "overall_confidence": round(avg_confidence, 2),
            "chi_tiet_ket_qua": [r.model_dump() for r in results]
        }


def load_rules_from_file(file_path: Path) -> pd.DataFrame:
    """Load rules from Excel file"""
    df = pd.read_excel(file_path, sheet_name='Các bước GQHS')

    # Rename columns
    df.columns = [
        'rule_id', 'nhom_thong_tin', 'dau_muc', 'chi_tiet',
        'du_lieu_dau_vao_bt', 'du_lieu_dau_vao_bl',
        'logic_xu_ly_bt', 'logic_xu_ly_bl',
        'ket_qua_tra_ve_bt', 'ket_qua_tra_ve_bl',
        'da_xu_ly_dmn_bt', 'da_xu_ly_dmn_bl',
        'note', 'nguon_du_lieu', 'itc'
    ]

    # Filter valid rules
    df = df.iloc[1:]
    df = df[df['rule_id'].notna() & (df['rule_id'].str.startswith('B', na=False))]

    return df.reset_index(drop=True)
