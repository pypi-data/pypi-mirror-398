"""
awsjavakit_cfn_rules package
"""
import os
from pathlib import Path

from awsjavakit_cfn_rules.rules.batch_job_definition_log_rule import BatchJobDefinitionLogRule
from awsjavakit_cfn_rules.rules.lambda_listens_to_event_bridge import LambdaListensToEventBridgeRule
from awsjavakit_cfn_rules.rules.sqs_long_polling_rule import SqsLongPollingRule
from awsjavakit_cfn_rules.rules.tags_checker import TagsChecker

PROJECT_FOLDER = Path(os.path.abspath(__file__)).parent

__all__ = [
    "TagsChecker",
    "SqsLongPollingRule",
    "LambdaListensToEventBridgeRule",
    "BatchJobDefinitionLogRule"
]
