"""Deployment utils: wraps CRUD operations for deployments"""

import json
import os
import tempfile
import typing
from typing import Any, Dict, List, Optional, Tuple

import colorama
from kubernetes.client.exceptions import ApiException
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

import konduktor
from konduktor import config as konduktor_config
from konduktor import kube_client, logging
from konduktor.backends import constants as backend_constants
from konduktor.backends import pod_utils
from konduktor.utils import (
    common_utils,
    kubernetes_utils,
    validator,
)

if typing.TYPE_CHECKING:
    pass

logger = logging.get_logger(__name__)

# Use shared constants from konduktor.backends.constants
DEPLOYMENT_NAME_LABEL = backend_constants.DEPLOYMENT_NAME_LABEL
DEPLOYMENT_USERID_LABEL = backend_constants.USERID_LABEL
DEPLOYMENT_USER_LABEL = backend_constants.USER_LABEL
DEPLOYMENT_ACCELERATOR_LABEL = backend_constants.ACCELERATOR_LABEL
DEPLOYMENT_NUM_ACCELERATORS_LABEL = backend_constants.NUM_ACCELERATORS_LABEL
AIBRIX_NAME_LABEL = backend_constants.AIBRIX_NAME_LABEL

SECRET_BASENAME_LABEL = backend_constants.SECRET_BASENAME_LABEL

_DEPLOYMENT_METADATA_LABELS = {
    'deployment_name_label': DEPLOYMENT_NAME_LABEL,
    'deployment_userid_label': DEPLOYMENT_USERID_LABEL,
    'deployment_user_label': DEPLOYMENT_USER_LABEL,
    'deployment_accelerator_label': DEPLOYMENT_ACCELERATOR_LABEL,
    'deployment_num_accelerators_label': DEPLOYMENT_NUM_ACCELERATORS_LABEL,
    'model_name_label': AIBRIX_NAME_LABEL,
}


def render_specs(
    task: 'konduktor.Task',
) -> Tuple[
    Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], Optional[Dict[str, Any]]
]:
    """Renders Kubernetes resource specifications from a Konduktor task.

    Takes a Konduktor task and generates the necessary Kubernetes resource
    specifications for deployment by filling the deployment.yaml.j2 template.
    Automatically detects deployment type (vLLM/Aibrix vs General) based on
    the task's run command.

    Args:
        task: A Konduktor Task object containing deployment configuration
              including resources, serving settings, and run commands.

    Returns:
        A tuple containing:
        - deployment_spec (Dict[str, Any]): Kubernetes Deployment specification
        - service_spec (Dict[str, Any]): Kubernetes Service specification
        - http_addon_resources (List[Dict[str, Any]]): List of HTTP add-on resources
          (HTTPScaledObject and Ingress) for general deployments; empty for vLLM
        - pa_resource (Optional[Dict[str, Any]]): PodAutoscaler specification for
          vLLM deployments with autoscaling enabled, None otherwise; empty for general

    Raises:
        ValueError: If required specs are missing after template rendering or
                   if spec validation fails.
    """
    general = True
    if task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        general = False

    # Calculate accelerator info for template
    assert task.resources is not None
    accelerator_type = task.resources.get_accelerator_type() or 'None'
    # For Deployments: GPUs per pod (not total across replicas)
    num_accelerators = task.resources.get_accelerator_count() or 0

    if task.run:
        task.run = task.run.replace('__KONDUKTOR_TASK_NAME__', task.name)
    with tempfile.NamedTemporaryFile() as temp:
        common_utils.fill_template(
            'deployment.yaml.j2',
            {
                'name': task.name,
                'user': common_utils.get_cleaned_username(),
                'accelerator_type': accelerator_type,
                'num_accelerators': str(num_accelerators),
                'min_replicas': task.serving.min_replicas if task.serving else 1,
                'max_replicas': task.serving.max_replicas if task.serving else 1,
                'ports': task.serving.ports if task.serving else 8000,
                'probe_path': (
                    task.serving.get('probe', None) if task.serving else None
                ),
                'autoscaler': (
                    'true'
                    if (
                        task.serving
                        and task.serving.min_replicas != task.serving.max_replicas
                    )
                    else 'false'
                ),
                'general': general,
                # Strip last 3 chars: backend Apoxy setup uses unique
                # suffixes (3 random numbers)to avoid Apoxy bugs when
                # deleting/creating TunnelNode resources with same names too
                # quickly, but we hide this complexity from user-facing endpoints
                'general_base_host': (
                    f'{get_unique_cluster_name_from_tunnel()[:-3]}2.trainy.us'
                )
                if general
                else None,
                **_DEPLOYMENT_METADATA_LABELS,
            },
            temp.name,
        )
        docs = common_utils.read_yaml_all(temp.name)

    deployment_spec = None
    service_spec = None
    http_addon_resources = []  # For general deployments
    pa_resource = None  # For aibrix deployments w autoscaling

    for doc in docs:
        kind = doc.get('kind')
        if kind == 'Deployment':
            deployment_spec = doc
        elif kind == 'Service':
            service_spec = doc
        # HTTPScaledObject resource for general deployments w autoscaling only
        elif kind == 'HTTPScaledObject':
            http_addon_resources.append(doc)
        # Ingress resource for all general deployments
        elif kind == 'Ingress':
            http_addon_resources.append(doc)
        # PodAutoscaler resource for aibrix deployments w autoscaling only
        elif kind == 'PodAutoscaler':
            pa_resource = doc

    if deployment_spec is None:
        raise ValueError('Deployment manifest not found.')
    if service_spec is None:
        raise ValueError('Service manifest not found.')
    if general and not http_addon_resources:
        raise ValueError('General deployment manifests not found.')
    if (
        not general
        and task.serving
        and task.serving.min_replicas != task.serving.max_replicas
        and pa_resource is None
    ):
        raise ValueError('Aibrix deployment PodAutoscaler manifest not found.')

    # Validate specs before returning
    try:
        validator.validate_deployment_spec(deployment_spec)
        validator.validate_service_spec(service_spec)
    except ValueError as e:
        raise ValueError(f'Spec validation failed: {e}')

    return deployment_spec, service_spec, http_addon_resources, pa_resource


