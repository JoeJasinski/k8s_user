import os
import base64
import collections
import yaml
from .k8s.csr_resource import CSRResource
from .pki import Cert, CSRandKey, KeyBundle
from .kubeconfig import KubeConfig
from .csr_workflow import UserCSRWorkflow


class K8sUser:

    kubeconfig_klass = KubeConfig

    def __init__(
        self,
        name,
        creds_dir=None,
        in_key=None,
        in_key_password=None,
        in_csr=None,
        metadata=None,
        kubeconfig_klass=None,
    ):
        self.name = name
        self.creds_dir = os.path.abspath(creds_dir or ".")
        self.in_key = in_key
        self.in_key_password = in_key_password
        self.in_csr = in_csr
        self.metadata = metadata if metadata else {}
        if kubeconfig_klass:
            self.kubeconfig_klass = kubeconfig_klass
        self.kubeconfig = None

    def create(self, api_client, inputs):
        self.api_client = api_client

        UserCSRWorkflow(
            start_step='get_csr_and_key',
            inputs={**dict(
                api_client=api_client,
                user=self,
            ), **inputs},
        ).start()
