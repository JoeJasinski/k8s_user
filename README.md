# 

TBD

    import kubernetes
    from kubernetes import client, config
    from k8s_user.k8s.csr_resource import CSRResource
    from k8s_user.crypto_key import CSRandKey

    csr_name = 'joe'

    # create a KEY and CSR
    ct = CSRandKey(csr_name, additional_subject={"O": "jazstudios"})

    # save the csr and key
    ct.csr.save("joe.csr")
    ct.key.save("joe.key")

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
    cert_str = csr.get_cert(api_client)