def create_pod_autoscaler(
    namespace: str,
    task: 'konduktor.Task',
    dryrun: bool = False,
) -> None:
    """Creates Aibrix PodAutoscaler for non-general deployments."""

    # Check if this is a non-general deployment
    general = True
    if task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        general = False

    # Only create PA for aibrix deployments w autoscaling
    if general:
        return

    # Check if autoscaling is needed
    if not task.serving or task.serving.min_replicas == task.serving.max_replicas:
        logger.debug(
            f'[DEBUG] No autoscaling needed: '
            f'min={task.serving.min_replicas if task.serving else "None"}, '
            f'max={task.serving.max_replicas if task.serving else "None"}'
        )
        return  # No autoscaling needed

    logger.debug(
        f'[DEBUG] PA autoscaling enabled: '
        f'min={task.serving.min_replicas}, max={task.serving.max_replicas}'
    )

    # Get the PA spec from the rendered template
    _, _, _, pa_spec = render_specs(task)

    if not pa_spec:
        logger.warning('[DEBUG] No PodAutoscaler found in rendered template')
        return

    if dryrun:
        logger.debug(
            f'[DRYRUN] Would create PA autoscaler: '
            f'{pa_spec["metadata"].get("name", "<no-name>")}'
        )
        return

    context = kubernetes_utils.get_current_kube_config_context_name()
    custom_api = kube_client.crd_api(context=context)

    # Create KPA for aibrix deployments w autoscaling
    name = pa_spec.get('metadata', {}).get('name', '<no-name>')
    try:
        custom_api.create_namespaced_custom_object(
            group='autoscaling.aibrix.ai',
            version='v1alpha1',
            namespace=namespace,
            plural='podautoscalers',
            body=pa_spec,
        )
        logger.info(f'Pod autoscaler {name} created')
    except Exception as e:
        if '409' in str(e) or 'AlreadyExists' in str(e):
            logger.warning(f'Pod autoscaler {name} already exists, skipping')
        else:
            logger.error(f'Error creating pod autoscaler {name}: {e}')
            raise


def create_deployment(
    namespace: str,
    task: 'konduktor.Task',
    pod_spec: Dict[str, Any],
    dryrun: bool = False,
) -> Optional[Dict[str, Any]]:
    """Creates a Kubernetes Deployment based on the task and pod spec."""

    assert task.resources is not None, 'Task resources are undefined'

    deployment_spec, _, _, _ = render_specs(task)

    # Inject deployment-specific pod metadata
    pod_utils.inject_deployment_pod_metadata(pod_spec, task)

    # Inject pod spec directly (like jobset logic)
    pod_utils.merge_pod_into_deployment_template(deployment_spec['spec'], pod_spec)

    if dryrun:
        logger.debug(f'[DRYRUN] Would create deployment:\n{deployment_spec}')
        return deployment_spec

    try:
        context = kubernetes_utils.get_current_kube_config_context_name()
        apps_api = kube_client.apps_api(context=context)
        deployment = apps_api.create_namespaced_deployment(
            namespace=namespace,
            body=deployment_spec,
        )
        logger.info(
            f'Deployment {colorama.Fore.CYAN}{colorama.Style.BRIGHT}'
            f'{task.name}{colorama.Style.RESET_ALL} created'
        )

        return deployment
    except kube_client.api_exception() as err:
        try:
            error_body = json.loads(err.body)
            error_message = error_body.get('message', '')
            logger.error(f'Error creating deployment: {error_message}')
        except json.JSONDecodeError:
            logger.error(f'Error creating deployment: {err.body}')
        raise err


def create_service(
    namespace: str,
    task: 'konduktor.Task',
    dryrun: bool = False,
) -> Optional[Dict[str, Any]]:
    """Creates a Kubernetes Service based on the task and pod spec."""

    assert task.resources is not None, 'Task resources are undefined'

    _, service_spec, _, _ = render_specs(task)

    if dryrun:
        logger.debug(f'[DRYRUN] Would create service:\n{service_spec}')
        return service_spec

    try:
        context = kubernetes_utils.get_current_kube_config_context_name()
        core_api = kube_client.core_api(context=context)
        service = core_api.create_namespaced_service(
            namespace=namespace,
            body=service_spec,
        )
        logger.info(
            f'Service {colorama.Fore.CYAN}{colorama.Style.BRIGHT}'
            f'{task.name}{colorama.Style.RESET_ALL} created'
        )
        return service
    except kube_client.api_exception() as err:
        try:
            error_body = json.loads(err.body)
            error_message = error_body.get('message', '')
            logger.error(f'Error creating service: {error_message}')
        except json.JSONDecodeError:
            logger.error(f'Error creating service: {error_message}')
        raise err


