"""Pod utils: handles pod spec creation and manipulation"""

import base64
import json
import os
import tempfile
import typing
from typing import Any, Dict
from urllib.parse import urlparse

import click

import konduktor
from konduktor import authentication, config, constants, logging
from konduktor.backends import constants as backend_constants
from konduktor.data import registry
from konduktor.utils import (
    common_utils,
    exceptions,
    kubernetes_utils,
    ux_utils,
    validator,
)

if typing.TYPE_CHECKING:
    pass

logger = logging.get_logger(__name__)

_RUN_DURATION_ANNOTATION_KEY = 'kueue.x-k8s.io/maxRunDurationSeconds'
# Use a large default (7 days) to mimic "infinite" runtime.
_DEFAULT_MAX_RUN_DURATION_SECONDS = 604800


def create_pod_spec(task: 'konduktor.Task') -> Dict[str, Any]:
    """Merges the task definition with config to create a final pod spec dict.

    This function is shared between JobSets and Deployments.

    Returns:
        Dict[str, Any]: k8s pod spec
    """
    context = kubernetes_utils.get_current_kube_config_context_name()
    namespace = kubernetes_utils.get_kube_config_context_namespace(context)

    # fill out the templating variables
    assert task.resources is not None, 'Task resources are required'
    num_gpus = task.resources.get_accelerator_count() or 0
    task.name = f'{task.name}-{common_utils.get_usage_run_id()[:4]}'
    node_hostnames = ','.join(
        [f'{task.name}-workers-0-{idx}.{task.name}' for idx in range(task.num_nodes)]
    )
    master_addr = f'{task.name}-workers-0-0.{task.name}'

    accelerator_type = task.resources.get_accelerator_type()

    assert task.resources.cpus is not None, 'Task resources cpus are required'
    assert task.resources.memory is not None, 'Task resources memory are required'
    assert task.resources.image_id is not None, 'Task resources image_id are required'

    # template the commands to run on the container for syncing files. At this point
    # task.stores is Dict[str, storage_utils.Storage] which is (dst, storage_obj_src)
    # first we iterate through storage_mounts and then file_mounts.
    sync_commands = []
    mkdir_commands = []
    storage_secrets = {}
    # first do storage_mount sync
    for dst, store in task.storage_mounts.items():
        # TODO(asaiacai) idk why but theres an extra storage mount for the
        # file mounts. Should be cleaned up eventually in
        # maybe_translate_local_file_mounts_and_sync_up
        assert store.source is not None and isinstance(
            store.source, str
        ), 'Store source is required'
        store_scheme = urlparse(store.source).scheme
        if '/tmp/konduktor-job-filemounts-files' in dst:
            continue
        # should impelement a method here instead of raw dog dict access
        cloud_store = registry._REGISTRY[store_scheme]
        storage_secrets[store_scheme] = cloud_store._STORE.get_k8s_credential_name()
        exists, _ = kubernetes_utils.check_secret_exists(
            storage_secrets[store_scheme], namespace=namespace, context=context
        )
        assert exists, (
            f"secret {storage_secrets[store_scheme]} doesn't "
            f'exist in namespace {namespace}'
        )
        mkdir_commands.append(
            f'cd {constants.KONDUKTOR_REMOTE_WORKDIR};' f'mkdir -p {dst}'
        )
        assert store._bucket_sub_path is not None
        sync_commands.append(
            cloud_store.make_sync_dir_command(
                os.path.join(store.source, store._bucket_sub_path), dst
            )
        )

    # then do file_mount sync.
    assert task.file_mounts is not None
    for dst, src in task.file_mounts.items():
        store_scheme = str(urlparse(store.source).scheme)
        cloud_store = registry._REGISTRY[store_scheme]
        mkdir_commands.append(
            f'cd {constants.KONDUKTOR_REMOTE_WORKDIR};'
            f'mkdir -p {os.path.dirname(dst)}'
        )
        storage_secrets[store_scheme] = cloud_store._STORE.get_k8s_credential_name()
        exists, reason = kubernetes_utils.check_secret_exists(
            storage_secrets[store_scheme], namespace=namespace, context=context
        )
        assert exists, (
            f'secret {storage_secrets[store_scheme]} '
            f"doesn't exist in namespace {namespace}"
        )
        sync_commands.append(cloud_store.make_sync_file_command(src, dst))

    tailscale_secret = config.get_nested(('tailscale', 'secret_name'), None)
    if tailscale_secret:
        secret_exist, err = kubernetes_utils.check_secret_exists(
            tailscale_secret, namespace, context
        )
        if not secret_exist:
            with ux_utils.print_exception_no_traceback():
                raise exceptions.MissingSecretError(
                    f'No tailscale auth-key secret `{tailscale_secret}` found even '
                    f'though specified by `tailscale.secret_name`: {err}'
                )

    enable_ssh = config.get_nested(('ssh', 'enable'), False) or tailscale_secret
    secret_name = None
    if enable_ssh:
        private_key_path, public_key_path = authentication.get_or_generate_keys()
        with (
            open(private_key_path, 'rb') as private_key_file,
            open(public_key_path, 'rb') as public_key_file,
        ):
            private_key, public_key = private_key_file.read(), public_key_file.read()
            user_hash = common_utils.get_user_hash()
            secret_name = f'konduktor-ssh-keys-{user_hash}'
            ok, result = kubernetes_utils.set_secret(
                secret_name=secret_name,
                namespace=namespace,
                context=context,
                data={
                    'PUBKEY': base64.b64encode(public_key).decode(),
                    'PRIVKEY': base64.b64encode(private_key).decode(),
                },
            )
            if not ok:
                raise exceptions.CreateSecretError(
                    f'Failed to set k8s secret {secret_name}: \n{result}'
                )

    # Mount the user's secrets
    git_ssh_secret_name = None
    env_secret_envs = []
    default_secrets = []
    basename_by_k8s: Dict[str, str] = {}

    # only get own secrets
    user_hash = common_utils.get_user_hash()
    label_selector = f'{backend_constants.SECRET_OWNER_LABEL}={user_hash}'
    user_secrets = kubernetes_utils.list_secrets(
        namespace, context, label_filter=label_selector
    )

    for secret in user_secrets:
        kind = kubernetes_utils.get_secret_kind(secret)

        # incase the user modified their secret to have no key:value data
        if secret.data is None:
            secret.data = {}

        # fill the map for *all* secrets we see
        k8s_name = secret.metadata.name
        lbls = secret.metadata.labels or {}
        base = lbls.get(
            backend_constants.SECRET_BASENAME_LABEL,
            # fallback: strip trailing "-<something>" once if present
            k8s_name.rsplit('-', 1)[0] if '-' in k8s_name else k8s_name,
        )
        basename_by_k8s[k8s_name] = base

        if kind == 'git-ssh' and git_ssh_secret_name is None:
            git_ssh_secret_name = secret.metadata.name
        elif kind == 'env':
            env_secret_name = secret.metadata.name
            # iterate ALL keys, not just one (ex. if user made a multi-key env secret)
            for key, _ in secret.data.items():
                # wire the env var to read its value from a k8s secret
                env_secret_envs.append(
                    {
                        'name': key,
                        'valueFrom': {
                            'secretKeyRef': {'name': env_secret_name, 'key': key}
                        },
                    }
                )
        elif kind == 'default':
            default_secret_name = secret.metadata.name
            basename = secret.metadata.labels.get(
                backend_constants.SECRET_BASENAME_LABEL, default_secret_name
            )
            default_secrets.append(
                {'k8s_name': default_secret_name, 'mount_name': basename}
            )

    # Check if the task references KONDUKTOR_DEFAULT_SECRETS and that it exists
    uses_default_secret_var = (
        'KONDUKTOR_DEFAULT_SECRETS' in (task.run or '')
        or 'KONDUKTOR_DEFAULT_SECRETS' in (task.setup or '')
        or '/konduktor/default-secrets/' in (task.run or '')
        or '/konduktor/default-secrets/' in (task.setup or '')
    )
    if uses_default_secret_var and not default_secrets:
        raise exceptions.MissingSecretError(
            f'Task references KONDUKTOR_DEFAULT_SECRETS or '
            f'/konduktor/default-secrets but '
            f'user {common_utils.get_cleaned_username()} '
            f'has no default secrets. Paths like '
            f'$KONDUKTOR_DEFAULT_SECRETS/<secret_name>/... will not exist.'
        )

    # Inject --served-model-name, --host, and --port into serving run command
    if task.serving and task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        if '--served-model-name' and '--host' and '--port' not in task.run:
            task.run = task.run.replace(
                '--model',
                (
                    f'--served-model-name {task.name} \\\n'
                    f"  --host '0.0.0.0' \\\n"
                    f"  --port '{task.serving.ports}' \\\n"
                    f'  --model'
                ),
            )
        elif '--served-model-name' in task.run:
            raise ValueError(
                'Error creating vllm deployment: '
                '--served-model-name flag should be excluded from run command'
            )
        elif '--host' in task.run:
            raise ValueError(
                'Error creating vllm deployment: '
                '--host flag should be excluded from run command'
            )
        else:
            raise ValueError(
                'Error creating vllm deployment: '
                '--port flag should be excluded from run command'
            )

    general = True
    if task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        general = False

    with tempfile.NamedTemporaryFile() as temp:
        common_utils.fill_template(
            'pod.yaml.j2',
            {
                # TODO(asaiacai) need to parse/round these numbers and sanity check
                'cpu': kubernetes_utils.parse_cpu_or_gpu_resource(
                    str(task.resources.cpus or '')
                ),
                'memory': kubernetes_utils.parse_memory_resource(
                    task.resources.memory or ''
                ),
                'image_id': task.resources.image_id,
                'num_gpus': num_gpus,
                'master_addr': master_addr,
                'num_nodes': task.num_nodes,
                'job_name': task.name,  # append timestamp and user id here?
                'setup_cmd': task.setup or '',
                'run_cmd': task.run or '',
                'node_hostnames': node_hostnames,
                'accelerator_type': accelerator_type,
                'sync_commands': sync_commands,
                'mkdir_commands': mkdir_commands,
                'mount_secrets': storage_secrets,
                'remote_workdir': constants.KONDUKTOR_REMOTE_WORKDIR,
                'user': common_utils.get_cleaned_username(),
                # Tailscale credentials
                'tailscale_secret': tailscale_secret,
                # SSH
                'enable_ssh': enable_ssh,
                'secret_name': secret_name,
                # Serving
                'serving': bool(task.serving),
                'general': general,
                'ports': task.serving.ports if task.serving else None,
                'probe': task.serving.probe if task.serving else None,
                'konduktor_ssh_port': backend_constants.KONDUKTOR_SSH_PORT,
                # Kinds of Secrets
                # --kind git-ssh
                'git_ssh': git_ssh_secret_name,
                # --kind default
                'default_secrets': default_secrets,
                # KONDUKTOR_DEBUG
                'konduktor_debug': os.getenv('KONDUKTOR_DEBUG', 0),
            },
            temp.name,
        )

        # Capture the template env names BEFORE user config is merged
        pod_config_template = common_utils.read_yaml(temp.name)
        tmpl_envs = pod_config_template['kubernetes']['pod_config']['spec'][
            'containers'
        ][0].get('env', [])
        tmpl_env_names = {e['name'] for e in tmpl_envs}

        pod_config = common_utils.read_yaml(temp.name)
        # merge with `~/.konduktor/config.yaml`` (config.yaml overrides template)
        kubernetes_utils.combine_pod_config_fields(temp.name, pod_config)
        pod_config = common_utils.read_yaml(temp.name)

    # Find what came from user config (appeared after combine, not in template)
    premerge_envs = pod_config['kubernetes']['pod_config']['spec']['containers'][0].get(
        'env', []
    )
    premerge_names = {e['name'] for e in premerge_envs}
    config_env_names0 = premerge_names - tmpl_env_names

    # Build final env list
    env_map = {env['name']: env for env in premerge_envs}

    # Inject secret envs (env secrets override config.yaml)
    for env in env_secret_envs:
        env_map[env['name']] = env

    # Inject task envs
    # CLI+task.yaml overrides everything else
    # CLI already overrode task.yaml in other code
    for k, v in task.envs.items():
        env_map[k] = {'name': k, 'value': v}

    final_envs_list = list(env_map.values())
    pod_config['kubernetes']['pod_config']['spec']['containers'][0]['env'] = (
        final_envs_list
    )
    container = pod_config['kubernetes']['pod_config']['spec']['containers'][0]
    final_envs = container['env']
    final_names = {e['name'] for e in final_envs}

    logger.debug(f'rendered pod spec: \n\t{json.dumps(pod_config, indent=2)}')

    # 1) Get secret envs actually used in the final env list
    secret_details = sorted(
        (e['name'], e['valueFrom']['secretKeyRef']['name'])
        for e in final_envs
        if isinstance(e, dict)
        and e.get('valueFrom', {})
        and e['valueFrom'].get('secretKeyRef')
    )
    secret_names = [n for n, _ in secret_details]

    # 2) Get task-sourced (CLI+task.yaml) envs actually used in the final env list
    task_all_names = sorted(
        n
        for n in (task.envs or {}).keys()
        if n in final_names and n not in secret_names
    )

    # 3) Get Config.yaml envs actually used in the final env list
    config_names = sorted(
        n
        for n in config_env_names0
        if n in final_names and n not in secret_names and n not in task_all_names
    )

    # 4) Get other envs (template/system) actually used in the final env list
    other_names = sorted(
        final_names - set(secret_names) - set(task_all_names) - set(config_names)
    )

    # Export helper envs for the startup script (names only)
    def _append_helper(name: str, values):
        container['env'].append({'name': name, 'value': ','.join(values)})

    # to show user basenames of k8s secrets instead of actual
    # k8s secret names (which have added suffixes)
    secret_map_pairs = [
        f'{var}={basename_by_k8s.get(secret_k8s, secret_k8s)}'
        for (var, secret_k8s) in secret_details
    ]

    # Priority order: CLI > task.yaml > env secret > config > template/system
    _append_helper(
        'KONDUKTOR_ENV_SECRETS_HOPEFULLY_NO_NAME_COLLISION',
        secret_names,
    )
    _append_helper(
        'KONDUKTOR_ENV_SECRETS_MAP_HOPEFULLY_NO_NAME_COLLISION',
        secret_map_pairs,
    )
    _append_helper(
        'KONDUKTOR_ENV_TASK_ALL_HOPEFULLY_NO_NAME_COLLISION',
        task_all_names,
    )
    _append_helper(
        'KONDUKTOR_ENV_CONFIG_HOPEFULLY_NO_NAME_COLLISION',
        config_names,
    )
    _append_helper(
        'KONDUKTOR_ENV_OTHER_HOPEFULLY_NO_NAME_COLLISION',
        other_names,
    )

    # validate pod spec using json schema
    try:
        validator.validate_pod_spec(pod_config['kubernetes']['pod_config']['spec'])
    except ValueError as e:
        raise click.UsageError(str(e))

    return pod_config


