from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any, ClassVar

import attrs
from cfnlint.rules import CloudFormationLintRule, RuleMatch
from cfnlint.template.template import Template

EMPTY_STRING = ""

EMPTY_DICT = {}

ERROR_MESSAGE = "A BatchJobDefinition should have a valid log configuration and a log group if CloudWatch is used"

logger = logging.getLogger(__name__)
RULE_ID: str = "E9005"


class BatchJobDefinitionLogRule(CloudFormationLintRule):

    id: str = RULE_ID
    shortdesc: str = "Ensure that Fargate Job definitions have configured logging"
    description: str = "Ensure that Fargate Job definitions have configured logging"
    tags = ["Batch", "CloudWatch", "logs"]
    experimental = False

    def __init__(self):
        super().__init__()
        self.configure()

    def match(self, cfn: Template) -> list[RuleMatch]:
        try:
            batch_job_definitions: dict[str, dict[str, Any]] = cfn.get_resources(BatchJobDefinitionEntry.type)
            job_definition_entries: Iterable[BatchJobDefinitionEntry] = \
                [BatchJobDefinitionEntry(item[0], item[1]) for item in batch_job_definitions.items()]
            entries_logging_to_cloudwatch_without_log_group: Iterable[BatchJobDefinitionEntry] = \
                [entry for entry in job_definition_entries if entry.is_misconfigured()]

            matches: list[RuleMatch] = \
                [entry.to_rule_match() for entry in entries_logging_to_cloudwatch_without_log_group]
            return matches
        except Exception as e:
            logger.error(str(e))
            raise e


@attrs.define
class BatchJobDefinitionEntry:
    type: ClassVar[str] = "AWS::Batch::JobDefinition"
    cloudwatch_log_driver: ClassVar[str] = "awslogs"
    key: str
    entry: dict[str, Any]

    def get_aws_log_group(self) -> str:
        return self.get_log_configuration() \
            .get("Options", EMPTY_DICT) \
            .get("awslogs-group", EMPTY_STRING)

    def get_log_configuration(self) -> dict[str, Any]:
        return self.entry.get("Properties", EMPTY_DICT) \
            .get("ContainerProperties", EMPTY_DICT) \
            .get("LogConfiguration", EMPTY_DICT)

    def is_misconfigured(self):
        return self._has_no_configuration() or self._has_no_log_group()

    def _has_no_configuration(self):
        return self.get_log_configuration() == EMPTY_DICT

    def _has_no_log_group(self):
        return self._is_sending_logs_to_cloudwatch() and \
            self.get_aws_log_group() == EMPTY_STRING

    def _is_sending_logs_to_cloudwatch(self) -> bool:
        log_driver: str = self.get_log_configuration().get("LogDriver", EMPTY_STRING)
        return log_driver == BatchJobDefinitionEntry.cloudwatch_log_driver

    def to_rule_match(self) -> RuleMatch:
        return RuleMatch(["Resources", self.key], ERROR_MESSAGE)