def create_http_addon_resources(
    namespace: str,
    task: 'konduktor.Task',
    dryrun: bool = False,
) -> None:
    """Creates HTTP Add-on resources for general deployments."""

    # Check if this is a non-general deployment
    general = True
    if task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        general = False

    # Only create PA for aibrix deployments w autoscaling
    if not general:
        return

    _, _, http_addon_resources, _ = render_specs(task)

    if not http_addon_resources:
        logger.debug('[DEBUG] No HTTP Add-on resources to create')
        return

    if dryrun:
        logger.debug(
            f'[DRYRUN] Would create HTTP Add-on resources:\n' f'{http_addon_resources}'
        )
        return

    context = kubernetes_utils.get_current_kube_config_context_name()
    logger.debug(f'[DEBUG] Using Kubernetes context: {context}')

    for resource in http_addon_resources:
        kind = resource.get('kind')
        name = resource['metadata']['name']

        logger.debug(f'[DEBUG] Creating {kind}: {name}')

        try:
            if kind == 'HTTPScaledObject':
                # Create HTTPScaledObject (only for autoscaling)
                custom_api = kube_client.crd_api(context=context)
                custom_api.create_namespaced_custom_object(
                    group='http.keda.sh',
                    version='v1alpha1',
                    namespace=namespace,
                    plural='httpscaledobjects',
                    body=resource,
                )
                logger.info(f'HTTPScaledObject {name} created')

            elif kind == 'Ingress':
                # Create Ingress (always needed for external access)
                networking_api = kube_client.networking_api(context=context)
                networking_api.create_namespaced_ingress(
                    namespace=namespace,
                    body=resource,
                )
                logger.info(f'Ingress {name} created')

        except Exception as e:
            if '409' in str(e) or 'AlreadyExists' in str(e):
                logger.warning(
                    f'HTTP Add-on resource {kind} {name} already exists, skipping'
                )
            else:
                logger.error(f'Error creating HTTP Add-on resource {kind} {name}: {e}')
                raise


def list_models(namespace: str) -> List[str]:
    """
    Returns a list of unique model names in the namespace,
    based on label DEPLOYMENT_NAME_LABEL=`trainy.ai/deployment-name`.
    """
    context = kubernetes_utils.get_current_kube_config_context_name()
    apps = kube_client.apps_api(context)
    core = kube_client.core_api(context)
    crds = kube_client.crd_client(context)

    label_selector = DEPLOYMENT_NAME_LABEL
    model_names: set[str] = set()

    # Deployments
    for deploy in apps.list_namespaced_deployment(
        namespace, label_selector=label_selector
    ).items:
        labels = getattr(deploy.metadata, 'labels', {}) or {}
        name = labels.get(DEPLOYMENT_NAME_LABEL)
        if name:
            model_names.add(name)

    # Services
    for svc in core.list_namespaced_service(
        namespace, label_selector=label_selector
    ).items:
        labels = getattr(svc.metadata, 'labels', {}) or {}
        name = labels.get(DEPLOYMENT_NAME_LABEL)
        if name:
            model_names.add(name)

    # Podautoscalers (KPA only)
    try:
        pa_list = crds.list_namespaced_custom_object(
            group='autoscaling.aibrix.ai',
            version='v1alpha1',
            namespace=namespace,
            plural='podautoscalers',
        )
        for pa in pa_list.get('items', []):
            labels = pa.get('metadata', {}).get('labels', {})
            name = labels.get(DEPLOYMENT_NAME_LABEL)
            if name:
                model_names.add(name)
    except ApiException as e:
        if e.status != 404:
            # re-raise if it's not just missing CRD
            raise
        # otherwise ignore, cluster just doesn't have Aibrix CRDs
        logger.warning('Skipping PA lookup. Aibrix CRDs not found in cluster')

    # HPA
    autoscaling_api = kube_client.autoscaling_api(context=context)
    hpa_list = autoscaling_api.list_namespaced_horizontal_pod_autoscaler(
        namespace=namespace
    )
    for hpa in hpa_list.items:
        labels = getattr(hpa.metadata, 'labels', {}) or {}
        name = labels.get(DEPLOYMENT_NAME_LABEL)
        if name:
            model_names.add(name)

    return sorted(model_names)


def get_autoscaler_status_for_deployment(
    name: str, autoscalers_map: dict, is_general: bool
) -> bool:
    """Return autoscaler readiness by deployment type.

    - General: returns hpa_ready
    - vLLM/Aibrix: returns kpa_ready
    """

    def _is_ready(obj: dict) -> bool:
        try:
            conditions = obj.get('status', {}).get('conditions') or []
            kind = obj.get('kind') or ''

            for cond in conditions:
                if cond.get('type') == 'AbleToScale' and cond.get('status') == 'True':
                    return True

            if kind == 'HorizontalPodAutoscaler':
                # Check for ScalingActive condition
                for cond in conditions:
                    if cond.get('type') == 'ScalingActive':
                        # ScalingActive: True means actively scaling
                        if cond.get('status') == 'True':
                            return True
                        # ScalingActive: False with ScalingDisabled reason
                        # is normal for scale-to-zero
                        if (
                            cond.get('status') == 'False'
                            and cond.get('reason') == 'ScalingDisabled'
                        ):
                            return True

                # Treat existing HPA with no conditions as ready
                return not conditions or any(
                    c.get('type') == 'AbleToScale' and c.get('status') == 'True'
                    for c in conditions
                )
        except Exception as e:
            logger.warning(f'Error checking autoscaler readiness: {e}')
        return False

    kpa_ready = False
    hpa_ready = False

    dep_autos = autoscalers_map.get(name, {})

    if is_general:
        if 'hpa' in dep_autos:
            hpa_ready = _is_ready(dep_autos['hpa'])
            return hpa_ready
        return False

    if 'kpa' in dep_autos:
        kpa_ready = _is_ready(dep_autos['kpa'])
        return kpa_ready
    return False


