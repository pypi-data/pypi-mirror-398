"""
HuyNK - Rule Evaluator Package
He thong danh gia ho so bao hiem su dung AI
"""

__version__ = "1.0.2"
__author__ = "HuyNK"

# Main classes and functions
from app.services.evaluator import RuleEvaluator, load_rules_from_file
from app.services.openai_client import OpenAIClient, get_openai_client
from app.models.schemas import RuleResult, EvaluationSummary, EvaluateRequest
from app.utils.markdown import generate_markdown_report
from app.config.settings import Settings, get_settings

# FastAPI app
from app.main import app

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core classes
    "RuleEvaluator",
    "OpenAIClient",
    "Settings",
    # Schemas
    "RuleResult",
    "EvaluationSummary",
    "EvaluateRequest",
    # Functions
    "generate_markdown_report",
    "load_rules_from_file",
    "get_openai_client",
    "get_settings",
    # FastAPI app
    "app",
]
