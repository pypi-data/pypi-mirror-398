"""AWS container resource collectors."""

from typing import Dict, List, Any, Optional

from ..base import BaseCollector


class ContainerCollector(BaseCollector):
    """Collector for AWS container resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize container collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    @staticmethod
    def _get_repository_policy(ecr, repository_name: str) -> Dict[str, Any]:
        """
        Get repository policy for an ECR repository.

        :param ecr: ECR client
        :param str repository_name: Name of the repository
        :return: Repository policy or None if not found
        :rtype: Dict[str, Any]
        """
        try:
            return ecr.get_repository_policy(repositoryName=repository_name).get("policyText")
        except Exception as ex:
            from regscale.core.app.utils.app_utils import create_logger

            create_logger().debug(f"Error getting repository policy for {repository_name}: {ex}")
            return None

    @staticmethod
    def _get_repository_images(ecr, repository_name: str) -> List[Dict[str, Any]]:
        """
        Get image details for an ECR repository.

        :param ecr: ECR client
        :param str repository_name: Name of the repository
        :return: List of image details
        :rtype: List[Dict[str, Any]]
        """
        images = []
        image_paginator = ecr.get_paginator("describe_images")
        for image_page in image_paginator.paginate(repositoryName=repository_name):
            for image in image_page.get("imageDetails", []):
                images.append(
                    {
                        "ImageDigest": image.get("imageDigest"),
                        "ImageTags": image.get("imageTags", []),
                        "ImageSizeInBytes": image.get("imageSizeInBytes"),
                        "ImagePushedAt": str(image.get("imagePushedAt")),
                        "ImageScanStatus": image.get("imageScanStatus", {}),
                        "ImageScanFindingsSummary": image.get("imageScanFindingsSummary", {}),
                    }
                )
        return images

    def _build_repository_data(
        self, repo: Dict[str, Any], policy: Dict[str, Any], images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build repository data dictionary.

        :param repo: Raw repository data
        :param policy: Repository policy
        :param images: List of image details
        :return: Processed repository data
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "RepositoryName": repo.get("repositoryName"),
            "RepositoryArn": repo.get("repositoryArn"),
            "RegistryId": repo.get("registryId"),
            "RepositoryUri": repo.get("repositoryUri"),
            "CreatedAt": str(repo.get("createdAt")),
            "ImageTagMutability": repo.get("imageTagMutability"),
            "ImageScanningConfiguration": repo.get("imageScanningConfiguration", {}),
            "EncryptionConfiguration": repo.get("encryptionConfiguration", {}),
            "Policy": policy,
            "Images": images,
        }

    def _should_include_repository(self, ecr, repo_arn: str) -> bool:
        """
        Check if repository should be included based on account and tag filters.

        :param ecr: ECR client
        :param str repo_arn: Repository ARN
        :return: True if repository should be included, False otherwise
        :rtype: bool
        """
        if not self._matches_account(repo_arn):
            return False

        if self.tags:
            try:
                tags_response = ecr.list_tags_for_resource(resourceArn=repo_arn)
                repo_tags = tags_response.get("tags", [])
                return self._matches_tags(repo_tags)
            except Exception:
                return False

        return True

    def _process_single_repository(self, ecr, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single repository, retrieving policy, images, and building data.

        :param ecr: ECR client
        :param repo: Repository data
        :return: Processed repository data
        :rtype: Dict[str, Any]
        """
        repo_name = repo["repositoryName"]
        policy = self._get_repository_policy(ecr, repo_name)
        images = self._get_repository_images(ecr, repo_name)
        return self._build_repository_data(repo, policy, images)

    def get_ecr_repositories(self) -> List[Dict[str, Any]]:
        """
        Get information about ECR repositories with filtering.

        :return: List of ECR repository information
        :rtype: List[Dict[str, Any]]
        """
        repositories = []
        try:
            ecr = self._get_client("ecr")
            paginator = ecr.get_paginator("describe_repositories")

            for page in paginator.paginate():
                for repo in page.get("repositories", []):
                    try:
                        repo_arn = repo.get("repositoryArn", "")

                        if not self._should_include_repository(ecr, repo_arn):
                            continue

                        repo_data = self._process_single_repository(ecr, repo)
                        repositories.append(repo_data)
                    except Exception as e:
                        self._handle_error(e, f"ECR repository {repo['repositoryName']}")
        except Exception as e:
            self._handle_error(e, "ECR repositories")
        return repositories

    def collect(self) -> Dict[str, Any]:
        """
        Collect container resources based on enabled_services configuration.

        :return: Dictionary containing enabled container resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # ECR Repositories
        if self.enabled_services.get("ecr", True):
            result["ECRRepositories"] = self.get_ecr_repositories()

        return result