def _extract_min_max_from_autoscaler(autoscaler: dict) -> tuple[str, str]:
    """Extract min/max replicas across PA/HPA/KEDA.

    Returns (min_str, max_str). Unknowns as '?'.
    """
    try:
        if not autoscaler:
            return '?', '?'

        spec = autoscaler.get('spec', {})

        # Check for HTTPScaledObject format (replicas.min/max)
        if 'replicas' in spec:
            replicas = spec.get('replicas', {})
            if 'min' in replicas or 'max' in replicas:
                return (str(replicas.get('min', '?')), str(replicas.get('max', '?')))

        # Check for KEDA ScaledObject format (minReplicaCount/maxReplicaCount)
        if 'minReplicaCount' in spec or 'maxReplicaCount' in spec:
            return (
                str(spec.get('minReplicaCount', '?')),
                str(spec.get('maxReplicaCount', '?')),
            )

        # Check for PA/HPA format (minReplicas/maxReplicas)
        if 'minReplicas' in spec or 'maxReplicas' in spec:
            return str(spec.get('minReplicas', '?')), str(spec.get('maxReplicas', '?'))
    except Exception:
        pass
    return '?', '?'


def build_autoscaler_map(namespace: str, context: str) -> dict[str, dict]:
    """Fetch autoscalers and return a simple map keyed by deployment name.

    Simplified model:
    - Aibrix deployments: 1 PodAutoscaler (KPA) if autoscaling enabled
    - General deployments: 1 HPA (created by KEDA) if autoscaling enabled
    - No autoscaling: No autoscaler

    Returns: {deployment_name: {'kpa': pa_obj} or {'hpa': hpa_obj}}
    """
    autoscalers: Dict[str, Dict[str, Any]] = {}

    # --- Aibrix deployment KPA ---
    try:
        crd_api = kube_client.crd_api(context=context)
        pa_list = crd_api.list_namespaced_custom_object(
            group='autoscaling.aibrix.ai',
            version='v1alpha1',
            namespace=namespace,
            plural='podautoscalers',
        )
        for pa in pa_list.get('items', []):
            labels = pa.get('metadata', {}).get('labels', {})
            dep_name = labels.get(DEPLOYMENT_NAME_LABEL)
            if not dep_name:
                # Fallback to scaleTargetRef.name
                spec = pa.get('spec', {})
                scale_ref = spec.get('scaleTargetRef', {})
                dep_name = scale_ref.get('name')
            if dep_name:
                autoscalers[dep_name] = {'kpa': pa}
        if pa_list.get('items'):
            logger.debug(f"Found {len(pa_list.get('items', []))} PodAutoscalers")
    except Exception as e:
        logger.warning(f'Error fetching PodAutoscalers: {e}')

    # --- General deployment HPA ---
    try:
        autoscaling_api = kube_client.autoscaling_api(context=context)
        hpa_list = autoscaling_api.list_namespaced_horizontal_pod_autoscaler(
            namespace=namespace
        )
        for hpa in hpa_list.items:
            labels = getattr(hpa.metadata, 'labels', {}) or {}
            dep_name = labels.get(DEPLOYMENT_NAME_LABEL)
            if not dep_name:
                # Fallback to scaleTargetRef.name
                spec = hpa.spec.to_dict() if hpa.spec else {}
                scale_ref = spec.get('scale_target_ref', {})
                dep_name = scale_ref.get('name')
            if dep_name:
                hpa_dict = hpa.to_dict()
                hpa_dict['kind'] = 'HorizontalPodAutoscaler'
                hpa_dict['apiVersion'] = 'autoscaling/v2'
                autoscalers[dep_name] = {'hpa': hpa_dict}
        if hpa_list.items:
            logger.debug(f'Found {len(hpa_list.items)} HPAs')
    except Exception as e:
        logger.warning(f'Error fetching HPAs: {e}')

    return autoscalers


def get_model_status(
    name: str,
    deployments: dict[str, Any],
    services: dict[str, Any],
    autoscalers: dict[str, dict],
) -> Dict[str, Optional[str]]:
    """Check the status of Deployment, Service, and Autoscaler."""
    status = {
        'deployment': 'missing',
        'service': 'missing',
        'autoscaler': None,
    }

    # --- Deployment ---
    if name in deployments:
        d = deployments[name]
        ready = (d.status.ready_replicas or 0) if d.status else 0
        desired = (d.spec.replicas or 0) if d.spec else 0

        labels = d.metadata.labels or {}
        is_aibrix = AIBRIX_NAME_LABEL in labels

        if is_aibrix and name in autoscalers:
            # For Aibrix deployments, get the original min replicas from
            # deployment labels
            original_min_replicas = 0
            original_min_str = labels.get('trainy.ai/original-min-replicas')
            if original_min_str:
                try:
                    original_min_replicas = int(original_min_str)
                except (ValueError, TypeError):
                    pass

            # For Aibrix deployments, consider ready if:
            # 1. Ready replicas >= original minimum replicas, OR
            # 2. If original_min_replicas is 0 (scale-to-zero allowed),
            #    then ready == desired
            if original_min_replicas == 0:
                status['deployment'] = 'ready' if ready == desired else 'pending'
            else:
                status['deployment'] = (
                    'ready' if ready >= original_min_replicas else 'pending'
                )
        else:
            # General deployments or no autoscaler: use simple ready == desired check
            status['deployment'] = 'ready' if ready == desired else 'pending'

    # --- Service ---
    if name in services:
        status['service'] = 'ready'
    else:
        status['service'] = 'missing'

    # --- Autoscaler ---
    if name in autoscalers:
        # Check if this is a general deployment (not vLLM/Aibrix)
        is_general = True
        if deployments.get(name) and hasattr(deployments[name].metadata, 'labels'):
            labels = deployments[name].metadata.labels or {}
            if AIBRIX_NAME_LABEL in labels:
                is_general = False

        # Check actual autoscaler readiness
        autoscaler_ready = get_autoscaler_status_for_deployment(
            name, autoscalers, is_general
        )
        status['autoscaler'] = 'ready' if autoscaler_ready else 'pending'
    else:
        status['autoscaler'] = None

    return status


