"""This module contains a custom validator for the JSON Schema specification.

The main motivation behind extending the existing JSON Schema validator is to
allow for case-insensitive enum matching since this is currently not supported
by the JSON Schema specification.
"""

import base64
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Tuple

import jsonschema
import requests
from colorama import Fore, Style
from filelock import FileLock

from konduktor import logging

SCHEMA_VERSION = 'v1.32.0-standalone-strict'
SCHEMA_CACHE_PATH = Path.home() / '.konduktor/schemas'
SCHEMA_LOCK_PATH = SCHEMA_CACHE_PATH / '.lock'
CACHE_MAX_AGE_SECONDS = 86400  # 24 hours

# Schema URLs for different Kubernetes resources
SCHEMA_URLS = {
    'podspec': f'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{SCHEMA_VERSION}/podspec.json',
    'deployment': f'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{SCHEMA_VERSION}/deployment.json',
    'service': f'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{SCHEMA_VERSION}/service.json',
    'horizontalpodautoscaler': f'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{SCHEMA_VERSION}/horizontalpodautoscaler-autoscaling-v2.json',
}

logger = logging.get_logger(__name__)


def _skip_image_checks() -> bool:
    val = os.getenv('KONDUKTOR_SKIP_IMAGE_CHECK', '')
    return val.lower() in ('1', 'true', 'yes', 'y')


def case_insensitive_enum(validator, enums, instance, schema):
    del validator, schema  # Unused.
    if instance.lower() not in [enum.lower() for enum in enums]:
        yield jsonschema.ValidationError(f'{instance!r} is not one of {enums!r}')


SchemaValidator = jsonschema.validators.extend(
    jsonschema.Draft7Validator,
    validators={'case_insensitive_enum': case_insensitive_enum},
)


def get_cached_schema(schema_type: str) -> dict:
    """Get cached schema for a specific Kubernetes resource type."""
    schema_url = SCHEMA_URLS.get(schema_type)
    if not schema_url:
        raise ValueError(f'Unknown schema type: {schema_type}')

    schema_file = SCHEMA_CACHE_PATH / f'{schema_type}.json'
    lock = FileLock(str(SCHEMA_LOCK_PATH))

    with lock:
        # Check if schema file exists and is fresh
        if schema_file.exists():
            age = time.time() - schema_file.stat().st_mtime
            # if fresh
            if age < CACHE_MAX_AGE_SECONDS:
                with open(schema_file, 'r') as f:
                    return json.load(f)

        # Download schema
        resp = requests.get(schema_url)
        resp.raise_for_status()

        SCHEMA_CACHE_PATH.mkdir(parents=True, exist_ok=True)
        with open(schema_file, 'w') as f:
            f.write(resp.text)

        return resp.json()


def _validate_k8s_spec(spec: dict, schema_type: str, resource_name: str) -> None:
    """Generic validation function for Kubernetes specs."""
    schema = get_cached_schema(schema_type)

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(spec), key=lambda e: e.path)

    if not errors:
        return

    formatted = [
        f'- {error.message}'
        + (f" at path: {' → '.join(str(p) for p in error.path)}" if error.path else '')
        for error in errors
    ]

    # Clean log
    logger.debug('Invalid k8s %s spec/config:\n%s', resource_name, '\n'.join(formatted))

    # Color only in CLI
    formatted_colored = [
        f'{Fore.RED}- {error.message}'
        + (f" at path: {' → '.join(str(p) for p in error.path)}" if error.path else '')
        + Style.RESET_ALL
        for error in errors
    ]

    raise ValueError(
        f'\n{Fore.RED}Invalid k8s {resource_name} spec/config: {Style.RESET_ALL}\n'
        + '\n'.join(formatted_colored)
    )


def validate_pod_spec(pod_spec: dict) -> None:
    """Validate a Kubernetes pod spec."""
    _validate_k8s_spec(pod_spec, 'podspec', 'pod')


def validate_deployment_spec(deployment_spec: dict) -> None:
    """Validate a Kubernetes deployment spec."""
    _validate_k8s_spec(deployment_spec, 'deployment', 'deployment')


def validate_service_spec(service_spec: dict) -> None:
    """Validate a Kubernetes service spec."""
    _validate_k8s_spec(service_spec, 'service', 'service')


def validate_horizontalpodautoscaler_spec(hpa_spec: dict) -> None:
    """Validate a Kubernetes HorizontalPodAutoscaler spec."""
    _validate_k8s_spec(hpa_spec, 'horizontalpodautoscaler', 'horizontalpodautoscaler')


