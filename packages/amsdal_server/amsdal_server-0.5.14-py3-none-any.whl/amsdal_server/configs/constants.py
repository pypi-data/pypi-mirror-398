import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
TESTING_ENVIRONMENT = 'testing'
DEVELOPMENT_ENVIRONMENT = 'development'
PRODUCTION_ENVIRONMENT = 'production'

# API Tags
TAG_COMMON = 'Common'
TAG_API = 'API'
TAG_OBJECTS = 'Objects'
TAG_SCHEMAS = 'Schemas'
TAG_TRANSACTIONS = 'Transactions'
TAG_CLASSES = 'Classes'
TAG_PROBES = 'Probes'

APP_DESCRIPTION = (BASE_DIR / 'docs' / 'api.md').read_text()


def check_force_test_environment(default: str) -> str:
    cmd = sys.argv[0] if sys.argv else ''

    if 'pytest' in cmd:
        return TESTING_ENVIRONMENT
    return default
