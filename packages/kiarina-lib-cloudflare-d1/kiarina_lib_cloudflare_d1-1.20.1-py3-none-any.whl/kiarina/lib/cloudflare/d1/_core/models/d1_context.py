from dataclasses import dataclass

from kiarina.lib.cloudflare.auth import CloudflareAuthSettings

from ..._settings import D1Settings


@dataclass
class D1Context:
    settings: D1Settings

    auth_settings: CloudflareAuthSettings

    @property
    def query_api_url(self) -> str:
        return "https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query".format(
            account_id=self.auth_settings.account_id,
            database_id=self.settings.database_id,
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.auth_settings.api_token.get_secret_value()}",
            "Content-Type": "application/json",
        }
