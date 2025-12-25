from typing import Optional

from httpx import Client
from pinexq_client.job_management import EntryPointHco, enter_jma
from pydantic import BaseModel


class Info(BaseModel):
    user_id: str
    org_id: Optional[str] = None
    user_grants: list[str]
    registry_endpoint: str
    api_key: str

    def get_context_id(self) -> str:
        if not self.org_id:
            return self.user_id
        else:
            return self.org_id

    def get_docker_auth(self):
        return {
            "username": self.user_id,
            "password": self.api_key,
        }


def get_info(client: Client) -> Info:
    entrypoint: EntryPointHco = enter_jma(client)
    info = entrypoint.info_link.navigate()
    return Info(
        user_id=info.current_user.user_id.__str__(),
        org_id=info.organization_id,
        user_grants=info.current_user.user_grants,
        registry_endpoint=str(info.deployment_registry_endpoint.get_url()),
        api_key=client.headers.get("x-api-key")
    )
