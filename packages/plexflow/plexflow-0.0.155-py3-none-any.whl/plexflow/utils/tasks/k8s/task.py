import json
import os
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

class PlexflowK8sOperator(KubernetesPodOperator):
    def __init__(self, *args, **kwargs):
        self.extra_args = args
        self.extra_kwargs = kwargs.pop('extra_kwargs', {})
        
        # Define default volumes and volume mounts
        self.default_volumes = [
            k8s.V1Volume(
                name='dags-volume',
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name='ssd-sync-dags-pvc'),
            ),
            k8s.V1Volume(
                name='logs-volume',
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name='ssd-airflow-logs-pvc')
            )
        ]
        self.default_volume_mounts = [
            k8s.V1VolumeMount(
                name='dags-volume',
                mount_path='/dags',
                sub_path='dags',
            ),
            k8s.V1VolumeMount(
                name='logs-volume',
                mount_path='/opt/airflow/logs'
            )
        ]
        
        # Add default volumes and volume mounts to the operator
        if 'volumes' in kwargs:
            kwargs['volumes'].extend(self.default_volumes)
        else:
            kwargs['volumes'] = self.default_volumes
        
        if 'volume_mounts' in kwargs:
            kwargs['volume_mounts'].extend(self.default_volume_mounts)
        else:
            kwargs['volume_mounts'] = self.default_volume_mounts
        
        super().__init__(*args, **kwargs)

    def execute(self, context):
        labels = self._generate_labels(context)
        env_vars = self._convert_labels_to_env_vars(labels)
        self.env_vars.extend(env_vars)
        super().execute(context)

    def _generate_labels(self, context):
        ti = context['ti']
        labels = {
            'TASK_MODE': 'k8s',
            'AIRFLOW_DAG_ID': ti.dag_id,
            'AIRFLOW_TASK_ID': ti.task_id,
            'AIRFLOW_RUN_ID': context['run_id'],
            'AIRFLOW_TRY_NUMBER': str(ti.try_number),
            'AIRFLOW_MAX_TRIES': str(1 + ti.max_tries),
            **{key.upper(): value for key, value in os.environ.items()},
            **{f"ARG_{i:05d}": str(arg) for i, arg in enumerate(self.extra_args)},
            **{f"KW_ARG_{i:05d}": json.dumps({"key": key, "value": value}) for i, (key, value) in enumerate(self.extra_kwargs.items())},
        }
        return labels

    def _convert_labels_to_env_vars(self, labels):
        # Converts labels to Kubernetes environment variables
        return [k8s.V1EnvVar(name=k, value=v) for k, v in labels.items()]