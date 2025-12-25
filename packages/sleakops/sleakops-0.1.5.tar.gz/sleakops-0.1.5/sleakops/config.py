import os
from importlib.metadata import version, PackageNotFoundError

# Version handling
try:
    __version__ = version("sleakops-cli")
except PackageNotFoundError:
    # package is not installed
    __version__ = "dev"

# API Configuration
API_URL = os.environ.get("SLEAKOPS_API_URL", "https://api.sleakops.com/api/")
CONSOLE_API_URL = os.environ.get(
    "SLEAKOPS_CONSOLE_API_URL",
    "https://console.sleakops.com/api/"
)

# Polling Configuration
MAX_POLLING = int(os.environ.get("MAX_POLLING", 1000))
SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 10))

# API Endpoints
BUILD_ENDPOINT = "cli-build/"
DEPLOY_ENDPOINT = "cli-deployment/"
PROJECT_ENV_ENDPOINT = "project-env/"
SERVICE_ENDPOINT = "service/"
LOGIN_ENDPOINT = "login/"
TOKEN_REFRESH_ENDPOINT = "token/refresh/"
ACCOUNT_ENDPOINT = "account/"

# Authentication
CREDENTIALS_FILE = os.path.expanduser("~/.sleakops/credentials.json")

# Cluster Management
CLUSTER_ENDPOINT = "cluster/"
KUBECONFIG_PATH = os.path.expanduser("~/.kube/config")
