import os
import base64
import yaml
from .k8s.csr_resource import CSRResource
from .pki import Cert, CSRandKey
from .config_gen import ClusterConfigGen, UserConfigGen, ContainerConfigGen

class K8sUser:
    def __init__(self, name, key_dir=None, metadata=None):
        self.name = name
        self.key_dir = os.path.abspath(key_dir)
        self.metadata = metadata if metadata else {}
        self._generate()

    def _generate(self):
        self.candk = CSRandKey(common_name=self.name)
        key_path = os.path.join(self.key_dir, f"{self.name}.key.pem")
        if self.key_dir:
            if os.path.exists(key_path):
                raise Exception(f"Key already exists at {key_path}")
            self.candk.key.save(key_path)
            csr_path = os.path.join(self.key_dir, f"{self.name}.csr.pem")
            self.candk.csr.save(csr_path)

    def create(self, api_client):
        self.api_client = api_client
        self.csr = CSRResource(
            name=self.name,
            csr_str=self.candk.csr.base64,
            metadata=self.metadata)
        self.csr.resource_exists(api_client)
        self.csr.create(api_client)
        self.csr.approve(api_client)

        cert_str = self.csr.get_cert(api_client)
        self.crt = Cert(crt_data=base64.b64decode(cert_str))
        if self.key_dir:
            self.crt.save(os.path.join(
                self.key_dir, f"{self.name}.crt.pem"))

    def config(self, cluster_name, context_name):
        self.config = self._config(
            self.api_client,
            cluster_name,
            context_name,
            self.name,
            self.candk.key.base64,
            self.crt.base64)

    def _config(
            self, api_client, cluster_name, context_name,
            user_name, user_key, user_cert):
        return (
            ClusterConfigGen(
                api_client=api_client,
                cluster_name=cluster_name) | 
            UserConfigGen(
                api_client=api_client,
                user_name=user_name,
                user_key=user_key,
                user_cert=user_cert) |
            ContainerConfigGen(
                {"apiVersion": "v1", "kind": "Config", "preferences": {}}, 
                {"current-context": context_name,
                 "contexts": [
                    {"context": {
                        "cluster": cluster_name,
                        "user": user_name,
                    },
                    "name": context_name},
                ]})
            ).to_dict()

    def save_config(self, path=None):
        if not path:
            path = os.path.join(self.key_dir, 'kubeconfig.yaml')
        with open(path, 'w') as f:
            f.write(yaml.dump(self.config))