def inject_deployment_pod_metadata(
    pod_spec: Dict[str, Any], task: 'konduktor.Task'
) -> None:
    """Inject deployment-specific metadata into pod spec.

    This function adds deployment-specific labels, annotations, and settings
    that are not present in the basic pod spec used for JobSets.

    Args:
        pod_spec: The pod spec dictionary to modify
        task: The task object containing resource information
    """
    # Ensure metadata structure exists
    pod_spec.setdefault('metadata', {})
    pod_spec['metadata'].setdefault('labels', {})
    pod_spec['metadata'].setdefault('annotations', {})

    # Determine deployment type
    deployment_type = 'general'
    if task.run and 'vllm.entrypoints.openai.api_server' in task.run:
        deployment_type = 'vllm'

    # Add deployment-specific label for vllm deployments only
    if deployment_type == 'vllm':
        pod_spec['metadata']['labels'][backend_constants.AIBRIX_NAME_LABEL] = task.name

    # Add deployment-specific label for all deployments
    pod_spec['metadata']['labels'][backend_constants.DEPLOYMENT_NAME_LABEL] = task.name

    # Add resource labels
    if task.resources and task.resources.labels:
        pod_spec['metadata']['labels'].update(task.resources.labels)

    # Set restart policy for deployments
    pod_spec.setdefault('spec', {})
    pod_spec['spec']['restartPolicy'] = 'Always'


