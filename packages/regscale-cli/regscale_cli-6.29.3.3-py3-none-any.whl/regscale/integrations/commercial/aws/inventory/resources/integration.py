"""AWS application integration resource collectors."""

from typing import Dict, List, Any, Optional

from ..base import BaseCollector


class IntegrationCollector(BaseCollector):
    """Collector for AWS application integration resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize integration collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_api_gateways(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about API Gateway APIs (REST and HTTP).

        :return: Dictionary containing API Gateway information
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        apis = {"REST": [], "HTTP": []}
        try:
            # Get REST APIs
            apigw = self._get_client("apigateway")
            rest_paginator = apigw.get_paginator("get_rest_apis")

            for page in rest_paginator.paginate():
                for api in page.get("items", []):
                    try:
                        stages = apigw.get_stages(restApiId=api["id"])["item"]
                        apis["REST"].append(
                            {
                                "Region": self.region,
                                "Id": api.get("id"),
                                "Name": api.get("name"),
                                "Description": api.get("description"),
                                "CreatedDate": str(api.get("createdDate")),
                                "Version": api.get("version"),
                                "EndpointConfiguration": api.get("endpointConfiguration", {}),
                                "Stages": [
                                    {
                                        "StageName": stage.get("stageName"),
                                        "DeploymentId": stage.get("deploymentId"),
                                        "Description": stage.get("description"),
                                        "CreatedDate": str(stage.get("createdDate")),
                                        "LastUpdatedDate": str(stage.get("lastUpdatedDate")),
                                    }
                                    for stage in stages
                                ],
                            }
                        )
                    except Exception as e:
                        self._handle_error(e, f"REST API {api['name']}")

            # Get HTTP APIs
            apigwv2 = self._get_client("apigatewayv2")
            http_paginator = apigwv2.get_paginator("get_apis")

            for page in http_paginator.paginate():
                for api in page.get("Items", []):
                    try:
                        stages = apigwv2.get_stages(ApiId=api["ApiId"])["Items"]
                        apis["HTTP"].append(
                            {
                                "Region": self.region,
                                "Id": api.get("ApiId"),
                                "Name": api.get("Name"),
                                "Description": api.get("Description"),
                                "ProtocolType": api.get("ProtocolType"),
                                "CreatedDate": str(api.get("CreatedDate")),
                                "ApiEndpoint": api.get("ApiEndpoint"),
                                "Stages": [
                                    {
                                        "StageName": stage.get("StageName"),
                                        "Description": stage.get("Description"),
                                        "CreatedDate": str(stage.get("CreatedDate")),
                                        "LastUpdatedDate": str(stage.get("LastUpdatedDate")),
                                        "DefaultRouteSettings": stage.get("DefaultRouteSettings", {}),
                                    }
                                    for stage in stages
                                ],
                            }
                        )
                    except Exception as e:
                        self._handle_error(e, f"HTTP API {api['Name']}")
        except Exception as e:
            self._handle_error(e, "API Gateway APIs")
        return apis

    def _should_include_topic(self, sns, topic_arn: str) -> bool:
        """
        Check if topic should be included based on account and tag filters.

        :param sns: SNS client
        :param str topic_arn: Topic ARN
        :return: True if topic should be included, False otherwise
        :rtype: bool
        """
        if not self._matches_account(topic_arn):
            return False

        if self.tags:
            try:
                tags_response = sns.list_tags_for_resource(ResourceArn=topic_arn)
                topic_tags = tags_response.get("Tags", [])
                return self._matches_tags(topic_tags)
            except Exception:
                return False

        return True

    def _get_topic_subscriptions(self, sns, topic_arn: str) -> List[Dict[str, Any]]:
        """
        Get all subscriptions for a topic.

        :param sns: SNS client
        :param str topic_arn: Topic ARN
        :return: List of subscriptions
        :rtype: List[Dict[str, Any]]
        """
        subs = []
        sub_paginator = sns.get_paginator("list_subscriptions_by_topic")
        for sub_page in sub_paginator.paginate(TopicArn=topic_arn):
            subs.extend(sub_page.get("Subscriptions", []))
        return subs

    def _build_topic_data(self, topic_arn: str, attrs: Dict[str, Any], subs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build topic data dictionary.

        :param str topic_arn: Topic ARN
        :param attrs: Topic attributes
        :param subs: List of subscriptions
        :return: Processed topic data
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "TopicArn": topic_arn,
            "Owner": attrs.get("Owner"),
            "Policy": attrs.get("Policy"),
            "DisplayName": attrs.get("DisplayName"),
            "SubscriptionsConfirmed": attrs.get("SubscriptionsConfirmed"),
            "SubscriptionsPending": attrs.get("SubscriptionsPending"),
            "SubscriptionsDeleted": attrs.get("SubscriptionsDeleted"),
            "Subscriptions": [
                {
                    "SubscriptionArn": sub.get("SubscriptionArn"),
                    "Protocol": sub.get("Protocol"),
                    "Endpoint": sub.get("Endpoint"),
                }
                for sub in subs
            ],
        }

    def get_sns_topics(self) -> List[Dict[str, Any]]:
        """
        Get information about SNS topics with filtering.

        :return: List of SNS topic information
        :rtype: List[Dict[str, Any]]
        """
        topics = []
        try:
            sns = self._get_client("sns")
            paginator = sns.get_paginator("list_topics")

            for page in paginator.paginate():
                for topic in page.get("Topics", []):
                    try:
                        topic_arn = topic["TopicArn"]

                        if not self._should_include_topic(sns, topic_arn):
                            continue

                        attrs = sns.get_topic_attributes(TopicArn=topic_arn)["Attributes"]
                        subs = self._get_topic_subscriptions(sns, topic_arn)
                        topic_data = self._build_topic_data(topic_arn, attrs, subs)
                        topics.append(topic_data)
                    except Exception as e:
                        self._handle_error(e, f"SNS topic {topic['TopicArn']}")
        except Exception as e:
            self._handle_error(e, "SNS topics")
        return topics

    def _should_include_queue(self, sqs, queue_arn: str, queue_url: str) -> bool:
        """
        Check if queue should be included based on account and tag filters.

        :param sqs: SQS client
        :param str queue_arn: Queue ARN
        :param str queue_url: Queue URL
        :return: True if queue should be included, False otherwise
        :rtype: bool
        """
        if not self._matches_account(queue_arn):
            return False

        if self.tags:
            try:
                tags_response = sqs.list_queue_tags(QueueUrl=queue_url)
                queue_tags = tags_response.get("Tags", {})
                return self._matches_tags(queue_tags)
            except Exception:
                return False

        return True

    def _build_queue_data(self, queue_url: str, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build queue data dictionary.

        :param str queue_url: Queue URL
        :param attrs: Queue attributes
        :return: Processed queue data
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "QueueUrl": queue_url,
            "QueueArn": attrs.get("QueueArn"),
            "ApproximateNumberOfMessages": attrs.get("ApproximateNumberOfMessages"),
            "ApproximateNumberOfMessagesNotVisible": attrs.get("ApproximateNumberOfMessagesNotVisible"),
            "ApproximateNumberOfMessagesDelayed": attrs.get("ApproximateNumberOfMessagesDelayed"),
            "CreatedTimestamp": attrs.get("CreatedTimestamp"),
            "LastModifiedTimestamp": attrs.get("LastModifiedTimestamp"),
            "VisibilityTimeout": attrs.get("VisibilityTimeout"),
            "MaximumMessageSize": attrs.get("MaximumMessageSize"),
            "MessageRetentionPeriod": attrs.get("MessageRetentionPeriod"),
            "DelaySeconds": attrs.get("DelaySeconds"),
            "Policy": attrs.get("Policy"),
            "RedrivePolicy": attrs.get("RedrivePolicy"),
        }

    def get_sqs_queues(self) -> List[Dict[str, Any]]:
        """
        Get information about SQS queues with filtering.

        :return: List of SQS queue information
        :rtype: List[Dict[str, Any]]
        """
        queues = []
        try:
            sqs = self._get_client("sqs")
            paginator = sqs.get_paginator("list_queues")

            for page in paginator.paginate():
                for queue_url in page.get("QueueUrls", []):
                    try:
                        attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["All"])["Attributes"]
                        queue_arn = attrs.get("QueueArn", "")

                        if not self._should_include_queue(sqs, queue_arn, queue_url):
                            continue

                        queue_data = self._build_queue_data(queue_url, attrs)
                        queues.append(queue_data)
                    except Exception as e:
                        self._handle_error(e, f"SQS queue {queue_url}")
        except Exception as e:
            self._handle_error(e, "SQS queues")
        return queues

    def get_eventbridge_rules(self) -> List[Dict[str, Any]]:
        """
        Get information about EventBridge rules.

        :return: List of EventBridge rule information
        :rtype: List[Dict[str, Any]]
        """
        rules = []
        try:
            events = self._get_client("events")
            paginator = events.get_paginator("list_rules")

            for page in paginator.paginate():
                for rule in page.get("Rules", []):
                    try:
                        # Get targets for this rule
                        targets = events.list_targets_by_rule(Rule=rule["Name"])["Targets"]

                        rules.append(
                            {
                                "Region": self.region,
                                "Name": rule.get("Name"),
                                "Arn": rule.get("Arn"),
                                "Description": rule.get("Description"),
                                "State": rule.get("State"),
                                "ScheduleExpression": rule.get("ScheduleExpression"),
                                "EventPattern": rule.get("EventPattern"),
                                "Targets": [
                                    {
                                        "Id": target.get("Id"),
                                        "Arn": target.get("Arn"),
                                        "RoleArn": target.get("RoleArn"),
                                        "Input": target.get("Input"),
                                        "InputPath": target.get("InputPath"),
                                    }
                                    for target in targets
                                ],
                            }
                        )
                    except Exception as e:
                        self._handle_error(e, f"EventBridge rule {rule['Name']}")
        except Exception as e:
            self._handle_error(e, "EventBridge rules")
        return rules

    def collect(self) -> Dict[str, Any]:
        """
        Collect application integration resources based on enabled_services configuration.

        :return: Dictionary containing enabled application integration resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # API Gateway
        if self.enabled_services.get("api_gateway", True):
            result["APIGateway"] = self.get_api_gateways()

        # SNS Topics
        if self.enabled_services.get("sns", True):
            result["SNSTopics"] = self.get_sns_topics()

        # SQS Queues
        if self.enabled_services.get("sqs", True):
            result["SQSQueues"] = self.get_sqs_queues()

        # EventBridge Rules
        if self.enabled_services.get("eventbridge", True):
            result["EventBridgeRules"] = self.get_eventbridge_rules()

        return result
