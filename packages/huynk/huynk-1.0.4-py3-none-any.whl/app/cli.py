"""
CLI entry point for HuyNK package
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="HuyNK - Rule Evaluator for Insurance Claims",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    huynk serve                           # Start API server
    huynk serve --port 8080               # Start on custom port
    huynk evaluate --claim claim.json --contract contract.md --rules rules.xlsx
    huynk version                         # Show version
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a claim")
    eval_parser.add_argument("--claim", required=True, help="Path to claim JSON file")
    eval_parser.add_argument("--contract", required=True, help="Path to contract markdown file")
    eval_parser.add_argument("--rules", required=True, help="Path to rules Excel file")
    eval_parser.add_argument("--output", help="Output file path (default: stdout)")
    eval_parser.add_argument("--rule-ids", nargs="+", help="Specific rule IDs to evaluate")

    # Version command
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "serve":
        run_server(args)
    elif args.command == "evaluate":
        run_evaluate(args)
    elif args.command == "version":
        from app import __version__
        print(f"huynk version {__version__}")
    else:
        parser.print_help()
        sys.exit(1)


def run_server(args):
    """Start the FastAPI server"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def run_evaluate(args):
    """Run evaluation from CLI"""
    import pandas as pd
    from app.services.evaluator import RuleEvaluator, load_rules_from_file
    from app.utils.markdown import MarkdownReportGenerator

    # Load input files
    claim_path = Path(args.claim)
    contract_path = Path(args.contract)
    rules_path = Path(args.rules)

    if not claim_path.exists():
        print(f"Error: Claim file not found: {claim_path}")
        sys.exit(1)
    if not contract_path.exists():
        print(f"Error: Contract file not found: {contract_path}")
        sys.exit(1)
    if not rules_path.exists():
        print(f"Error: Rules file not found: {rules_path}")
        sys.exit(1)

    # Load data
    with open(claim_path, 'r', encoding='utf-8') as f:
        claim_data = json.load(f)

    with open(contract_path, 'r', encoding='utf-8') as f:
        contract_content = f.read()

    rules_df = load_rules_from_file(rules_path)

    # Filter rules if specified
    if args.rule_ids:
        rules_df = rules_df[rules_df['rule_id'].isin(args.rule_ids)].reset_index(drop=True)

    print(f"Evaluating {len(rules_df)} rules...")

    # Create evaluator and run
    evaluator = RuleEvaluator(
        claim_data=claim_data,
        contract_content=contract_content,
        rules_df=rules_df
    )

    results = evaluator.evaluate_all_rules()
    summary = evaluator.generate_summary(results)

    # Output
    if args.output:
        output_path = Path(args.output)

        if output_path.suffix == '.md':
            # Generate markdown report
            generator = MarkdownReportGenerator()
            markdown = generator.generate_report(summary)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
        else:
            # JSON output
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"Results saved to: {output_path}")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
