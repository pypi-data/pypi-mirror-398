#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Cloud Logging resource collectors.

This module provides collectors for GCP Cloud Logging resources including:
- Log sinks (export destinations)
- Log buckets (storage)
- Log metrics (custom metrics from logs)
- Audit log configuration
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class LoggingCollector(BaseCollector):
    """Collector for GCP Cloud Logging resources."""

    # GCP asset types for logging resources
    supported_asset_types: List[str] = [
        "logging.googleapis.com/LogSink",
        "logging.googleapis.com/LogBucket",
        "logging.googleapis.com/LogMetric",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the logging collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_log_sinks(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Logging sinks.

        Log sinks are export destinations for log entries.

        :return: List of log sink information
        :rtype: List[Dict[str, Any]]
        """
        sinks = []
        try:
            from google.cloud import logging_v2

            client = logging_v2.ConfigServiceV2Client()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for log sinks collection")
                return sinks

            # List sinks for the project
            parent = f"projects/{project}"
            request = logging_v2.ListSinksRequest(parent=parent)

            for sink in client.list_sinks(request=request):
                sinks.append(self._parse_log_sink(sink))

        except Exception as e:
            self._handle_error(e, "log sinks")

        return sinks

    def _get_attr_or_default(self, obj: Any, attr_name: str, default: Any = None) -> Any:
        """Get an attribute from an object or return a default value.

        :param obj: Object to get attribute from
        :param attr_name: Name of the attribute
        :param default: Default value if attribute doesn't exist
        :return: Attribute value or default
        :rtype: Any
        """
        return getattr(obj, attr_name, default) if hasattr(obj, attr_name) else default

    def _extract_enum_value(self, obj: Any, attr_name: str) -> Optional[str]:
        """Extract an enum value as string from an object attribute.

        :param obj: Object containing the attribute
        :param attr_name: Name of the attribute to extract
        :return: String representation of the enum value or None
        :rtype: Optional[str]
        """
        if not hasattr(obj, attr_name):
            return None
        attr = getattr(obj, attr_name, None)
        if attr is None:
            return None
        return attr.name if hasattr(attr, "name") else str(attr)

    def _format_timestamp(self, obj: Any, attr_name: str) -> Optional[str]:
        """Format a timestamp attribute to ISO format string.

        :param obj: Object containing the timestamp attribute
        :param attr_name: Name of the timestamp attribute
        :return: ISO formatted timestamp string or None
        :rtype: Optional[str]
        """
        if not hasattr(obj, attr_name):
            return None
        timestamp = getattr(obj, attr_name, None)
        return timestamp.isoformat() if timestamp else None

    def _parse_log_sink(self, sink: Any) -> Dict[str, Any]:
        """Parse a log sink to a dictionary.

        :param sink: Log sink object
        :return: Parsed sink data
        :rtype: Dict[str, Any]
        """
        output_version_format = self._extract_enum_value(sink, "output_version_format")

        return {
            "name": sink.name,
            "destination": sink.destination,
            "filter": sink.filter,
            "description": self._get_attr_or_default(sink, "description"),
            "disabled": self._get_attr_or_default(sink, "disabled", False),
            "writer_identity": self._get_attr_or_default(sink, "writer_identity"),
            "include_children": self._get_attr_or_default(sink, "include_children", False),
            "create_time": self._format_timestamp(sink, "create_time"),
            "update_time": self._format_timestamp(sink, "update_time"),
            "output_version_format": output_version_format,
        }

    def get_log_buckets(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Logging buckets.

        Log buckets are storage containers for log entries.

        :return: List of log bucket information
        :rtype: List[Dict[str, Any]]
        """
        buckets = []
        try:
            from google.cloud import logging_v2

            client = logging_v2.ConfigServiceV2Client()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for log buckets collection")
                return buckets

            # List buckets for the project in all locations
            parent = f"projects/{project}/locations/-"
            request = logging_v2.ListBucketsRequest(parent=parent)

            for bucket in client.list_buckets(request=request):
                buckets.append(self._parse_log_bucket(bucket))

        except Exception as e:
            self._handle_error(e, "log buckets")

        return buckets

    def _get_restricted_fields(self, bucket: Any) -> List[str]:
        """Extract restricted fields list from a log bucket.

        :param bucket: Log bucket object
        :return: List of restricted field names
        :rtype: List[str]
        """
        if not hasattr(bucket, "restricted_fields"):
            return []
        if not bucket.restricted_fields:
            return []
        return list(bucket.restricted_fields)

    def _parse_log_bucket(self, bucket: Any) -> Dict[str, Any]:
        """Parse a log bucket to a dictionary.

        :param bucket: Log bucket object
        :return: Parsed bucket data
        :rtype: Dict[str, Any]
        """
        lifecycle_state = self._extract_enum_value(bucket, "lifecycle_state")

        return {
            "name": bucket.name,
            "description": self._get_attr_or_default(bucket, "description"),
            "retention_days": self._get_attr_or_default(bucket, "retention_days"),
            "locked": self._get_attr_or_default(bucket, "locked", False),
            "lifecycle_state": lifecycle_state,
            "create_time": self._format_timestamp(bucket, "create_time"),
            "update_time": self._format_timestamp(bucket, "update_time"),
            "restricted_fields": self._get_restricted_fields(bucket),
            "analytics_enabled": self._get_attr_or_default(bucket, "analytics_enabled", False),
        }

    def get_log_metrics(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Logging metrics.

        Log metrics are custom metrics based on log entries.

        :return: List of log metric information
        :rtype: List[Dict[str, Any]]
        """
        metrics = []
        try:
            from google.cloud import logging_v2

            client = logging_v2.MetricsServiceV2Client()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for log metrics collection")
                return metrics

            # List metrics for the project
            parent = f"projects/{project}"
            request = logging_v2.ListLogMetricsRequest(parent=parent)

            for metric in client.list_log_metrics(request=request):
                metrics.append(self._parse_log_metric(metric))

        except Exception as e:
            self._handle_error(e, "log metrics")

        return metrics

    def _parse_metric_descriptor(self, metric: Any) -> Optional[Dict[str, Any]]:
        """Parse metric descriptor from a log metric.

        :param metric: Log metric object
        :return: Parsed metric descriptor data or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(metric, "metric_descriptor") or not metric.metric_descriptor:
            return None
        descriptor = metric.metric_descriptor
        metric_kind = self._extract_enum_value(descriptor, "metric_kind")
        value_type = self._extract_enum_value(descriptor, "value_type")
        return {
            "name": descriptor.name,
            "type": descriptor.type,
            "metric_kind": metric_kind,
            "value_type": value_type,
            "unit": descriptor.unit,
            "description": descriptor.description,
        }

    def _get_label_extractors(self, metric: Any) -> Dict[str, str]:
        """Extract label extractors from a log metric.

        :param metric: Log metric object
        :return: Dictionary of label extractors
        :rtype: Dict[str, str]
        """
        if not hasattr(metric, "label_extractors"):
            return {}
        if not metric.label_extractors:
            return {}
        return dict(metric.label_extractors)

    def _get_bucket_options(self, metric: Any) -> Optional[Dict[str, Any]]:
        """Extract bucket options from a log metric.

        :param metric: Log metric object
        :return: Parsed bucket options or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(metric, "bucket_options"):
            return None
        if not metric.bucket_options:
            return None
        return self._parse_bucket_options(metric.bucket_options)

    def _parse_log_metric(self, metric: Any) -> Dict[str, Any]:
        """Parse a log metric to a dictionary.

        :param metric: Log metric object
        :return: Parsed metric data
        :rtype: Dict[str, Any]
        """
        version = self._extract_enum_value(metric, "version")

        return {
            "name": metric.name,
            "description": self._get_attr_or_default(metric, "description"),
            "filter": metric.filter,
            "disabled": self._get_attr_or_default(metric, "disabled", False),
            "metric_descriptor": self._parse_metric_descriptor(metric),
            "value_extractor": self._get_attr_or_default(metric, "value_extractor"),
            "label_extractors": self._get_label_extractors(metric),
            "bucket_options": self._get_bucket_options(metric),
            "create_time": self._format_timestamp(metric, "create_time"),
            "update_time": self._format_timestamp(metric, "update_time"),
            "version": version,
        }

    def _parse_bucket_options(self, bucket_options: Any) -> Dict[str, Any]:
        """Parse bucket options for distribution metrics.

        :param bucket_options: Bucket options object
        :return: Parsed bucket options data
        :rtype: Dict[str, Any]
        """
        result = {}
        if hasattr(bucket_options, "linear_buckets") and bucket_options.linear_buckets:
            result["linear_buckets"] = {
                "num_finite_buckets": bucket_options.linear_buckets.num_finite_buckets,
                "width": bucket_options.linear_buckets.width,
                "offset": bucket_options.linear_buckets.offset,
            }
        if hasattr(bucket_options, "exponential_buckets") and bucket_options.exponential_buckets:
            result["exponential_buckets"] = {
                "num_finite_buckets": bucket_options.exponential_buckets.num_finite_buckets,
                "growth_factor": bucket_options.exponential_buckets.growth_factor,
                "scale": bucket_options.exponential_buckets.scale,
            }
        if hasattr(bucket_options, "explicit_buckets") and bucket_options.explicit_buckets:
            result["explicit_buckets"] = {
                "bounds": list(bucket_options.explicit_buckets.bounds),
            }
        return result

    def _parse_audit_log_config(self, log_config: Any) -> Dict[str, Any]:
        """Parse a single audit log config to a dictionary.

        :param log_config: Audit log config object
        :return: Parsed audit log config data
        :rtype: Dict[str, Any]
        """
        log_type = self._extract_enum_value(log_config, "log_type")
        exempted_members = list(log_config.exempted_members) if log_config.exempted_members else []
        return {"log_type": log_type, "exempted_members": exempted_members}

    def _parse_audit_config(self, audit_config: Any) -> Dict[str, Any]:
        """Parse an audit config to a dictionary.

        :param audit_config: Audit config object from IAM policy
        :return: Parsed audit config data
        :rtype: Dict[str, Any]
        """
        audit_log_configs = []
        if hasattr(audit_config, "audit_log_configs") and audit_config.audit_log_configs:
            audit_log_configs = [self._parse_audit_log_config(lc) for lc in audit_config.audit_log_configs]
        return {"service": audit_config.service, "audit_log_configs": audit_log_configs}

    def _extract_audit_configs(self, policy: Any) -> List[Dict[str, Any]]:
        """Extract audit configs from an IAM policy.

        :param policy: IAM policy object
        :return: List of parsed audit configs
        :rtype: List[Dict[str, Any]]
        """
        if not hasattr(policy, "audit_configs") or not policy.audit_configs:
            return []
        return [self._parse_audit_config(ac) for ac in policy.audit_configs]

    def get_audit_log_config(self) -> Dict[str, Any]:
        """Get audit logging configuration for the project.

        Returns information about which audit log types are enabled.

        :return: Audit log configuration
        :rtype: Dict[str, Any]
        """
        config: Dict[str, Any] = {}
        try:
            from google.cloud import resourcemanager_v3

            client = resourcemanager_v3.ProjectsClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for audit log config collection")
                return config

            project_name = f"projects/{project}"
            request = resourcemanager_v3.GetIamPolicyRequest(resource=project_name)
            policy = client.get_iam_policy(request=request)

            config = {
                "project": project,
                "audit_configs": self._extract_audit_configs(policy),
            }

        except Exception as e:
            self._handle_error(e, "audit log configuration")

        return config

    def collect(self) -> Dict[str, Any]:
        """Collect logging resources based on enabled_services configuration.

        :return: Dictionary containing enabled logging resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Log Sinks
        if self.enabled_services.get("log_sinks", True):
            result["LogSinks"] = self.get_log_sinks()

        # Log Buckets
        if self.enabled_services.get("log_buckets", True):
            result["LogBuckets"] = self.get_log_buckets()

        # Log Metrics
        if self.enabled_services.get("log_metrics", True):
            result["LogMetrics"] = self.get_log_metrics()

        # Audit Log Configuration
        if self.enabled_services.get("audit_log_config", True):
            result["AuditLogConfig"] = self.get_audit_log_config()

        return result
