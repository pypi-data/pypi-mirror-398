"""
Markdown Report Generator
"""

from typing import Dict, Any


def generate_markdown_report(summary: Dict[str, Any]) -> str:
    """Chuyển đổi kết quả JSON sang format Markdown"""

    lines = []

    # Header
    lines.append("# BÁO CÁO ĐÁNH GIÁ HỒ SƠ BẢO HIỂM")
    lines.append("")
    lines.append(f"**Claim ID:** {summary['claim_id']}")
    lines.append(f"**Contract ID:** {summary['contract_id']}")
    lines.append("")

    # Tổng quan
    lines.append("---")
    lines.append("## TỔNG QUAN")
    lines.append("")
    tq = summary['tong_quan']
    lines.append("| Chỉ số | Giá trị |")
    lines.append("|--------|---------|")
    lines.append(f"| Số rule ĐẠT | {tq['so_rule_dat']} |")
    lines.append(f"| Số rule KHÔNG ĐẠT | {tq['so_rule_khong_dat']} |")
    lines.append(f"| Số rule CẦN XEM XÉT | {tq['so_rule_can_xem_xet']} |")
    lines.append(f"| Tỷ lệ đạt | {tq['ty_le_dat']} |")
    lines.append(f"| Confidence trung bình | {tq['avg_confidence']} |")
    lines.append("")

    # Kết luận
    lines.append("---")
    lines.append("## KẾT LUẬN")
    lines.append("")
    ket_luan_icon = "✅" if summary['ket_luan'] == "DAT" else ("❌" if summary['ket_luan'] == "KHONG_DAT" else "⚠️")
    lines.append(f"**{ket_luan_icon} {summary['ket_luan']}**")
    lines.append("")
    lines.append(f"**Đề xuất:** {summary['de_xuat']}")
    lines.append("")

    # Danh sách không đạt
    if summary['danh_sach_khong_dat']:
        lines.append("---")
        lines.append("## DANH SÁCH RULE KHÔNG ĐẠT")
        lines.append("")
        for item in summary['danh_sach_khong_dat']:
            lines.append(f"### ❌ {item['rule_id']}: {item['rule_name']}")
            lines.append(f"- **Confidence:** {item['confidence']}")
            lines.append(f"- **Lý do:** {item['ly_do']}")
            lines.append("")

    # Danh sách cần xem xét
    if summary['danh_sach_can_xem_xet']:
        lines.append("---")
        lines.append("## DANH SÁCH RULE CẦN XEM XÉT")
        lines.append("")
        for item in summary['danh_sach_can_xem_xet']:
            lines.append(f"### ⚠️ {item['rule_id']}: {item['rule_name']}")
            lines.append(f"- **Confidence:** {item['confidence']}")
            lines.append(f"- **Lý do:** {item['ly_do']}")
            lines.append("")

    # Điểm lưu ý
    if summary['diem_luu_y']:
        lines.append("---")
        lines.append("## ĐIỂM LƯU Ý")
        lines.append("")
        for note in summary['diem_luu_y']:
            lines.append(f"- {note}")
        lines.append("")

    # Chi tiết kết quả
    lines.append("---")
    lines.append("## CHI TIẾT KẾT QUẢ TỪNG RULE")
    lines.append("")

    for r in summary['chi_tiet_ket_qua']:
        icon = "✅" if r['result'] == "DAT" else ("❌" if r['result'] == "KHONG_DAT" else "⚠️")
        lines.append(f"### {icon} {r['rule_id']}: {r['rule_name']}")
        lines.append("")
        lines.append("| Thông tin | Giá trị |")
        lines.append("|-----------|---------|")
        lines.append(f"| **Câu hỏi** | {r['question']} |")
        lines.append(f"| **Kết quả** | {r['result']} |")
        lines.append(f"| **Confidence** | {r['confidence']} |")
        lines.append("")
        lines.append(f"**Giải thích:** {r['explanation']}")
        lines.append("")

    return "\n".join(lines)
