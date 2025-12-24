from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from attrs import define
from cfnlint import ConfigMixIn
from cfnlint.rules import CloudFormationLintRule, RuleMatch
from cfnlint.template.template import Template

from awsjavakit_cfn_rules.utils.functional import flatmap
from awsjavakit_cfn_rules.utils.invalid_config_exception import InvalidConfigException

EMPTY_DICT = {}


EXPECTED_TAGS_FIELD_NAME = "expected_tags"

CONFIG_DEFINITION = {
    EXPECTED_TAGS_FIELD_NAME: {"default": {}, "type": "list", "itemtype": "string"}
}

NON_TAGGABLE_RESOURCES = {"AWS::IAM::Policy",
                          "AWS::IAM::RolePolicy",
                          "AWS::IAM::Role",
                          "AWS::IAM::ManagedPolicy",
                          "AWS::CloudFormation::Stack",
                          "AWS::CloudWatch::Dashboard",
                          "AWS::Events::Rule",
                          "AWS::Lambda::EventInvokeConfig",
                          "AWS::Lambda::EventSourceMapping",  # sam does not add the tags in the event invoke configs
                          "AWS::Lambda::Permission",
                          "AWS::Scheduler::Schedule",
                          "AWS::SNS::Subscription",
                          "AWS::SQS::QueuePolicy",
                          "AWS::Budgets::Budget",
                          "AWS::SNS::TopicInlinePolicy",
                          "AWS::S3::BucketPolicy",
                          "AWS::SecretsManager::RotationSchedule",
                          "AWS::CloudFront::OriginAccessControl",
                          "AWS::CloudFront::CachePolicy",
                          "AWS::EC2::Route",
                          "AWS::EC2::SubnetRouteTableAssociation",
                          "AWS::EC2::VPCGatewayAttachment",
                          "AWS::EC2::InternetGateway"
                          }
TAGS_RULE_ID = "E9001"

EMPTY_DICT = {}
EMPTY_CONFIG = []


class TagsChecker(CloudFormationLintRule):

    id: str = TAGS_RULE_ID
    shortdesc: str = "Missing Tags Rule for Resources"
    description: str = "A rule for checking that all resources have the required tags"
    tags = ["tags"]
    experimental = False

    def __init__(self):
        super().__init__()
        self.config_definition = CONFIG_DEFINITION
        self.configure()

    def match(self, cfn: Template) -> list[RuleMatch]:
        tags_rule_config = TagsRuleConfig(self.config)
        tag_rules: list[TagRule] = tags_rule_config.tag_rules()
        matches = list(flatmap(lambda tag_rule: tag_rule.validate_template(cfn), tag_rules))
        return matches


@define
class TagsRuleConfig:
    rule_config_input: dict[str, list[str]]

    def tag_rules(self) -> list[TagRule]:
        tags: list[str] = self._extract_tag_config_as_dict()
        return [TagRule(expected_tag) for expected_tag in tags]

    def _extract_tag_config_as_dict(self) -> list[str]:
        config = self.rule_config_input.get(EXPECTED_TAGS_FIELD_NAME, [])
        if self._is_valid_format_(config):
            return config
        if self._is_empty_(config):
            return EMPTY_CONFIG
        raise InvalidConfigException("config is not correct")

    def _is_empty_(self, config: Any) -> bool:
        return isinstance(config, dict) and not config

    def _is_valid_format_(self, config: Any) -> bool:
        return isinstance(config, list)
    
    def as_cfn_config(self) -> ConfigMixIn:
        return ConfigMixIn(cli_args=None, **{EXPECTED_TAGS_FIELD_NAME: self.rule_config_input})  # type: ignore


@define
class TagRule:
    expected_tag: str

    def validate_template(self, cfn: Template) -> list[RuleMatch]:
        resources = cfn.get_resources()
        taggable_resources: dict[str,Any]= \
            {key: value for key,value in resources.items() if self._is_taggable_resource_(value) }

        matches = self._calculate_matches_(taggable_resources)
        return list(matches)

    def _calculate_matches_(self,  taggable_resources:dict[str,Any]):
        check_results: list[CheckResult] = \
            [self._calculate_missing_tags_(resource_name=key, resource=taggable_resources.get(key, EMPTY_DICT)) \
             for key in taggable_resources]
        non_empty_check_results: Iterable[CheckResult] = \
            [result for result in check_results if result != EMPTY_CHECK_RESULT]
        matches = map(lambda check_result: check_result.as_rule_match(), non_empty_check_results)
        return matches

    def _is_taggable_resource_(self, resource: dict) -> bool:
        return self._type_of_(resource) not in NON_TAGGABLE_RESOURCES

    def _type_of_(self, resource: dict[str, Any]):
        return resource.get("Type")

    def _calculate_missing_tags_(self, resource_name: str, resource: dict[str, Any]) -> CheckResult:
        if self.expected_tag not in self._extract_resource_tags(resource):
            return CheckResult(resource=resource, missing_tag=self.expected_tag, resource_name=resource_name)
        return EMPTY_CHECK_RESULT

    def _extract_resource_tags(self, resource: dict) -> list[str]:
        tags: Any = resource.get("Properties", {}).get("Tags")
        if isinstance(tags, list):
            return [tag.get('Key') for tag in tags if tag is not None]
        if isinstance(tags, dict):
            tags_as_dict: dict = tags
            return list(tags_as_dict.keys())
        return []


@define
class CheckResult:
    resource: dict[str, Any]
    resource_name: str
    missing_tag: str

    def as_rule_match(self) -> RuleMatch:
        return RuleMatch(path=["Resources", self.resource_name],
                         message=self._construct_message_())

    def _construct_message_(self) -> str:
        return f"Resource {self.resource_name}:{self._resource_type_()} is missing required tag:{self.missing_tag}"

    def _resource_type_(self) -> str:
        return str(self.resource.get("Type", ""))

@define
class EmptyCheckResult(CheckResult):
    pass

EMPTY_CHECK_RESULT = EmptyCheckResult(EMPTY_DICT,"","")