def merge_pod_into_deployment_template(
    deployment_spec: Dict[str, Any], pod_spec: Dict[str, Any]
) -> None:
    """Merge a pod spec into a deployment template.

    Args:
        deployment_spec: The deployment spec dictionary to modify
        pod_spec: The pod spec to merge into the deployment template
    """
    deployment_spec['template'] = pod_spec


def inject_jobset_metadata(jobset_spec: Dict[str, Any], task: 'konduktor.Task') -> None:
    """Inject JobSet-specific pod metadata.

    This function adds JobSet-specific annotations that are not present
    in the basic pod spec.

    Args:
        jobset_spec: The JobSet spec dictionary to modify
        task: The task object containing resource information
    """
    assert task.resources is not None, 'Task resources are required'
    labels = task.resources.labels or {}

    # Add max run duration annotation, defaulting to a practically infinite value.
    maxRunDurationSeconds = labels.get('maxRunDurationSeconds')
    metadata = jobset_spec['jobset']['metadata']
    metadata.setdefault('annotations', {})[_RUN_DURATION_ANNOTATION_KEY] = str(
        maxRunDurationSeconds
        if maxRunDurationSeconds is not None
        else _DEFAULT_MAX_RUN_DURATION_SECONDS
    )

    # Inject resource labels into JobSet metadata.
    if labels:
        jobset_spec['jobset']['metadata']['labels'].update(labels)


def merge_pod_into_jobset_template(
    jobset_spec: Dict[str, Any], pod_spec: Dict[str, Any]
) -> None:
    """Merge a pod spec into a JobSet template.

    Args:
        jobset_spec: The JobSet spec dictionary to modify
        pod_spec: The pod spec to merge into the JobSet template
    """
    jobset_spec['jobset']['spec']['replicatedJobs'][0]['template']['spec'][
        'template'
    ] = pod_spec
