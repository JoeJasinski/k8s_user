import os
import sys
import argparse
import kubernetes
from kubernetes import client, config
from .user import K8sUser


parser = argparse.ArgumentParser(description="Create K8S User", epilog="")

parser.add_argument("name", nargs="?")
parser.add_argument(
    "-d",
    "--out-dir",
    dest="out_directory",
    help="output directory for key files",
    default=None,
)
parser.add_argument(
    "--out-kubeconfig-context-name",
    dest="out_context",
    help="output kubernetes context name",
    default="default",
)
parser.add_argument(
    "--out-kubeconfig-cluster-name",
    dest="out_cluster",
    help="output kubernetes cluster name",
    default="default",
)
parser.add_argument(
    "-k", "--out-kubeconfig", dest="out_kubeconfig", help="output kubeconfig file"
)
parser.add_argument(
    "--kubeconfig", dest="in_kubeconfig", help="input kubeconfig file", default=None,
)
parser.add_argument(
    "--in-key",
    dest="in_key",
    help="input rsa key pem file (load instead of generate)",
    default=None,
)
parser.add_argument(
    "--in-key-password",
    dest="in_key_password",
    help="input rsa key pem file password (requires --in-key)",
    default=None,
)

args = parser.parse_args()
print(args)

if not args.name:
    print("Name argument must be specified")
    sys.exit(1)

out_directory = args.out_directory

if args.out_kubeconfig:
    out_kubeconfig = args.out_kubeconfig
else:
    out_kubeconfig = f"{args.name}-kubeconfig.yaml"
    if out_directory:
        out_kubeconfig = os.path.join(out_directory, out_kubeconfig)

if os.path.isfile(out_kubeconfig):
    print("kubeconfig file exists already at this location")
    sys.exit(1)

api_client = config.new_client_from_config(config_file=args.in_kubeconfig)

try:
    user = K8sUser(
        name=args.name,
        key_dir=out_directory,
        in_key=args.in_key,
        in_key_password=args.in_key_password,
    )

    user.create(api_client)
    user.make_kubeconfig(cluster_name=args.out_cluster, context_name=args.out_context)

    user.kubeconfig.save(out_kubeconfig)
except Exception as e:
    raise
    print(f"{e}")
    sys.exit(1)
