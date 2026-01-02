import os
import logging
import threading

from typing import Optional

import requests
from environs import Env

from paytechuz.core.exceptions import UnknownPartnerError


logger = logging.getLogger(__name__)


API_KEY_ENV_NAME = "PAYTECH_LICENSE_API_KEY"
env = Env()
env.read_env()


OFFLINE_API_KEYS = [
    "808e6b0d-6099-4045-a289-90999b7533a8",
    "19dbc03d-8c6f-4164-8dcd-e85c78fe351d",
    "e9cf78aa-4292-4dd0-a0c2-cd325a3e8482",
    "ec042d30-10b9-400c-b4f7-88af6b6b5bc3",
    "8bbec0dc-6362-4168-84b0-1c2ba62318e8",
    "b65f8e7f-53e6-4477-add0-1952dc3f58f8",
    "7018a544-99ed-4bc6-854f-fcfd224b3164",
    "6ecde9d8-9ee4-433c-866e-0d2cd2d7aef7",
    "a5c7ad32-9001-4a07-b38b-ecb083ba439a",
    "496d4efa-f99c-43de-92bd-55158d08371f",
    "f6dccafa-307b-429a-b6cb-21e6420eacd9",
    "afbf4e5e-2dc2-477f-825b-6b90fc6065cd",
    "b6fc7d94-bc67-4bb3-b5d8-d7b9cc5985c1",
    "95b5f9aa-a3d1-4bf3-9543-15a122084ae5",
    "66adece6-3d7d-4558-a085-7057c078f555",
    "564362cb-a340-4fe5-98d7-ef4b9fd56524",
    "dca425bf-64ff-4979-86ca-32e883c3eaca",
    "305c6289-3f20-4b15-8881-3615d3fe27ae",
    "5febc6b3-d8d1-4cca-ba85-489f61d77307",
    "841ee495-d46f-43be-9e39-ade5bf632c1a",
    "3b061293-78e0-4e68-b9cf-b77cc8eb6e25",
    "ab29ca7f-657a-4e0c-8724-977116c9e690",
    "fc091206-601d-4d2d-be98-cfa60ba5756c",
    "79caec83-bd5a-4091-9844-df463e4ceae9",
    "c3ea4753-dd70-46ee-9cb9-41563880f3b7",
    "2d1acb40-595e-49a7-884d-bbbd5917bdd5",
    "ead65356-a50c-4e06-a496-2d015b4ddd82",
    "d8452141-36db-4e44-9173-3f0f70a7c66c",
    "46ba950b-2ef8-48bf-b9e7-2b395cd31648",
    "d52edae0-91a2-4524-8b56-b5467176d06a",
    "8a11a511-8300-4b40-b515-0648b7becbcf",
    "7a6928d4-a688-4e09-b1f6-c381118f8ac8",
    "b3af2473-2132-4cd6-adcb-b313a2cce30a",
    "636caa11-3a7c-4721-9b6c-2e9534de5aa0",
    "67bb0d34-b865-450f-9e11-6fa2adeccc1d",
    "d18f6de4-0013-4cc4-b39a-5e25600271b2",
    "23ae35e8-ec56-45c4-a5b4-3cf1c7329c63",
    "807db634-88fa-4293-b46a-8ed790fbeb2a",
    "cd831af4-804e-4d8c-9a02-c474477063e6",
    "34b1a832-b6be-4ebd-911d-96b715e025ae",
    "34aea8a8-8b75-4ed9-bfb5-166cf76b5052",
    "cdc55b7c-8cbb-4506-b66c-978b2ab2137b",
    "1c2f67bd-7ed5-4732-ab8a-e38ca1c99dea",
    "f712c674-d694-4fb5-8f48-7ee8411ada79",
    "0a2a5448-670b-4837-8a06-0b2a84453c3a",
    "00c1983b-df6c-491b-bc97-5bbb983c3d04",
    "ea32ee4d-cbf5-40b3-b4ee-759db947851c",
    "1ff63e1b-bcdc-4048-b940-7f444e4a4dee",
    "f08ddd1b-2447-4c47-8a5d-eadcb392c5f0",
    "8cf873e5-5934-433b-b360-164080e05814",
    "5d8e6158-c34d-45ba-afb4-b90d0af7ffb1",
    "f72ed1a8-58d0-4334-be6d-c85f7efb0733",
    "ab3639c3-56e2-4076-9dac-4fef28a79628",
    "0f792e21-21b9-4723-9f72-e36737d709b8",
    "91f21921-f780-4ac0-ac8d-77352f74ac1c",
    "45479ae5-170a-4039-bb1c-d7f051e7965e",
    "79f042b7-6e7d-49b0-806e-60761c22874d",
    "6d0b40aa-797b-438f-b687-d2ffeec5d150",
    "9a725c30-59cc-40ee-bb75-d4e6c419fc96",
    "ab6397f8-a2d6-48d8-adf3-7f197d34aa4d",
    "2ae7daa0-6742-4d9e-99a9-4bfb0375a768",
    "1fa2d320-e669-4714-8947-cd37eefebb1c",
    "d2a1a705-f7fb-472d-8b42-ea9590a3e3b6",
    "e2875d8a-7f5b-481d-90ea-a7d1aef087a8",
    "aaba6dcf-2973-4494-bab8-7d55b9b30804",
    "590b08e2-8557-4ab2-a79f-05005da4ddb9",
    "d18e2b0d-dea5-4795-98f7-a27c1b508959",
    "a056b450-75b0-4a46-9499-89647755926b",
    "730ba746-3624-48e3-81ce-a79fb8470eb6",
    "b5df6078-db80-446a-9ca2-346a4f828596",
    "1f9d896b-f45c-4b7d-9c44-8e123365bea1",
    "d5384069-b6b9-47c6-b83e-d707da65b2af",
    "07b15ae4-9c3b-4ded-9758-8ce4132fd451",
    "9f64e1dd-1730-467e-b531-54a80725f2ef",
    "94e565b2-bfea-4fda-9af4-f1741b921c85",
    "a466a8b5-c4f9-4387-9e8d-fb42563d7e21",
    "8b4351b3-7f83-4d25-95a7-a832a2bac54a",
    "b84d0c0c-ccec-4539-a6b1-18e0810c0fa6",
    "dcce6817-de4d-45f5-8c82-f4af866afc21",
    "bc5576c4-da16-4645-b8d8-ef4c449c4253",
    "57b8698d-d21d-44d0-b043-85f4f59973c4",
    "3f84177f-4dcf-4b20-8dfc-91821033cb79",
    "fbd2b24b-1809-40ef-9f41-54250cccddd3",
    "b21af09b-cd8e-4298-81e7-84e49b7da26e",
    "f28a27ad-ead6-4f46-b56f-09612046cb41",
    "a0c78fbb-c063-4fbe-91fa-19bad0040e98",
    "3df7c83a-46af-4871-90a8-22533801dded",
    "5a9d04c1-ebba-45ab-b147-6a5ad25b7311",
    "dcd3e201-5a28-4393-839e-55c452648909",
    "579210be-7bdd-4698-bfb5-b0d49659a437",
    "b1ec7772-83b8-4b1d-a317-fbf6059d3d20",
    "eb79f691-f823-4588-9ff3-87cf5218398e",
    "e37a122d-ff34-4686-bd73-5a6d8818dd75",
    "9f2e3262-e462-48fc-96b7-4e202d15bfb9",
    "4d1f9bfb-d136-48c2-bef2-0c6189a0202e",
    "a3fc2212-c225-4476-a201-c00b68a38bae",
    "9de6bf82-b9af-4fbd-9d1a-4db2f819a5e5",
    "4bdf32c8-154d-4f6f-bc70-4d2fb0aba3e9",
    "c4ea8658-b9c2-432e-9b6c-c59e4160a624",
    "6d982bda-fab5-4527-8ce7-eb74bc3c9bc8",
]


