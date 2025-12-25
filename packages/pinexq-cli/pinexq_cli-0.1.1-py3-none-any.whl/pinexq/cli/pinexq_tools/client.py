from httpx import Client


def get_client(endpoint: str, api_key: str):
    if api_key is None or api_key == "":
        raise Exception("PINEXQ_API_KEY is required. Provide it by the environment variable `PINEXQ_API_KEY` globally or in .env or using --api-key flag.")
    pinexq_endpoint = f'https://{endpoint.replace("https://", "").replace("http://", "")}'
    return Client(base_url=pinexq_endpoint, headers={'x-api-key': api_key})
