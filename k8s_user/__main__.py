import os
import argparse
from .user import K8sUser
import kubernetes
from kubernetes import client, config


parser = argparse.ArgumentParser(
    description='Create K8S User',
    epilog='')

parser.add_argument('name', nargs='?')
parser.add_argument('-d', "--directory", help='Key Dir')
parser.add_argument('-c', "--context", help="context name", default="default")
args = parser.parse_args()
print(args)
api_client = config.new_client_from_config()
user = K8sUser(name=args.name, key_dir=args.directory)
user.create(api_client)
user.config(cluster_name="default", context_name=args.context)
user.save_config(os.path.join(args.directory, "kubeconfig.yaml"))