def get_deployment(namespace: str, job_name: str) -> Optional[Any]:
    context = kubernetes_utils.get_current_kube_config_context_name()
    apps_api = kube_client.apps_api(context=context)
    try:
        return apps_api.read_namespaced_deployment(name=job_name, namespace=namespace)
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def get_service(namespace: str, job_name: str) -> Optional[Any]:
    context = kubernetes_utils.get_current_kube_config_context_name()
    core_api = kube_client.core_api(context=context)
    try:
        return core_api.read_namespaced_service(name=job_name, namespace=namespace)
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def get_autoscaler(namespace: str, job_name: str) -> Optional[Any]:
    context = kubernetes_utils.get_current_kube_config_context_name()
    # --- Try Aibrix PA first ---
    crd_api = kube_client.crd_api(context=context)
    try:
        return crd_api.get_namespaced_custom_object(
            group='autoscaling.aibrix.ai',
            version='v1alpha1',
            namespace=namespace,
            plural='podautoscalers',
            name=f'{job_name}-pa',
        )
    except ApiException as e:
        if e.status != 404:
            raise
        # Fall through to check HPA

    # --- Try built‑in Kubernetes HPA ---
    try:
        autoscaling_api = kube_client.autoscaling_api(context=context)
        return autoscaling_api.read_namespaced_horizontal_pod_autoscaler(
            name=f'{job_name}-hpa', namespace=namespace
        ).to_dict()
    except ApiException as e:
        if e.status != 404:
            raise

    # --- Try KEDA ScaledObject ---
    try:
        return crd_api.get_namespaced_custom_object(
            group='keda.sh',
            version='v1alpha1',
            namespace=namespace,
            plural='scaledobjects',
            name=f'{job_name}-keda',
        )
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def delete_deployment(namespace: str, name: str) -> Optional[Dict[str, Any]]:
    """Deletes a Kubernetes Deployment in the given namespace.

    Args:
        namespace: Namespace where the deployment exists.
        name: Name of the deployment to delete.

    Returns:
        Response from delete operation, or None on error.
    """
    try:
        context = kubernetes_utils.get_current_kube_config_context_name()
        response = kube_client.apps_api(context=context).delete_namespaced_deployment(
            name=name,
            namespace=namespace,
        )
        return response
    except kube_client.api_exception() as err:
        try:
            error_body = json.loads(err.body)
            error_message = error_body.get('message', '')
            logger.error(f'Error deleting deployment: {error_message}')
        except json.JSONDecodeError:
            error_message = str(err.body)
            logger.error(f'Error deleting deployment: {error_message}')
        else:
            raise err
    return None


def delete_service(namespace: str, name: str) -> Optional[Dict[str, Any]]:
    """Deletes a Kubernetes Service in the given namespace.

    Args:
        namespace: Namespace where the service exists.
        name: Name of the service to delete.

    Returns:
        Response from delete operation, or None on error.
    """
    try:
        context = kubernetes_utils.get_current_kube_config_context_name()
        response = kube_client.core_api(context=context).delete_namespaced_service(
            name=name,
            namespace=namespace,
        )
        return response
    except kube_client.api_exception() as err:
        try:
            error_body = json.loads(err.body)
            error_message = error_body.get('message', '')
            logger.error(f'Error deleting service: {error_message}')
        except json.JSONDecodeError:
            logger.error(f'Error deleting service: {err.body}')
        raise err
    return None


def delete_autoscaler(namespace: str, name: str) -> Optional[Dict[str, Any]]:
    """Delete all autoscalers associated with a deployment name.

    This includes:
    - All Aibrix PodAutoscalers (e.g., "-pa", "-apa") targeting the deployment
    - Any HorizontalPodAutoscaler named "<name>-hpa"
    - Any KEDA ScaledObject named "<name>-keda"
    """
    context = kubernetes_utils.get_current_kube_config_context_name()

    # --- Delete ALL PodAutoscalers that target this deployment ---
    try:
        custom_api = kube_client.crd_api(context=context)
        pa_list = custom_api.list_namespaced_custom_object(
            group='autoscaling.aibrix.ai',
            version='v1alpha1',
            namespace=namespace,
            plural='podautoscalers',
        )
        for pa in pa_list.get('items', []):
            meta = pa.get('metadata', {})
            spec = pa.get('spec', {})
            pa_name = meta.get('name', '')
            labels = meta.get('labels', {})
            scale_ref = spec.get('scaleTargetRef', {}).get('name')
            targets_deployment = (
                labels.get(DEPLOYMENT_NAME_LABEL) == name
                or scale_ref == name
                or pa_name.startswith(f'{name}-')
            )
            if targets_deployment:
                try:
                    custom_api.delete_namespaced_custom_object(
                        group='autoscaling.aibrix.ai',
                        version='v1alpha1',
                        namespace=namespace,
                        plural='podautoscalers',
                        name=pa_name,
                    )
                    logger.info(f'Deleted PodAutoscaler: {pa_name}')
                except kube_client.api_exception() as err:
                    if getattr(err, 'status', None) != 404:
                        raise
    except kube_client.api_exception() as err:
        # If PA CRD is missing, skip; otherwise bubble up
        if getattr(err, 'status', None) not in (404, None):
            raise

    # --- Delete HPA ---
    try:
        autoscaling_api = kube_client.autoscaling_api(context=context)
        autoscaling_api.delete_namespaced_horizontal_pod_autoscaler(
            name=f'{name}-hpa',
            namespace=namespace,
        )
        logger.info(f'Deleted HPA: {name}-hpa')
    except kube_client.api_exception() as err:
        if getattr(err, 'status', None) not in (404, None):
            try:
                error_body = json.loads(err.body)
                error_message = error_body.get('message', '')
                logger.error(f'Error deleting HPA: {error_message}')
            except json.JSONDecodeError:
                logger.error(f'Error deleting HPA: {err.body}')
            raise err

    # --- Delete KEDA ScaledObject ---
    try:
        custom_api = kube_client.crd_api(context=context)
        custom_api.delete_namespaced_custom_object(
            group='keda.sh',
            version='v1alpha1',
            namespace=namespace,
            plural='scaledobjects',
            name=f'{name}-keda',
        )
        logger.info(f'Deleted ScaledObject: {name}-keda')
    except kube_client.api_exception() as err:
        if getattr(err, 'status', None) not in (404, None):
            try:
                error_body = json.loads(err.body)
                error_message = error_body.get('message', '')
                logger.error(f'Error deleting KEDA ScaledObject: {error_message}')
            except json.JSONDecodeError:
                logger.error(f'Error deleting KEDA ScaledObject: {err.body}')
            raise err

    return None


