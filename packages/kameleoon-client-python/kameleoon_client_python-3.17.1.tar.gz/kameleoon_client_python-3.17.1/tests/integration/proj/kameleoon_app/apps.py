import sys
import os
from django.apps import AppConfig

ROOT_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from tests_defaults import SITE_CODE
from kameleoon import KameleoonClient, KameleoonClientConfig

from tests.test_network_manager_factory import TestNetworkManagerFactory


class KameleoonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kameleoon_app"

    def ready(self):
        config_path = os.path.join(ROOT_DIR, "tests", "resources", "config.yml")
        config = KameleoonClientConfig.read_from_yaml(config_path)
        KameleoonClient._network_manager_factory = TestNetworkManagerFactory()
        self.kameleoon_client = KameleoonClient(SITE_CODE, config)
        self.kameleoon_client.wait_init()