def validate_docker_image(image_id: str) -> Tuple[str, str]:
    """Validate if a Docker image exists and is accessible.

    Args:
        image_id: The Docker image ID to validate
        (e.g., 'ubuntu:latest', 'gcr.io/project/image:tag')

    Returns:
        Tuple of (status, message) where status is:
        - 'valid': Image definitely exists
        - 'warning': Couldn't validate, but might be valid
        - 'invalid': Image definitely doesn't exist
    """
    if not image_id or not isinstance(image_id, str):
        return 'invalid', 'Image ID must be a non-empty string'

    # Basic format validation
    if not _is_valid_docker_image_format(image_id):
        return 'invalid', f'Invalid Docker image format: {image_id}'

    # Try registry API validation first (works without Docker daemon)
    registry_result = _validate_image_in_registry(image_id)
    if registry_result[0] in ['valid', 'invalid']:
        return registry_result

    # If registry validation couldn't determine, try local Docker as fallback
    if _can_pull_image_locally(image_id):
        return 'valid', f"Docker image '{image_id}' validated locally"

    # Return the registry result (warning)
    return registry_result


def _is_valid_docker_image_format(image_id: str) -> bool:
    """Check if the image ID follows valid Docker image naming conventions."""
    # Basic regex for Docker image names
    # Supports: name:tag, registry/name:tag, registry/namespace/name:tag
    pattern = (
        r'^[a-zA-Z0-9][a-zA-Z0-9._-]*'
        r'(?:\/[a-zA-Z0-9][a-zA-Z0-9._-]*)*'
        r'(?::[a-zA-Z0-9._-]+)?$'
    )
    return bool(re.match(pattern, image_id))


def _can_pull_image_locally(image_id: str) -> bool:
    """Try to inspect the image manifest locally to check if it exists."""
    try:
        # Use docker manifest inspect instead of pull for faster validation
        result = subprocess.run(
            ['docker', 'manifest', 'inspect', image_id],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        # Debug logging
        logger.debug(
            f'Local Docker manifest inspect for {image_id}: '
            f'returncode={result.returncode}, '
            f"stdout='{result.stdout}', "
            f"stderr='{result.stderr}'"
        )

        return result.returncode == 0
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.SubprocessError,
    ) as e:
        # Docker not available or timeout
        logger.debug(f'Local Docker manifest inspect failed for {image_id}: {e}')
        return False


def _validate_image_in_registry(image_id: str) -> Tuple[str, str]:
    """Validate image exists in registry using API calls."""
    try:
        registry, repo, tag = _parse_image_components(image_id)

        if registry == 'docker.io':
            return _validate_dockerhub_image(repo, tag)
        elif registry.endswith('gcr.io'):
            return _validate_gcr_image(registry, repo, tag)
        elif registry.endswith('ecr.') and '.amazonaws.com' in registry:
            return _validate_ecr_image(registry, repo, tag)
        elif registry == 'nvcr.io':
            return _validate_nvcr_image(registry, repo, tag)
        elif registry == 'ghcr.io':
            return _validate_ghcr_image(registry, repo, tag)
        elif registry == 'quay.io':
            return _validate_quay_image(registry, repo, tag)
        else:
            # For other registries, we can't easily validate without credentials
            # Return warning that we couldn't verify
            return (
                'warning',
                f"Could not validate '{image_id}' in registry {registry} "
                f'(not supported)',
            )

    except Exception as e:
        logger.debug(f'Error validating image {image_id}: {e}')
        return 'warning', f"Could not validate '{image_id}' due to validation error"


def _parse_image_components(image_id: str) -> Tuple[str, str, str]:
    """Parse image ID into registry, repository, and tag components."""
    # Default to Docker Hub
    if '/' not in image_id or '.' not in image_id.split('/')[0]:
        registry = 'docker.io'
        # For Docker Hub official images (single word), add 'library/' prefix
        if ':' in image_id:
            repo, tag = image_id.rsplit(':', 1)
        else:
            repo = image_id
            tag = 'latest'
        # Only add 'library/' prefix for single-word official images
        if '/' not in repo:
            repo = f'library/{repo}'
    else:
        parts = image_id.split('/')
        if '.' in parts[0] or parts[0] in ['localhost']:
            registry = parts[0]
            repo = '/'.join(parts[1:])
        else:
            registry = 'docker.io'
            repo = image_id

        # Split repository and tag
        if ':' in repo:
            repo, tag = repo.rsplit(':', 1)
        else:
            tag = 'latest'

    return registry, repo, tag


