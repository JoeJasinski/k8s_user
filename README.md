# Kubernetes User Creator

The goal of this project is to make it easy to create a Kubernetes user. While the k8s
documentation is quick to point out that users do not exist in Kubernetes, sometimes
you just want to generate a kubeconfig which has access to the cluster.

This access can be achived by the following means:

- create a Service Account with a token with access to the cluster
- create a RSA certificate/key pair allowing access to the cluster

The "user" is not given any permissions be default, so you still need to create/associate
the user with ClusterRoleBindings/RoleBindgins.

This project is inspired by the following blog post:
https://www.openlogic.com/blog/granting-user-access-your-kubernetes-cluster

TODO
- [x] Automate the creation of openssl key and csr
- [x] Automate the creation of a k8s CSR resource
- [x] Automate the approval of the CSR resource
- [x] Automate the creation of a kubeconfig 
- [x] Automate or document the creation of cluster premissions
- [x] Create a command line tool as well as python api
- [X] Automate the SA Token workflow
- [ ] Allow passing in SA and CSR resource metadata to CLI
- [ ] Document well
- [ ] Automate the build
- [ ] 95% test coverage


## Install

```bash
pip install kubernetes-user
```

## CLI Quick Start

### Generate a CSR-based User

```bash

# basic usage

k8s_user csr myusername

# or providing a non-default kubeconfig

python -m k8s_user csr myusername \
    --kubeconfig ~/.kube/config

# or without installing

python -m k8s_user csr myusername

# or without installing and providing a non-default kubeconfig

python -m k8s_user csr myusername \
    --kubeconfig ~/.kube/config
```

### Generate a SA-based User with token

```bash

# basic usage

k8s_user sa myusername

# or providing a non-default kubeconfig

k8s_user sa myusername \
    --kubeconfig ~/.kube/config

# or without installing

python -m k8s_user sa myusername

# or without installing and providing a non-default kubeconfig

python -m k8s_user sa myusername \
    --kubeconfig ~/.kube/config
```

Add a clusterrollbinding for the new user

```bash
kubectl create clusterrolebinding joe-admin --clusterrole=admin --user=joe
```


## Python API Quick Start

Create and sign the user

```python
import kubernetes
from kubernetes import client, config
api_client = config.new_client_from_config()

from k8s_user import CSRK8sUser
user = CSRK8sUser(name="joe")
inputs = {
    "cluster_name": "default",
    "context_name": "default",
    "out_kubeconfig": "new-kubeconfig.yaml",
    "creds_dir": ".",
}
user.create(api_client, inputs)

```

Add a clusterrollbinding for the new user

```bash
kubectl create clusterrolebinding joe-admin --clusterrole=admin --user=joe
```

## Low-Level CSR API Interaction

```python
import kubernetes
from kubernetes import client, config
from k8s_user.k8s.csr_resource import CSRResource
from k8s_user.pki import CSRandKey, Cert

csr_name = 'joe'

# create a KEY and CSR
candk = CSRandKey(csr_name, additional_subject={"O": "jazstudios"})

# save the csr and key
candk.csr.save("joe.csr.pem")
candk.key.save("joe.key.pem")

# create the k8s api client
api_client = config.new_client_from_config()

# Check if the k8s CSR resource exists
csr.resource_exists(api_client)

# Create the k8s CSR resource
obj = csr.create(api_client)

# Check again if the k8s CSR resource exists (it will now)
csr.resource_exists(api_client)

# Approve the k8s CSR resource
approved_csr_obj = csr.approve(api_client)

# Get the certificate file
crt_str = csr.get_cert(api_client)

candk = Cert(crt_data=base64.b64decode(crt_str))
candk.save('joe.crt.pem')
```
