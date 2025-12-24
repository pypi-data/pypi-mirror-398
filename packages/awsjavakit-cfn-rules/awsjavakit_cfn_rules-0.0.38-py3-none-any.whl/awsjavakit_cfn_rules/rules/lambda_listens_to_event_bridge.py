from __future__ import annotations

import logging
import numbers
import sys
from collections.abc import Iterable
from typing import Any

from cfnlint.rules import CloudFormationLintRule, RuleMatch
from cfnlint.template.template import Template

from awsjavakit_cfn_rules.utils.functional import flatmap

REF_REFERENCE = "Ref"

GET_ATT_REFERENCE = "Fn::GetAtt"

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
EVENT_RULES = "AWS::Events::Rule"

KEY = 0
VALUE = 1
RESOURCE_NAME = 0
EMPTY_STRING = ""
EMPTY_LIST=[]

RULE_ID: str = "E9003"


class LambdaListensToEventBridgeRule(CloudFormationLintRule):

    id: str = RULE_ID
    shortdesc: str = "Ensure better event control by forwarding EventBridge events to an SQS queue first"
    description: str = "Ensure better event control by forwarding EventBridge events to an SQS queue first"
    tags = ["EventBridge", "SQS", "Lambda"]
    experimental = False

    def __init__(self):
        super().__init__()
        self.configure()

    def match(self, cfn: Template) -> list[RuleMatch]:
        try:
            event_rules: Iterable[EventRuleEntry] = \
                map(lambda dict_entry: EventRuleEntry.from_dict_entry(dict_entry),
                    (cfn.get_resources(EVENT_RULES).items()))

            targets: Iterable[EventRuleTargetEntry] = \
                flatmap(lambda event_rule: self._extract_rule_targets_(event_rule), event_rules)
            lambda_function_targets: Iterable[EventRuleTargetEntry] = \
                filter(lambda target: self._is_lambda_function_(target, cfn), targets)
            rule_matches = list(map(lambda target: self._create_match_(target), lambda_function_targets))
            return rule_matches
        except Exception as e:
            logger.error(str(e))
            raise e

    def _extract_rule_targets_(self, event_rule: EventRuleEntry) -> Iterable[EventRuleTargetEntry]:
        targets = event_rule.rule.get("Properties", {}).get("Targets", {})
        return list(map(lambda target: EventRuleTargetEntry.from_dict(event_rule.logical_name, target), targets))

    def _create_match_(self, target: EventRuleTargetEntry) -> RuleMatch:
        function_logical_name = self.extract_resource_reference_(target)
        return RuleMatch(["Resources", function_logical_name], self._error_message_(function_logical_name))

    def _extract_lambda_functions_(self, cfn) -> list[str]:
        return list(cfn.get_resources("AWS::Lambda::Function").keys())

    @staticmethod
    def _is_not_a_number_(long_property_value) -> bool:
        return not isinstance(long_property_value, numbers.Number)

    def _is_lambda_function_(self, target: EventRuleTargetEntry, cfn: Template):
        target_arn = self.extract_resource_reference_(target)
        return target_arn in self._extract_lambda_functions_(cfn)

    def extract_resource_reference_(self, target: EventRuleTargetEntry):
        target_arn = target.target_entry.get("Arn", {})
        if self._is_get_att_reference_to_another_resource_in_the_template(target_arn):
            return self._extract_referenced_resource(target, GET_ATT_REFERENCE)
        if self._is_ref_reference_to_another_resource_in_the_template(target_arn):
            return self._extract_referenced_resource(target, REF_REFERENCE)
        return target_arn

    def _extract_referenced_resource(self, target: EventRuleTargetEntry, reference_method: str):
        return target.target_entry.get("Arn", {}).get(reference_method, EMPTY_STRING)[RESOURCE_NAME]

    def _error_message_(self, function_name: str) -> str:
        return f"""
        Lambda Function  ${function_name} is listening to an EventBridge event directly.
        Better to set up an SQS queue to listen to the Event Bridge event and the Lambda to listen to the SQS queue.
        This way, you have better control over the parallelism.
        """

    def _is_get_att_reference_to_another_resource_in_the_template(self, target_arn: Any):
        return (isinstance(target_arn, dict)
                and isinstance(target_arn.get(GET_ATT_REFERENCE, EMPTY_LIST), list)
                and len(target_arn.get(GET_ATT_REFERENCE,EMPTY_LIST)) > 0)

    def _is_ref_reference_to_another_resource_in_the_template(self, target_arn):
        return (isinstance(target_arn, dict)
         and isinstance(target_arn.get(REF_REFERENCE, EMPTY_STRING), str)
         and len(target_arn.get(REF_REFERENCE,EMPTY_STRING)) > 0)


class EventRuleEntry:
    logical_name: str
    rule: dict

    def __init__(self, logical_name: str, rule: dict):
        self.logical_name = logical_name
        self.rule = rule

    @staticmethod
    def from_dict_entry(dict_entry: tuple[str, dict[str, Any]]) -> EventRuleEntry:
        return EventRuleEntry(logical_name=dict_entry[KEY], rule=dict_entry[VALUE])


class EventRuleTargetEntry:
    rule_logical_name: str
    target_entry: dict

    def __init__(self, rule_logical_name: str, target_entry: dict):
        self.rule_logical_name = rule_logical_name
        self.target_entry = target_entry

    @staticmethod
    def from_dict(rule_name: str, target_entry: dict[str, Any]) -> EventRuleTargetEntry:
        return EventRuleTargetEntry(rule_logical_name=rule_name, target_entry=target_entry)
