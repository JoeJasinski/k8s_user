import os
import base64
import yaml
from .k8s.csr_resource import CSRResource
from .pki import Cert, CSRandKey, KeyBundle
from .kubeconfig import KubeConfig


class K8sUser:

    kubeconfig_klass = KubeConfig

    def __init__(
        self,
        name,
        key_dir=None,
        in_key=None,
        in_key_password=None,
        in_csr=None,
        metadata=None,
        kubeconfig_klass=None,
    ):
        self.name = name
        self.key_dir = os.path.abspath(key_dir or ".")
        self.in_key = in_key
        self.in_key_password = in_key_password
        self.in_csr = in_csr
        self.metadata = metadata if metadata else {}
        if kubeconfig_klass:
            self.kubeconfig_klass = kubeconfig_klass
        self.kubeconfig = None
        self.generate()

    def generate(self):
        self.candk = CSRandKey(
            common_name=self.name,
            key_file=self.in_key,
            key_file_password=self.in_key_password,
            csr_file=self.in_csr,
        )
        key_path = os.path.join(self.key_dir, f"{self.name}.key.pem")
        if self.key_dir and not self.in_key:
            if os.path.exists(key_path):
                raise Exception(f"Key already exists at {key_path}")
            self.candk.key.save(key_path)
        if self.key_dir and not self.in_csr:
            csr_path = os.path.join(self.key_dir, f"{self.name}.csr.pem")
            self.candk.csr.save(csr_path)

    def create(self, api_client):
        self.api_client = api_client
        self.csr = CSRResource(
            name=self.name, csr_str=self.candk.csr.base64, metadata=self.metadata
        )
        self.csr.resource_exists(api_client)
        self.csr.create(api_client)
        self.csr.approve(api_client)

        cert_str = self.csr.get_cert(api_client)
        self.crt = Cert(crt_data=base64.b64decode(cert_str))
        if self.key_dir:
            self.crt.save(os.path.join(self.key_dir, f"{self.name}.crt.pem"))

    def make_kubeconfig(self, cluster_name, context_name):
        keybundle = KeyBundle(
            user_name=self.name,
            user_key=self.candk.key.base64,
            user_csr=self.candk.key.base64,
            user_cert=self.crt.base64,
        )
        self.kubeconfig = self.kubeconfig_klass(
            self.api_client, cluster_name, context_name, keybundle,
        )
        self.kubeconfig_dict = self.kubeconfig.generate()