def delete_http_addon_resources(name: str, namespace: str) -> None:
    """Deletes HTTP Add-on resources for general deployments."""
    context = kubernetes_utils.get_current_kube_config_context_name()

    # Delete HTTPScaledObject
    try:
        custom_api = kube_client.crd_api(context=context)
        custom_api.delete_namespaced_custom_object(
            group='http.keda.sh',
            version='v1alpha1',
            namespace=namespace,
            plural='httpscaledobjects',
            name=f'{name}-httpscaledobject',
        )
        logger.info(f'Deleted HTTPScaledObject: {name}-httpscaledobject')
    except kube_client.api_exception() as err:
        if err.status != 404:
            logger.debug(
                f'Failed to delete HTTPScaledObject {name}-httpscaledobject: {err}'
            )

    # Delete Ingress
    try:
        networking_api = kube_client.networking_api(context=context)
        networking_api.delete_namespaced_ingress(
            name=f'{name}-ingress',
            namespace=namespace,
        )
        logger.info(f'Deleted Ingress: {name}-ingress')
    except kube_client.api_exception() as err:
        if err.status != 404:
            logger.debug(f'Failed to delete Ingress {name}-ingress: {err}')


def delete_serving_specs(name: str, namespace: str) -> None:
    for kind, delete_fn in [
        ('deployment', delete_deployment),
        ('service', delete_service),
    ]:
        try:
            delete_fn(namespace, name)
            logger.info(f'Deleted {kind}: {name}')
        except Exception as e:
            logger.debug(f'Failed to delete {kind} {name}: {e}')

    # Delete autoscaler resources (Aibrix PA, HPA, or KEDA ScaledObject)
    try:
        delete_autoscaler(namespace=namespace, name=name)
    except Exception as e:
        logger.debug(f'Failed to delete autoscaler for {name}: {e}')

    # Delete HTTP Add-on resources for general deployments
    delete_http_addon_resources(name, namespace)


def _get_resource_summary(deployment) -> str:
    """Extract and format pod resource information from a deployment.

    Args:
        deployment: Kubernetes deployment object

    Returns:
        Formatted string with resource information (GPU, CPU, memory)
    """
    if not deployment:
        return '?'

    try:
        containers = deployment.spec.template.spec.containers
        if not containers:
            return '?'
        container = containers[0]
        res = container.resources.requests or {}

        cpu = res.get('cpu', '?')
        mem = res.get('memory', '?')
        gpu = res.get('nvidia.com/gpu') or res.get('trainy.ai/gpu')

        # Try to extract GPU type from deployment labels
        labels = deployment.metadata.labels or {}
        accelerator_type = labels.get('trainy.ai/accelerator', 'L4O')

        gpu_str = f'{accelerator_type}:{gpu}' if gpu else 'None'
        return f'{gpu_str}\n{cpu} CPU\n{mem}'
    except Exception:
        return '?'


def get_envoy_external_ip() -> Optional[str]:
    context = kubernetes_utils.get_current_kube_config_context_name()
    core_api = kube_client.core_api(context=context)
    try:
        services = core_api.list_namespaced_service(namespace='envoy-gateway-system')
        for svc in services.items:
            if svc.spec.type == 'LoadBalancer' and 'envoy' in svc.metadata.name:
                ingress = svc.status.load_balancer.ingress
                if ingress:
                    return ingress[0].ip or ingress[0].hostname
    except Exception:
        pass
    return None


def get_ingress_nginx_external_ip() -> Optional[str]:
    """Get the external IP of the keda-ingress-nginx-controller LoadBalancer."""
    context = kubernetes_utils.get_current_kube_config_context_name()
    core_api = kube_client.core_api(context=context)
    try:
        # Look for keda-ingress-nginx-controller service in keda namespace
        service = core_api.read_namespaced_service(
            name='keda-ingress-nginx-controller', namespace='keda'
        )
        if service.spec.type == 'LoadBalancer':
            ingress = service.status.load_balancer.ingress
            if ingress:
                return ingress[0].ip or ingress[0].hostname
    except Exception:
        pass
    return None


