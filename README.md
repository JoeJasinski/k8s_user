# Kubernetes User Creator

The goal of this project is to make it easy to create a kubernetes user.

TODO
- [x] Automate the creation of openssl key and csr
- [x] Automate the creation of a k8s CSR resource
- [x] Automate the approval of the CSR resource
- [x] Automate the creation of a kubeconfig 
- [x] Automate or document the creation of cluster premissions
- [x] Create a command line tool as well as python api
- [ ] Automate the SA Token workflow
- [ ] Document well
- [ ] Automate the build
- [ ] Good test coverage


## CLI Quick Start

```bash
python -m k8s_user mysecretname

python -m k8s_user mysecretname \
    --kubeconfig ~/.kube/config
```

## Python Quick Start

Create and sign the user

```python
import kubernetes
from kubernetes import client, config
api_client = config.new_client_from_config()

from k8s_user import K8sUser
user = K8sUser(name="joe", key_dir=".")
user.create(api_client)
user.config(cluster_name="joe", context_name="my-context")
user.save_config("kubeconfig.yaml")
```

Add a clusterrollbinding for the new users

```bash
kubectl create clusterrolebinding joe-admin --clusterrole=admin --user=joe
```

## Detailed API Interaction

```python
import kubernetes
from kubernetes import client, config
from k8s_user.k8s.csr_resource import CSRResource
from k8s_user.pki import CSRandKey, Cert

csr_name = 'joe'

# create a KEY and CSR
ct = CSRandKey(csr_name, additional_subject={"O": "jazstudios"})

# save the csr and key
ct.csr.save("joe.csr.pem")
ct.key.save("joe.key.pem")

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

ct = Cert(crt_data=base64.b64decode(crt_str))
ct.save('joe.crt.pem')
```
