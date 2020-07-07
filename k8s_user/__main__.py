import argparse
from .user import K8sUser
import kubernetes
from kubernetes import client, config


parser = argparse.ArgumentParser(
    description='Create K8S User',
    epilog='')

parser.add_argument('name', nargs='?')
parser.add_argument('-d', "--directory", help='Key Dir')
args = parser.parse_args()
print(args)
api_client = config.new_client_from_config()
user = K8sUser(name=args.name, key_dir=args.directory)
user.create(api_client)