def get_unique_cluster_name_from_tunnel() -> str:
    """Get cluster name from the apoxy deployment command."""
    try:
        context = kubernetes_utils.get_current_kube_config_context_name()
        apps_api = kube_client.apps_api(context=context)

        # Get the apoxy deployment
        deployment = apps_api.read_namespaced_deployment(
            name='apoxy', namespace='apoxy-system'
        )

        # Extract cluster name from the command
        containers = deployment.spec.template.spec.containers
        if containers and len(containers) > 0:
            command = containers[0].command
            if (
                command
                and len(command) >= 4
                and command[1] == 'tunnel'
                and command[2] == 'run'
            ):
                return command[3]  # The cluster name is the 4th argument

        logger.warning('Could not extract cluster name from apoxy deployment command')

    except Exception as e:
        logger.warning(f'Error getting cluster name from apoxy deployment: {e}')

    return 'default'


def get_endpoint_type_from_config() -> str:
    """Get the endpoint type from konduktor config.

    Returns:
        'trainy' for Apoxy endpoints (default)
        'direct' for LoadBalancer IP endpoints
    """
    try:
        # Use the proper config system that handles KONDUKTOR_CONFIG env var
        endpoint_type = konduktor_config.get_nested(('serving', 'endpoint'), 'trainy')
        logger.debug(f'[DEBUG] Config endpoint_type: {endpoint_type}')
        return endpoint_type.lower()
    except Exception as e:
        logger.warning(f'Error reading endpoint config: {e}')

    # Default to trainy if config not found or error
    logger.debug('[DEBUG] Falling back to default endpoint type: trainy')
    return 'trainy'


def get_deployment_endpoint(
    force_direct: bool = False, deployment_type: str = 'AIBRIX'
) -> str:
    """Get the endpoint for both vLLM/Aibrix and general deployments."""
    if force_direct:
        endpoint_type = 'direct'
    else:
        endpoint_type = get_endpoint_type_from_config()

    if endpoint_type == 'direct':
        # Check if this is a general deployment
        if deployment_type == 'GENERAL':
            # General deployments: ingress IP + Host header
            ingress_ip = get_ingress_nginx_external_ip()
            if ingress_ip:
                return f'{ingress_ip}'
            else:
                return '<pending>'
        else:
            # vLLM/Aibrix deployments: envoy IP
            try:
                aibrix_endpoint = get_envoy_external_ip()
                return aibrix_endpoint or '<pending>'
            except Exception:
                return '<pending>'
    else:
        # Use Apoxy (trainy.us)
        try:
            cluster_name = get_unique_cluster_name_from_tunnel()
            if deployment_type == 'GENERAL':
                # Strip last 3 chars: backend Apoxy setup uses unique
                # suffixes (3 random numbers)to avoid Apoxy bugs when
                # deleting/creating TunnelNode resources with same names too
                # quickly, but we hide this complexity from user-facing endpoints
                return f'{cluster_name[:-3]}2.trainy.us'  # General deployments
            else:
                # Strip last 3 chars: backend Apoxy setup uses unique
                # suffixes (3 random numbers)to avoid Apoxy bugs when
                # deleting/creating TunnelNode resources with same names too
                # quickly, but we hide this complexity from user-facing endpoints
                return f'{cluster_name[:-3]}.trainy.us'  # vLLM deployments
        except Exception:
            return '<pending>'


