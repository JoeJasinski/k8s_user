from typing import Optional, Dict, List
import base64
import yaml


def _read_cert(path):
    with open(path, "rb") as f:
        return f.read()


def _base64(cert_data):
    return base64.b64encode(cert_data).decode("utf-8")


class GenericConfigGen:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_dict(self):
        left = self.left.to_dict() if hasattr(self.left, "to_dict") else self.left
        right = self.right.to_dict() if hasattr(self.right, "to_dict") else self.right
        return {**right, **left}

    def __or__(self, other):
        return GenericConfigGen(self, other)


class ClusterConfigGen:
    def __init__(self, api_client, cluster_name):
        self.api_client = api_client
        self.cluster_name = cluster_name

    @property
    def cluster_ca_cert(self):
        return _base64(_read_cert(self.api_client.configuration.ssl_ca_cert))

    @property
    def host(self):
        return self.api_client.configuration.host

    def to_dict(self):
        return {
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": self.cluster_ca_cert,
                        "server": self.host,
                    },
                    "name": self.cluster_name,
                },
            ]
        }

    def __or__(self, other):
        return GenericConfigGen(self, other)


class UserConfigGen:
    def __init__(self, api_client, keybundle):
        self.api_client = api_client
        self.keybundle = keybundle

    @property
    def cert(self):
        return _base64(_read_cert(self.api_client.configuration.cert_file))

    def to_dict(self):
        return {
            "users": [
                {
                    "name": self.keybundle.user_name,
                    "user": {
                        "client-certificate-data": self.keybundle.user_cert,
                        "client-key-data": self.keybundle.user_key,
                    },
                },
            ]
        }

    def __or__(self, other):
        return GenericConfigGen(self, other)


class KubeConfig:

    config_gen_klasses = {
        "cluster": ClusterConfigGen,
        "user": UserConfigGen,
        "container": GenericConfigGen,
    }

    def __init__(
        self,
        api_client,
        cluster_name,
        context_name,
        keybundle,
        config_gen_klasses: Optional[Dict] = None,
    ):

        self.api_client = api_client
        self.cluster_name = cluster_name
        self.context_name = context_name
        self.keybundle = keybundle
        self.kubeconfig_dict = {}
        if config_gen_klasses:
            self.config_gen_klasses.update(config_gen_klasses)

    def generate(self):
        self.kubeconfig_dict = (
            self.config_gen_klasses["cluster"](
                api_client=self.api_client, cluster_name=self.cluster_name
            )
            | self.config_gen_klasses["user"](
                api_client=self.api_client, keybundle=self.keybundle
            )
            | self.config_gen_klasses["container"](
                {"apiVersion": "v1", "kind": "Config", "preferences": {}},
                {
                    "current-context": self.context_name,
                    "contexts": [
                        {
                            "context": {
                                "cluster": self.cluster_name,
                                "user": self.keybundle.user_name,
                            },
                            "name": self.context_name,
                        },
                    ],
                },
            )
        ).to_dict()
        return self.kubeconfig_dict

    def save(self, path):
        if not self.kubeconfig_dict:
            self.generate()
        with open(path, "w") as f:
            f.write(yaml.dump(self.kubeconfig_dict))
