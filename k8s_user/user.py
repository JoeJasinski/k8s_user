import os
import base64
from .k8s.csr_resource import CSRResource
from .pki import Cert, CSRandKey

class K8sUser:
    def __init__(self, name, key_dir):
        self.name = name
        self.key_dir = os.path.abspath(key_dir)
        self._generate()

    def _generate(self):
        self.candk = CSRandKey(common_name=self.name)
        key_path = os.path.join(self.key_dir, f"{self.name}.key.pem")
        if os.path.exists(key_path):
            raise Exception(f"Key already exists at {key_path}")
        self.candk.key.save(key_path)
        csr_path = os.path.join(self.key_dir, f"{self.name}.csr.pem")
        self.candk.csr.save(csr_path)

    def create(self, api_client):
        self.csr = CSRResource(
            name=self.name,
            csr_str=self.candk.csr.base64)
        self.csr.create(api_client)
        self.csr.approve(api_client)

        cert_str = self.csr.get_cert(api_client)
        self.cert = Cert(
            crt_data=base64.b64decode(cert_str))
        self.cert.save(os.path.join(
            self.key_dir, f"{self.name}.crt.pem"))