def _validate_dockerhub_image(repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in Docker Hub using the official API."""
    try:
        # Use Docker Hub's official API v2 endpoint
        # This endpoint checks if a specific tag exists for a repository
        url = f'https://registry.hub.docker.com/v2/repositories/{repo}/tags/{tag}'

        # Add User-Agent to avoid being blocked
        headers = {'User-Agent': 'Konduktor-Docker-Validator/1.0'}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return 'valid', f"Docker image '{repo}:{tag}' validated via Docker Hub"
        else:
            # API error, can't determine
            return ('warning', f"Could not validate '{repo}:{tag}' in Docker Hub")

    except requests.RequestException:
        # Network error, can't determine
        return (
            'warning',
            f"Could not validate '{repo}:{tag}' in Docker Hub " f'(network error)',
        )


def _validate_gcr_image(registry: str, repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in Google Container Registry."""
    try:
        # GCR manifest endpoint
        url = f'https://{registry}/v2/{repo}/manifests/{tag}'
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return 'valid', f"Docker image '{repo}:{tag}' validated via {registry}"
        else:
            # API error, can't determine
            return ('warning', f"Could not validate '{repo}:{tag}' in {registry} ")

    except requests.RequestException:
        # Network error, can't determine
        return (
            'warning',
            f"Could not validate '{repo}:{tag}' in {registry} " f'(network error)',
        )


def _validate_ecr_image(registry: str, repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in Amazon ECR."""
    # ECR requires AWS credentials and is complex to validate
    # For now, return warning that we couldn't verify
    return ('warning', f"Could not validate '{repo}:{tag}' in {registry}")


def _validate_nvcr_image(registry: str, repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in NVIDIA Container Registry."""
    # NVCR requires NVIDIA credentials and is complex to validate
    # For now, return warning that we couldn't verify
    return ('warning', f"Could not validate '{repo}:{tag}' in {registry}")


def _validate_ghcr_image(registry: str, repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in GitHub Container Registry."""
    try:
        # Check if GITHUB_TOKEN is available
        github_token = os.environ.get('GITHUB_TOKEN')

        # If not in environment, try to get from konduktor secrets
        if not github_token:
            try:
                # these imports are inside the try block to avoid circular import error
                from konduktor.backends import constants as backend_constants
                from konduktor.utils import common_utils, kubernetes_utils

                context = kubernetes_utils.get_current_kube_config_context_name()
                namespace = kubernetes_utils.get_kube_config_context_namespace(context)
                user_hash = common_utils.get_user_hash()
                label_selector = f'{backend_constants.SECRET_OWNER_LABEL}={user_hash}'
                user_secrets = kubernetes_utils.list_secrets(
                    namespace, context, label_filter=label_selector
                )

                for secret in user_secrets:
                    kind = kubernetes_utils.get_secret_kind(secret)
                    if kind == 'env' and secret.data and 'GITHUB_TOKEN' in secret.data:
                        # Decode the base64 encoded token
                        github_token = base64.b64decode(
                            secret.data['GITHUB_TOKEN']
                        ).decode()
                        logger.debug('GITHUB_TOKEN found in konduktor secret')
                        break

            except Exception as e:
                logger.debug(f'Failed to check konduktor secrets: {e}')

        if not github_token:
            return (
                'warning',
                'GITHUB_TOKEN unset, cannot verify this image. '
                'To enable validation, either:\n'
                '  1. Set GITHUB_TOKEN locally: export GITHUB_TOKEN=<token>\n'
                '  2. Create a secret: konduktor secret create --kind=env '
                '--inline GITHUB_TOKEN=<token> <name>\n'
                'See: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry',
            )

        # Base64 encode the token
        ghcr_token = base64.b64encode(github_token.encode()).decode()

        # GHCR manifest endpoint
        url = f'https://{registry}/v2/{repo}/manifests/{tag}'
        headers = {'Authorization': f'Bearer {ghcr_token}'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return 'valid', f"Docker image '{repo}:{tag}' validated via {registry}"
        else:
            # API error, can't determine
            return ('warning', f"Could not validate '{repo}:{tag}' in {registry}")

    except requests.RequestException:
        # Network error, can't determine
        return (
            'warning',
            f"Could not validate '{repo}:{tag}' in {registry} " f'(network error)',
        )


def _validate_quay_image(registry: str, repo: str, tag: str) -> Tuple[str, str]:
    """Validate image exists in Quay.io Container Registry."""
    # Quay.io requires authentication and is complex to validate
    # For now, return warning that we couldn't verify
    return ('warning', f"Could not validate '{repo}:{tag}' in {registry}")


# Track which images we've already warned about to avoid duplicate warnings
_warned_images = set()


def validate_and_warn_image(image_id: str, context: str = 'task') -> None:
    """Validate Docker image and show appropriate warnings.

    Args:
        image_id: The Docker image ID to validate
        context: Context for the validation (e.g., "task", "deployment")

    """
    if not image_id:
        return

    if _skip_image_checks():
        logger.info(
            'Skipping Docker image validation for %s',
            image_id,
        )
        return

    status, message = validate_docker_image(image_id)

    if status == 'invalid':
        # Invalid images should fail - they definitely don't exist
        raise ValueError(
            f'{message}\n'
            f'This Docker image does not exist and will cause the {context} to fail.\n'
            f"Please check that the image '{image_id}' is correct and accessible.\n"
        )
    elif status == 'warning':
        # Only warn once per image per session for warnings
        if image_id not in _warned_images:
            _warned_images.add(image_id)

            logger.warning(
                f'⚠️  Basic public image validation using Docker Daemon failed.  ⚠️\n'
                f'⚠️  {message} ⚠️\n'
                f'⚠️  The {context} will be submitted anyway, but may be stuck '
                f'PENDING forever. ⚠️\n'
                f"⚠️  Check for 'ErrImagePull' or 'ImagePullBackOff' in "
                f'kubectl get pods if issues occur. ⚠️'
            )

            # Add info about private registries
            logger.info(
                '⚠️  If pulling from a private registry, using ecr/nvcr, or not '
                'logged into Docker, this is safe to ignore. ⚠️'
            )
