"""
Evaluate Router
API endpoints for evaluating insurance claims
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response

from app.models.schemas import EvaluateRequest
from app.services.evaluator import RuleEvaluator, load_rules_from_file
from app.utils.markdown import generate_markdown_report


router = APIRouter(prefix="/evaluate", tags=["Evaluate"])


@router.post("")
async def evaluate_claim(request: EvaluateRequest):
    """
    Đánh giá hồ sơ bảo hiểm theo các rules

    - **claim_path**: Đường dẫn file JSON chứa thông tin yêu cầu bồi thường
    - **contract_path**: Đường dẫn file Markdown chứa nội dung hợp đồng đã OCR
    - **rules_path**: Đường dẫn file Excel chứa các rules đánh giá
    - **rule_ids**: Danh sách rule IDs cần đánh giá (None = tất cả)

    Returns: Báo cáo đánh giá dạng Markdown
    """
    try:
        # Validate file paths
        claim_path = Path(request.claim_path)
        contract_path = Path(request.contract_path)
        rules_path = Path(request.rules_path)

        if not claim_path.exists():
            raise HTTPException(status_code=400, detail=f"File không tồn tại: {claim_path}")
        if not contract_path.exists():
            raise HTTPException(status_code=400, detail=f"File không tồn tại: {contract_path}")
        if not rules_path.exists():
            raise HTTPException(status_code=400, detail=f"File không tồn tại: {rules_path}")

        # Validate file extensions
        if not str(claim_path).endswith('.json'):
            raise HTTPException(status_code=400, detail="claim_path phải là file .json")
        if not str(contract_path).endswith('.md'):
            raise HTTPException(status_code=400, detail="contract_path phải là file .md")
        if not str(rules_path).endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="rules_path phải là file .xlsx")

        # Read claim JSON
        try:
            with open(claim_path, 'r', encoding='utf-8') as f:
                claim_data = json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Read contract MD
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract_text = f.read()

        # Read rules Excel
        try:
            rules_df = load_rules_from_file(rules_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing rules: {str(e)}")

        # Filter rules if specified
        if request.rule_ids:
            rules_df = rules_df[rules_df['rule_id'].isin(request.rule_ids)].reset_index(drop=True)
            if len(rules_df) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy rules: {request.rule_ids}"
                )

        print(f"\n{'='*60}")
        print("RULE EVALUATOR API")
        print(f"{'='*60}")
        print(f"Claim: {claim_data.get('claim_id', 'N/A')}")
        print(f"Contract: {claim_data.get('contract_id', 'N/A')}")
        print(f"Số rules: {len(rules_df)}")
        print(f"{'='*60}\n")

        # Initialize evaluator
        evaluator = RuleEvaluator(
            claim_data=claim_data,
            contract_content=contract_text,
            rules_df=rules_df
        )

        # Evaluate all rules
        results = evaluator.evaluate_all_rules()

        # Generate summary
        summary = evaluator.generate_summary(results)

        print(f"\n{'='*60}")
        print("KẾT QUẢ")
        print(f"{'='*60}")
        print(f"Đạt: {summary['tong_quan']['so_rule_dat']}")
        print(f"Không đạt: {summary['tong_quan']['so_rule_khong_dat']}")
        print(f"Cần xem xét: {summary['tong_quan']['so_rule_can_xem_xet']}")
        print(f"Kết luận: {summary['ket_luan']}")
        print(f"{'='*60}\n")

        # Generate Markdown report
        markdown_report = generate_markdown_report(summary)

        # Save to output folder
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_filename = f"evaluation_{summary['claim_id']}.md"
        output_path = output_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        print(f"📁 Báo cáo đã lưu: {output_path}")

        # Return Markdown
        return Response(
            content=markdown_report,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
