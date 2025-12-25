import threading

import requests
from environs import Env

from payme.exceptions.general import UnknownPartnerError


API_KEY_ENV_NAME = "PAYTECH_LICENSE_API_KEY"
LICENSE_CHECK_URL = "https://paytechuz-core.uz/api/tariffs/check-api-key/"
LICENSE_USE_REQUEST_URL = "https://paytechuz-core.uz/api/tariffs/use-request/"
LICENSE_TIMEOUT = 2


OFFLINE_KEYS = frozenset([
    "6bb7d17e-c22b-44ee-96f3-d93f8b0d750b", # sold
    "0782557c-2972-4f74-bec0-32731bf66ae7", # sold
    "9c5a1186-ccfa-4b2a-8128-b983d2090f08",
    "ce4ec253-de89-4b74-b796-7a7d590ca3e2",
    "06df8c2e-3967-46dc-867d-3e536fb0ddc3",
    "6238644c-b4b7-4d2b-b32f-950c1432f898",
    "a36e83a9-f303-4374-9bbe-fccb90de08a1",
    "843ff4eb-b9fa-49d0-a4a3-5841b0e8d995",
    "371feaee-4853-4def-8795-425372ad0ab2",
    "6044681d-c84c-4959-b05a-2cbb9fea2bb0",
    "3fbca46d-131d-41c5-b565-fd50c89074ad",
    "77b8ffcf-dfe9-464b-a4fb-a24b5040dcad",
    "000bd8c7-68fd-41e9-bfee-7877e6f78131",
    "10e0bee6-22b2-4761-89ad-81defafb2d47",
    "39524d28-5986-4b7c-8a75-8c96b520fe6d",
    "6a9e6b84-b3ba-4ca9-95e7-cc6aec00070b",
    "ad7f65a6-541c-409d-9078-5a06477ba052",
    "9b5843a5-4745-4a04-8724-40f5724e58ef",
    "f3bf38a2-d09f-435c-8a36-46412e045f59",
    "f617bcf4-3343-4729-ba00-577d75998239",
    "8df5f081-7774-4eb8-9b2f-fa0de6094854",
    "b3b5aed6-b0fe-4a35-b1f2-13685c027d80",
    "47ffc18c-cd7f-4e24-b891-ff0973a2b990",
    "ee166871-1c9e-4f29-a139-d92c5b8bca7f",
    "4a018a92-c299-42a1-b10d-6b892a2b2881",
    "65733970-be24-46a2-b55e-0866c916379c",
    "da7a5318-4666-45ed-9ea8-11171ea20394",
    "e39b28b6-4403-4eab-b81f-0f67c0356d7e",
    "2d1acda6-80b7-4ede-be63-f1c5f9ae4def",
    "a4095870-dd87-4dce-b27c-564bc639d28c",
    "db3d8d6c-93eb-4f1d-a3a1-0d7644eca82d",
    "4862616d-9ce5-44a7-85f4-b9712e123406",
    "e38240f4-c5db-429c-8935-129268c35793",
    "77a42812-0caf-4dce-a1fa-c32907ffc1a8",
    "1d6a71fc-c9bc-4f75-b2c9-ad3ad14e6592",
    "e2fc045d-d647-4b46-9c7b-843ca9ad0de7",
    "edff23fb-51bc-44c4-8237-5dea6f065962",
    "2935925b-b6a0-45d0-b2ac-a7856d81633b",
    "fb51c48f-76e2-403e-b20a-b6b635a566b3",
    "09038522-45ea-46ae-84e0-3518afb6d357",
    "7efaa126-e806-4849-aace-1b370b7b66fd",
    "c772c8e8-2b4c-4fa1-8c9c-b922c090668b",
    "17deaac2-bbc0-4dd0-9d7b-76fdb6e2c9c4",
    "309588bd-ef03-4c13-8104-a9c2d762b4da",
    "20bcdf2b-b390-4a49-adfd-d193e1a31d1d",
    "5d8b2e69-bbf5-4616-a886-9d6e67a51a92",
    "5d941e4e-953e-44bd-8a63-b0ca4aebfe6c",
    "b4a5ceba-fc07-44d3-b93f-8a0482aff039",
    "cfc68aaa-92ee-46ee-8c45-e31de10d6bc2",
    "bbbe3edc-3e41-4ffa-93a7-20d96b69a1a9",
    "5178717d-beb5-4a82-8102-21b70b2a5034",
    "b97c5aa4-5d10-4ed8-bae6-d4a254bd532e",
    "1886fc83-f7bc-4aa1-8af2-f5a5f83c1c7e",
    "123fdd2e-0061-4578-9a4e-ff35a9f82608",
    "18b5df36-bbb8-44b0-b2ff-6d788f8d31b8",
    "eaac08c3-2e50-46d4-b70b-f76170023457",
    "e7052044-6faf-4c1b-885a-82d607545e1a",
    "5f75b1f0-84d1-4c7f-847c-4a753f522267",
    "d4454e2f-85c4-4e2c-97b4-1e1a5f8ea6d2",
    "faaf4e07-196f-4759-845e-06615d606278",
    "30a4fd9d-2118-4b2d-bc26-5b6bbd557018",
    "43ce56e9-d415-42ab-9ddf-ef353f29a800",
    "43178f4b-8afc-442a-bc3c-0a434598d8a5",
    "0631fdb3-fadc-4595-af64-a95bb28789f0",
    "4de3673e-ffa8-457d-8f16-a8fa498d8ecf",
    "3c288304-3c79-4b97-a05c-42e756e79de2",
    "d9e88648-6e75-4971-897e-5ab8004e5b6f",
    "69e6f608-3ed4-4750-96b5-cf5ca4ed6753",
    "6be9db75-c309-4409-b760-a98de0b513c2",
    "9b12ca3a-04ea-409d-a2ca-1bdc4ba366f0",
    "6e498d2c-0d28-41d8-87b6-b5c84b4c6c15",
    "f3834390-6ecb-4a87-8680-604fe26f837e",
    "8d32e859-3fbe-45e2-bd65-8a48c648070c",
    "b00254a8-2cef-4ed9-85a5-f32a2948e16b",
    "619c1d29-0131-4b36-8de7-ae2c52cfc1bd",
    "090be6d5-c531-4292-9f46-014b39ad6abe",
    "e1377172-69be-4e13-969f-3017ad9e4a46",
    "a8d230be-426c-40e2-a610-52f28c4def62",
    "7e54c897-c0ae-4408-b3b4-cbb874f682a5",
    "6b3e5e75-9ec2-4c01-ab85-72ca8305d109",
    "b4c4bfcd-48cd-4cf2-9c2b-cdade247b7df",
    "58e7d867-5d25-4024-89c8-347edbdda4c8",
    "06d03fda-322c-41a5-b252-b3dab25b00f8",
    "a68c35eb-c72f-4b32-b21b-c68488fb0295",
    "21bee792-0eeb-4985-b298-ff9334c2bacb",
    "6fba8021-2524-4372-8197-5a9a7726226e",
    "6176ff1f-1a09-49e2-acba-f11f80fc6a13",
    "c38afcc4-1b82-4bc5-9bc0-891a774d0f81",
    "fa21ac11-49c9-495a-8329-9638f92c71bf",
    "dd778a95-67ee-40f1-8e23-eb20fe679002",
    "76223204-4ddd-4cad-8435-1b094b5c7071",
    "b724833d-d602-4385-a35b-c00a3b8cb203",
    "ad7045d2-5e37-409b-a030-f233a5c4dfe1",
    "a6681de4-70fd-4295-b31f-3b10b2cefc46",
    "d5992998-b2bb-4fdf-a26d-b07588620e59",
    "dd3e3e66-3d73-4f13-8085-9a9a7af9e201",
    "44e637af-683f-426f-bf26-90b34b6403a8",
    "91b966c1-d34b-445f-846b-065011c76347",
    "167607af-31e1-46fc-80ac-dec75123caac",
    "93480f14-3164-4ac4-b8a1-b44dfd44acbd",
    "2c678901-6a8a-4f59-b47f-dc0368f8403d",
])


