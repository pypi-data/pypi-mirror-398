from fluidattacks_core.logging.sources.types import SourceStrategy
from fluidattacks_core.logging.sources.utils import get_env_var, get_environment, get_version


class DefaultSource(SourceStrategy):
    @staticmethod
    def detect() -> bool:
        return True

    @staticmethod
    def log_metadata() -> dict[str, str]:
        return {
            "ddsource": "python",
            "dd.service": get_env_var("PRODUCT_ID") or "unknown",
            "dd.version": get_version(),
            "deployment.environment": get_environment(),
        }


class LambdaSource(SourceStrategy):
    @staticmethod
    def detect() -> bool:
        return get_env_var("AWS_LAMBDA_FUNCTION_NAME") is not None

    @staticmethod
    def log_metadata() -> dict[str, str]:
        return {
            "ddsource": "lambda",
            "dd.service": get_env_var("AWS_LAMBDA_FUNCTION_NAME") or "unknown",
            "dd.version": get_version(),
            "deployment.environment": get_environment(),
        }


class BatchSource(SourceStrategy):
    @staticmethod
    def detect() -> bool:
        return get_env_var("AWS_BATCH_JOB_ID") is not None

    @staticmethod
    def log_metadata() -> dict[str, str]:
        job_name = get_env_var("JOB_NAME")
        job_definition_name = get_env_var("JOB_DEFINITION_NAME")
        job_queue = get_env_var("AWS_BATCH_JQ_NAME")
        product_id = get_env_var("PRODUCT_ID")
        service = (
            job_name or job_definition_name or (f"from-{job_queue}" if job_queue else product_id)
        )
        return {
            "ddsource": "batch",
            "dd.service": service or "unknown",
            "dd.version": get_version(),
            "deployment.environment": get_environment(),
        }


class PipelineSource(SourceStrategy):
    @staticmethod
    def detect() -> bool:
        return PipelineSource._get_pipeline_metadata() is not None

    @staticmethod
    def log_metadata() -> dict[str, str]:
        metadata = PipelineSource._get_pipeline_metadata()

        return {
            "ddsource": "ci",
            "dd.service": get_env_var("PRODUCT_ID") or "unknown",
            "dd.version": get_version(),
            "deployment.environment": get_environment(),
            **(metadata or {}),
        }

    @staticmethod
    def _get_pipeline_metadata() -> dict[str, str] | None:
        pipeline = None
        if get_env_var("CI_JOB_ID"):
            pipeline = "gitlab_ci"
        elif get_env_var("CIRCLECI"):
            pipeline = "circleci"
        elif get_env_var("System.JobId"):
            pipeline = "azure_devops"
        elif get_env_var("BUILD_NUMBER"):
            pipeline = "jenkins"

        if pipeline is None:
            return None

        return {
            "ddsource": f"ci/{pipeline}",
            "deployment.pipeline.type": pipeline,
            **(
                {
                    "deployment.pipeline.CI_JOB_ID": get_env_var("CI_JOB_ID") or "unknown",
                    "deployment.pipeline.CI_JOB_URL": get_env_var("CI_JOB_URL") or "unknown",
                }
                if pipeline == "gitlab_ci"
                else {}
            ),
            **(
                {
                    "deployment.pipeline.CIRCLE_BUILD_NUM": get_env_var("CIRCLE_BUILD_NUM")
                    or "unknown",
                    "deployment.pipeline.CIRCLE_BUILD_URL": get_env_var("CIRCLE_BUILD_URL")
                    or "unknown",
                }
                if pipeline == "circleci"
                else {}
            ),
            **(
                {
                    "deployment.pipeline.System.JobId": get_env_var("System.JobId") or "unknown",
                }
                if pipeline == "azure_devops"
                else {}
            ),
            **(
                {
                    "deployment.pipeline.BUILD_NUMBER": get_env_var("BUILD_NUMBER") or "unknown",
                    "deployment.pipeline.BUILD_ID": get_env_var("BUILD_ID") or "unknown",
                    "deployment.pipeline.BUILD_URL": get_env_var("BUILD_URL") or "unknown",
                }
                if pipeline == "jenkins"
                else {}
            ),
        }


class ContainerSource(SourceStrategy):
    @staticmethod
    def detect() -> bool:
        return (
            get_env_var("CONTAINER_IMAGE") is not None
            or get_env_var("CONTAINER_NAME") is not None
            or get_env_var("CONTAINER_IMAGE_PATH") is not None
        )

    @staticmethod
    def log_metadata() -> dict[str, str]:
        return {
            "ddsource": "container",
            "dd.service": get_env_var("PRODUCT_ID") or "unknown",
            "dd.version": get_version(),
            "deployment.environment": get_environment(),
        }


__all__ = [
    "BatchSource",
    "ContainerSource",
    "DefaultSource",
    "LambdaSource",
    "PipelineSource",
]
