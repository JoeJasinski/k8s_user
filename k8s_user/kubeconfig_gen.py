import base64

def _read_cert(path):
    with open(path, 'rb') as f:
        return f.read()

def _base64(cert_data):
    return base64.b64encode(cert_data).decode('utf-8')


class ContainerConfigGen:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def to_dict(self):
        left = self.left.to_dict() if hasattr(self.left, 'to_dict') else self.left
        right = self.right.to_dict() if hasattr(self.right, 'to_dict') else self.right
        return {**right, **left}

    def __or__(self, other):
        return ContainerConfigGen(self, other)


class ClusterConfigGen:
    def __init__(self, api_client, cluster_name):
        self.api_client = api_client
        self.cluster_name = cluster_name

    @property
    def cluster_ca_cert(self):
        return _base64(_read_cert(
            self.api_client.configuration.ssl_ca_cert))

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
        return ContainerConfigGen(self, other)


class UserConfigGen:
    def __init__(self, api_client, user_name, user_key, user_cert):
        self.api_client = api_client
        self.user_name = user_name
        self.user_key = user_key
        self.user_cert = user_cert

    @property
    def cert(self):
        return _base64(_read_cert(
            self.api_client.configuration.cert_file))

    def to_dict(self):
        return {
            "users": [
                {
                    "name": self.user_name,
                    "user": {
                        "client-certificate-data": self.user_cert,
                        "client-key-data": self.user_key,
                    },
                },
            ]
        }

    def __or__(self, other):
        return ContainerConfigGen(self, other)