class LicenseManager:
    """Manager for license validation and usage tracking."""

    @staticmethod
    def _get_license_api_key(explicit_key: Optional[str]) -> str:
        """Get license API key from explicit parameter or environment."""
        license_api_key = explicit_key or env.str(API_KEY_ENV_NAME, None)
        if not license_api_key:
            raise UnknownPartnerError(
                f"Missing license_api_key for paytechuz. Please set the '{API_KEY_ENV_NAME}' environment variable "
                "or pass it explicitly. To obtain a valid license_api_key, please visit https://pay-tech.uz/console "
                "or contact @muhammadali_me on Telegram."
            )
        return license_api_key

    @staticmethod
    def validate_license_api_key(license_api_key: Optional[str] = None) -> None:
        """Validate license API key."""
        key = LicenseManager._get_license_api_key(license_api_key)

        if key in OFFLINE_API_KEYS:
            return

        try:
            license_url = "https://paytechuz-core.uz/api/tariffs/check-api-key/"
            response = requests.post(
                license_url,
                json={"api_key": key},
                headers={
                    "Content-Type": "application/json",
                },
                timeout=2,
            )
            data = response.json()
            if not data.get("valid"):
                raise UnknownPartnerError(
                    "Invalid license_api_key for paytechuz. Please visit https://pay-tech.uz/console "
                    "or contact @muhammadali_me on Telegram."
                )
        except (requests.RequestException, ValueError):
            return
        except UnknownPartnerError:
            raise

    @staticmethod
    def decrement_usage_limit(license_api_key: Optional[str] = None) -> None:
        """Decrement usage limit for the license."""
        key = LicenseManager._get_license_api_key(license_api_key)

        if key in OFFLINE_API_KEYS:
            return

        try:
            url = "https://paytechuz-core.uz/api/tariffs/use-request/"
            requests.post(
                url,
                json={"api_key": key},
                headers={"Content-Type": "application/json"},
                timeout=2,
            )

        except Exception:
            logger.exception("Error decrementing usage limit", exc_info=True)
            return

    @staticmethod
    def decrement_usage_limit_async(license_api_key: Optional[str] = None) -> None:
        """Run decrement_usage_limit in a background thread to avoid blocking."""
        thread = threading.Thread(
            target=LicenseManager.decrement_usage_limit,
            args=(license_api_key,),
            daemon=True
        )
        thread.start()


# Backward compatibility - keep old function names
def _get_license_api_key(explicit_key: Optional[str]) -> str:
    """Deprecated: Use LicenseManager._get_license_api_key instead."""
    return LicenseManager._get_license_api_key(explicit_key)


def _validate_license_api_key(license_api_key: Optional[str] = None) -> None:
    """Deprecated: Use LicenseManager.validate_license_api_key instead."""
    return LicenseManager.validate_license_api_key(license_api_key)


def decrement_usage_limit(license_api_key: Optional[str] = None) -> None:
    """Deprecated: Use LicenseManager.decrement_usage_limit instead."""
    return LicenseManager.decrement_usage_limit(license_api_key)
