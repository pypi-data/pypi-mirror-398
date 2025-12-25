"""AWS developer tools resource collectors."""

import logging
from typing import Dict, List, Any, Optional

from ..base import BaseCollector

logger = logging.getLogger("regscale")


class DeveloperToolsCollector(BaseCollector):
    """Collector for AWS developer tools resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize developer tools collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_codepipeline_pipelines(self) -> List[Dict[str, Any]]:
        """
        Get information about CodePipeline pipelines.

        :return: List of CodePipeline pipeline information
        :rtype: List[Dict[str, Any]]
        """
        pipelines = []
        try:
            codepipeline_client = self._get_client("codepipeline")
            paginator = codepipeline_client.get_paginator("list_pipelines")

            for page in paginator.paginate():
                for pipeline_summary in page.get("pipelines", []):
                    pipeline_name = pipeline_summary.get("name")

                    try:
                        pipeline_detail = codepipeline_client.get_pipeline(name=pipeline_name)
                        pipeline = pipeline_detail.get("pipeline", {})
                        pipeline_arn = pipeline.get("pipelineArn", "")

                        if not self._matches_account(pipeline_arn):
                            continue

                        tags_response = codepipeline_client.list_tags_for_resource(resourceArn=pipeline_arn)
                        pipeline_tags = tags_response.get("tags", [])

                        if not self._matches_tags(pipeline_tags):
                            continue

                        pipelines.append(
                            {
                                "Region": self.region,
                                "PipelineName": pipeline_name,
                                "PipelineArn": pipeline_arn,
                                "RoleArn": pipeline.get("roleArn"),
                                "Version": pipeline.get("version"),
                                "Created": pipeline_summary.get("created"),
                                "Updated": pipeline_summary.get("updated"),
                                "Tags": pipeline_tags,
                            }
                        )
                    except Exception as pipeline_error:
                        logger.debug("Error getting CodePipeline details for %s: %s", pipeline_name, pipeline_error)
                        continue

        except Exception as e:
            self._handle_error(e, "CodePipeline pipelines")
        return pipelines

    def get_codebuild_projects(self) -> List[Dict[str, Any]]:
        """
        Get information about CodeBuild projects.

        :return: List of CodeBuild project information
        :rtype: List[Dict[str, Any]]
        """
        projects = []
        try:
            codebuild_client = self._get_client("codebuild")
            paginator = codebuild_client.get_paginator("list_projects")

            for page in paginator.paginate():
                project_names = page.get("projects", [])

                if not project_names:
                    continue

                batch_response = codebuild_client.batch_get_projects(names=project_names)
                for project in batch_response.get("projects", []):
                    project_arn = project.get("arn", "")

                    if not self._matches_account(project_arn):
                        continue

                    if not self._matches_tags(project.get("tags", [])):
                        continue

                    projects.append(
                        {
                            "Region": self.region,
                            "ProjectName": project.get("name"),
                            "ProjectArn": project_arn,
                            "Description": project.get("description"),
                            "ServiceRole": project.get("serviceRole"),
                            "Created": project.get("created"),
                            "LastModified": project.get("lastModified"),
                            "Environment": project.get("environment"),
                            "Tags": project.get("tags", []),
                        }
                    )

        except Exception as e:
            self._handle_error(e, "CodeBuild projects")
        return projects

    def get_codedeploy_applications(self) -> List[Dict[str, Any]]:
        """
        Get information about CodeDeploy applications.

        :return: List of CodeDeploy application information
        :rtype: List[Dict[str, Any]]
        """
        applications = []
        try:
            codedeploy_client = self._get_client("codedeploy")
            paginator = codedeploy_client.get_paginator("list_applications")

            for page in paginator.paginate():
                for app_name in page.get("applications", []):
                    try:
                        app_detail = codedeploy_client.get_application(applicationName=app_name)
                        application = app_detail.get("application", {})
                        app_arn = f"arn:aws:codedeploy:{self.region}:{self.account_id or '*'}:application:{app_name}"

                        if not self._matches_account(app_arn):
                            continue

                        tags_response = codedeploy_client.list_tags_for_resource(ResourceArn=app_arn)
                        app_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(app_tags):
                            continue

                        applications.append(
                            {
                                "Region": self.region,
                                "ApplicationName": app_name,
                                "ApplicationId": application.get("applicationId"),
                                "CreateTime": application.get("createTime"),
                                "ComputePlatform": application.get("computePlatform"),
                                "Tags": app_tags,
                            }
                        )
                    except Exception as app_error:
                        logger.debug("Error getting CodeDeploy application details for %s: %s", app_name, app_error)
                        continue

        except Exception as e:
            self._handle_error(e, "CodeDeploy applications")
        return applications

    def get_codecommit_repositories(self) -> List[Dict[str, Any]]:
        """
        Get information about CodeCommit repositories.

        :return: List of CodeCommit repository information
        :rtype: List[Dict[str, Any]]
        """
        repositories = []
        try:
            codecommit_client = self._get_client("codecommit")
            paginator = codecommit_client.get_paginator("list_repositories")

            for page in paginator.paginate():
                for repo_metadata in page.get("repositories", []):
                    repo_name = repo_metadata.get("repositoryName")

                    try:
                        repo_detail = codecommit_client.get_repository(repositoryName=repo_name)
                        repository = repo_detail.get("repositoryMetadata", {})
                        repo_arn = repository.get("Arn", "")

                        if not self._matches_account(repo_arn):
                            continue

                        tags_response = codecommit_client.list_tags_for_resource(resourceArn=repo_arn)
                        repo_tags = tags_response.get("tags", {})

                        if not self._matches_tags(repo_tags):
                            continue

                        repositories.append(
                            {
                                "Region": self.region,
                                "RepositoryName": repo_name,
                                "RepositoryId": repository.get("repositoryId"),
                                "RepositoryArn": repo_arn,
                                "DefaultBranch": repository.get("defaultBranch"),
                                "CloneUrlHttp": repository.get("cloneUrlHttp"),
                                "CloneUrlSsh": repository.get("cloneUrlSsh"),
                                "CreationDate": repository.get("creationDate"),
                                "LastModifiedDate": repository.get("lastModifiedDate"),
                                "Tags": repo_tags,
                            }
                        )
                    except Exception as repo_error:
                        logger.debug("Error getting CodeCommit repository details for %s: %s", repo_name, repo_error)
                        continue

        except Exception as e:
            self._handle_error(e, "CodeCommit repositories")
        return repositories

    def collect(self) -> Dict[str, Any]:
        """
        Collect developer tools resources based on enabled_services configuration.

        :return: Dictionary containing enabled developer tools resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # CodePipeline
        if self.enabled_services.get("codepipeline", True):
            result["CodePipelinePipelines"] = self.get_codepipeline_pipelines()

        # CodeBuild
        if self.enabled_services.get("codebuild", True):
            result["CodeBuildProjects"] = self.get_codebuild_projects()

        # CodeDeploy
        if self.enabled_services.get("codedeploy", True):
            result["CodeDeployApplications"] = self.get_codedeploy_applications()

        # CodeCommit
        if self.enabled_services.get("codecommit", True):
            result["CodeCommitRepositories"] = self.get_codecommit_repositories()

        return result