def _get_api_key_from_env() -> str:
    env = Env()
    env.read_env()
    api_key = env.str(API_KEY_ENV_NAME, default=None)
    if not api_key:
        raise UnknownPartnerError(
            "Missing PAYTECH_LICENSE_API_KEY in environment. "
            "Get your API key at https://docs.pay-tech.uz/console or contact @muhammadali_me on Telegram."
        )
    return api_key


def _handle_api_response(response: requests.Response) -> None:
    if response.status_code >= 500:
        return

    try:
        data = response.json()
    except ValueError:
        return

    if "error_type" in data and data["error_type"] == "invalid_api_key":
        error_msg = data.get("error_message", {})
        msg = error_msg.get("en", "Invalid or inactive API key.")
        raise UnknownPartnerError(
            f"{msg} Get your API key at https://docs.pay-tech.uz/console or contact @muhammadali_me on Telegram."
        )

    if data.get("valid") is True:
        return

    if data.get("valid") is False:
        error = data.get("error", "License validation failed.")
        raise UnknownPartnerError(
            f"{error} Visit https://docs.pay-tech.uz/console or contact @muhammadali_me on Telegram."
        )


def validate_api_key() -> None:
    key = _get_api_key_from_env()

    if key in OFFLINE_KEYS:
        return

    try:
        response = requests.post(
            LICENSE_CHECK_URL,
            json={"api_key": key},
            headers={"Content-Type": "application/json"},
            timeout=LICENSE_TIMEOUT,
        )
        _handle_api_response(response)
    except requests.RequestException:
        pass


def _send_usage_request(api_key: str) -> None:
    try:
        requests.post(
            LICENSE_USE_REQUEST_URL,
            json={"api_key": api_key},
            headers={"Content-Type": "application/json"},
            timeout=LICENSE_TIMEOUT,
        )
    except requests.RequestException:
        pass


def track_successful_transaction() -> None:
    try:
        api_key = _get_api_key_from_env()
    except UnknownPartnerError:
        return

    thread = threading.Thread(target=_send_usage_request, args=(api_key,), daemon=True)
    thread.start()
