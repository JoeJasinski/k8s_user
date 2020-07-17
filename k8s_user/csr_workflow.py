import os
from typing import Dict
import collections
import base64
from .pki import Cert, CSRandKey, KeyBundle
from .k8s.csr_resource import CSRResource


StepReturn = collections.namedtuple(
    "StepReturn", "next_step message"
)


class BaseStep:

    name = "base"

    def __init__(self, inputs: Dict):
        print(self.name)
        self.user = inputs.get('user')
        self.api_client = inputs.get('api_client')


class GetCSRandKeyStep(BaseStep):

    name="get_csr_and_key"

    def __init__(self, inputs):
        self.in_key = inputs.get("in_key")
        self.in_key_password = inputs.get("in_key_password")
        self.in_csr = inputs.get("in_csr")
        super().__init__(inputs)

    def run(self) -> StepReturn:
        self.user.candk = CSRandKey(
            common_name=self.user.name,
            key_file=self.in_key,
            key_file_password=self.in_key_password,
            csr_file=self.in_csr,
        )
        self.user.csr = CSRResource(
            name=self.user.name,
            csr_str=self.user.candk.csr.base64,
            metadata=self.user.metadata
        )
        return StepReturn(next_step='save_key', message="")


class SaveKeyStep(BaseStep):

    name="save_key"

    def __init__(self, inputs):
        self.in_key = inputs.get("in_key")
        self.creds_dir = inputs.get("creds_dir")
        super().__init__(inputs)

    def run(self) -> StepReturn:
        if self.creds_dir and not self.in_key:
            key_path = os.path.join(self.creds_dir, f"{self.user.name}.key.pem")
            if os.path.exists(key_path):
                raise Exception(f"Key already exists at {key_path}")
            self.user.candk.key.save(key_path)
        return StepReturn(next_step='save_csr', message="")


class SaveCSRStep(BaseStep):

    name="save_csr"

    def __init__(self, inputs):
        self.in_csr = inputs.get("in_csr")
        self.creds_dir = inputs.get("creds_dir")
        super().__init__(inputs)

    def run(self) -> StepReturn:
        if self.creds_dir and not self.in_csr:
            csr_path = os.path.join(self.creds_dir, f"{self.user.name}.csr.pem")
            self.user.candk.csr.save(csr_path)
        return StepReturn(next_step='csr_create_resource', message="")


class ResourceExistsStep(BaseStep):

    name="csr_resource_exists"

    def run(self) -> StepReturn:
        self.user.csr.resource_exists(self.api_client)
        return StepReturn(next_step='csr_create_resource', message="")


class CreateResourceStep(BaseStep):

    name="csr_create_resource"

    def run(self) -> StepReturn:
        self.user.csr.create(self.api_client)
        return StepReturn(next_step='csr_approve_resource', message="")


class ApproveResourceStep(BaseStep):

    name="csr_approve_resource"

    def run(self) -> StepReturn:
        self.user.csr.approve(self.api_client)
        return StepReturn(next_step='get_cert', message="")


class GetCertStep(BaseStep):

    name="get_cert"

    def run(self) -> StepReturn:
        cert_str = self.user.csr.get_cert(self.api_client)
        self.user.crt = Cert(crt_data=base64.b64decode(cert_str))
        return StepReturn(next_step='save_cert', message="")


class SaveCertStep(BaseStep):

    name="save_cert"

    def run(self) -> StepReturn:
        if self.user.creds_dir:
            self.user.crt.save(
                os.path.join(self.user.creds_dir, f"{self.user.name}.crt.pem"))
        return StepReturn(next_step='make_kubeconfig', message="")


class MakeKubeConfigStep(BaseStep):

    name="make_kubeconfig"

    def __init__(self, inputs):
        self.cluster_name = inputs.get("cluster_name")
        self.context_name = inputs.get("context_name")
        super().__init__(inputs)

    def run(self) -> StepReturn:

        keybundle = KeyBundle(
            user_name=self.user.name,
            user_key=self.user.candk.key.base64,
            user_csr=self.user.candk.key.base64,
            user_cert=self.user.crt.base64,
        )
        self.user.kubeconfig = self.user.kubeconfig_klass(
            self.api_client, self.cluster_name, self.context_name, keybundle,
        )
        self.user.kubeconfig_dict = self.user.kubeconfig.generate()

        return StepReturn(next_step='end', message="")


class EndStep(BaseStep):

    name="end"

    def run(self) -> StepReturn:
        return StepReturn(next_step=None, message="")


class UserCSRWorkflow:
    steps = [
        GetCSRandKeyStep,
        SaveKeyStep,
        SaveCSRStep,
        ResourceExistsStep,
        CreateResourceStep,
        ApproveResourceStep,
        GetCertStep,
        SaveCertStep,
        MakeKubeConfigStep,
        EndStep,
    ]

    step_instances = {}

    def __init__(self, start_step, inputs: Dict):
        self.start_step = start_step
        for step_class in self.steps:
            self.step_instances[step_class.name] = step_class(inputs)

    def start(self):
        step = StepReturn(self.start_step, '')
        while step.next_step:
            step = self.step_instances[step.next_step].run()