def show_status_table(namespace: str, all_users: bool, force_direct: bool = False):
    """Display status of Konduktor Serve models."""
    context = kubernetes_utils.get_current_kube_config_context_name()

    # Build lookup maps (deployment_name -> object)
    apps_api = kube_client.apps_api(context)
    core_api = kube_client.core_api(context)

    deployments_map = {}
    for d in apps_api.list_namespaced_deployment(namespace=namespace).items:
        name = (d.metadata.labels or {}).get(DEPLOYMENT_NAME_LABEL)
        if name is not None:
            deployments_map[name] = d

    services_map = {}
    for s in core_api.list_namespaced_service(namespace=namespace).items:
        name = (s.metadata.labels or {}).get(DEPLOYMENT_NAME_LABEL)
        if name is not None:
            services_map[name] = s

    autoscalers_map = build_autoscaler_map(namespace, context or '')

    model_names = list_models(namespace)
    if not model_names:
        Console().print(
            f'[yellow]No deployments found in namespace {namespace}.[/yellow]'
        )
        return

    Console().print()
    title = '[bold]KONDUKTOR SERVE[/bold]'
    is_ci = os.environ.get('CI') or os.environ.get('BUILDKITE')

    # Get Aibrix endpoint once for all Aibrix deployments
    aibrix_endpoint = get_deployment_endpoint(force_direct, 'AIBRIX')
    # Get General endpoint once for all General deployments
    general_endpoint = get_deployment_endpoint(force_direct, 'GENERAL')

    table = Table(title=title, box=box.ASCII if is_ci else box.ROUNDED)
    if all_users:
        table.add_column('User', style='magenta', no_wrap=True)
    table.add_column('Name', style='cyan', no_wrap=True)
    table.add_column('Status', no_wrap=True)
    table.add_column('Summary', style='bold', no_wrap=True)
    table.add_column('Endpoint', style='yellow', no_wrap=True)
    table.add_column('Replicas', style='dim', no_wrap=True)
    table.add_column('Resources', style='white', no_wrap=True)

    unowned = 0

    for idx, name in enumerate(model_names):
        deployment = deployments_map.get(name)
        service = services_map.get(name)
        autoscaler = autoscalers_map.get(name)

        # Extract owner
        owner = None
        for resource in [deployment, service, autoscaler]:
            if not resource:
                continue
            metadata = (
                resource.metadata
                if hasattr(resource, 'metadata')
                else resource.get('metadata', {})
            )
            labels = (
                metadata.labels
                if hasattr(metadata, 'labels')
                else metadata.get('labels', {})
            )
            if labels:
                owner = labels.get('trainy.ai/username')
            if owner:
                break

        if not all_users and owner != common_utils.get_cleaned_username():
            unowned += 1
            continue

        # Status
        status = get_model_status(name, deployments_map, services_map, autoscalers_map)
        states = [status['deployment'], status['service'], status['autoscaler']]

        def emoji_line(label: str, state: str) -> str:
            emoji_map = {
                'ready': '✅',
                'pending': '❓',
                'missing': '❌',
            }
            return f"{label}: {emoji_map.get(state, '❓')}"

        # Check if this is a general deployment (not vLLM/Aibrix)
        is_general = True
        if deployment and hasattr(deployment.metadata, 'labels'):
            labels = deployment.metadata.labels or {}
            if AIBRIX_NAME_LABEL in labels:
                is_general = False

        summary_lines = [
            emoji_line('Deploym', status['deployment'] or 'missing'),
            emoji_line('Service', status['service'] or 'missing'),
        ]

        if is_general:
            # Autoscaler for General: HPA only
            hpa_ready = get_autoscaler_status_for_deployment(
                name, autoscalers_map, is_general=True
            )
            if name in autoscalers_map:
                summary_lines.append(f"AScaler: {'✅' if hpa_ready else '❓'}")
        else:
            # Autoscaler for vLLM: only KPA (APA no longer used)
            if name in autoscalers_map:
                kpa_ready = get_autoscaler_status_for_deployment(
                    name, autoscalers_map, is_general=False
                )
                if 'kpa' in autoscalers_map.get(name, {}):
                    summary_lines.append(f"AScaler: {'✅' if kpa_ready else '❓'}")
        summary = '\n'.join(summary_lines)

        # Overall status
        if any(s == 'missing' for s in states):
            status_text = Text('FAILED', style='red')
        else:
            if status['autoscaler'] is not None:
                status_text = (
                    Text('READY', style='green')
                    if all(s == 'ready' for s in states)
                    else Text('PENDING', style='yellow')
                )
            else:
                status_text = (
                    Text('READY', style='green')
                    if (
                        status['deployment'] == 'ready' and status['service'] == 'ready'
                    )
                    else Text('PENDING', style='yellow')
                )

        # Extract labels from deployment, service, or fallback to empty dict
        labels = {}
        if deployment and hasattr(deployment.metadata, 'labels'):
            labels = deployment.metadata.labels or {}
        elif service and hasattr(service.metadata, 'labels'):
            labels = service.metadata.labels or {}
        else:
            labels = {}

        endpoint_str = '<pending>'
        if AIBRIX_NAME_LABEL in labels:
            # Aibrix deployment
            endpoint_type = get_endpoint_type_from_config()
            if force_direct or endpoint_type == 'direct':
                # Direct access: use http for IP endpoints
                endpoint_str = (
                    f'http://{aibrix_endpoint}'
                    if aibrix_endpoint != '<pending>'
                    else aibrix_endpoint
                )
            else:
                # Apoxy access: use https for trainy.us endpoints
                endpoint_str = (
                    f'https://{aibrix_endpoint}'
                    if aibrix_endpoint != '<pending>'
                    else aibrix_endpoint
                )
        else:
            # General deployment
            endpoint_type = get_endpoint_type_from_config()
            if force_direct or endpoint_type == 'direct':
                # Direct access: IP + Host header
                endpoint_str = f'http://{general_endpoint}\nHost: {name}'
            else:
                # Apoxy access: single host + path
                endpoint_str = f'https://{general_endpoint}/{name}'

        # Replicas
        if deployment:
            ready_replicas = str(deployment.status.ready_replicas or 0)
            desired_replicas = str(deployment.spec.replicas or 0)
        else:
            ready_replicas = '?'
            desired_replicas = '?'

        replicas_text = Text()
        replicas_text.append(
            f'Ready: {ready_replicas}/{desired_replicas}\n', style='bold white'
        )

        if status['autoscaler']:
            # Get min/max from deployment labels
            min_r, max_r = '?', '?'

            if deployment and hasattr(deployment.metadata, 'labels'):
                labels = deployment.metadata.labels or {}
                # All deployments with autoscaling get these labels from the template
                original_min_str = labels.get('trainy.ai/original-min-replicas')
                original_max_str = labels.get('trainy.ai/original-max-replicas')
                if original_min_str and original_max_str:
                    min_r, max_r = original_min_str, original_max_str
                    logger.debug(
                        f'[DEBUG] Got replicas from deployment labels: '
                        f'min={min_r}, max={max_r}'
                    )

            replicas_text.append(f'Min  : {min_r}\n', style='bold white')
            replicas_text.append(f'Max  : {max_r}', style='bold white')

        # Resources
        resources_text = _get_resource_summary(deployment)

        # Row
        if all_users:
            table.add_row(
                owner or '(unknown)',
                name,
                status_text,
                summary,
                endpoint_str,
                replicas_text,
                resources_text,
            )
        else:
            table.add_row(
                name, status_text, summary, endpoint_str, replicas_text, resources_text
            )

        if idx != len(model_names) - 1:
            table.add_row(*([''] * len(table.columns)))

    if len(model_names) == unowned:
        Console().print(
            f'[yellow]No deployments created by you found '
            f'in namespace {namespace}. Try --all-users.[/yellow]'
        )
        return

    Console().print(table)
