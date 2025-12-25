import asyncio
import jwt
import httpx
from decouple import config
from altscore.borrower_central import BorrowerCentralAsync, BorrowerCentralSync
from altscore.altdata import AltDataSync, AltDataAsync
from altscore.cms import CMSSync, CMSAsync
from altscore.macros import MacrosSync, MacrosAsync
from altscore.comms import CommsSync, CommsAsync
from typing import Optional, Union
import warnings
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from loguru import logger



warnings.filterwarnings("ignore")


class AltScoreBase:

    def __init__(self, tenant: str = "default", environment: str = "production",
                 api_key: str = None, user_token: Optional[str] = None,
                 email: Optional[str] = None, password: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 form_token: Optional[str] = None, partner_id: Optional[str] = None):
        self.environment = environment
        self.tenant = tenant
        self.form_token = form_token
        self._partner_id = partner_id
        self.api_key = api_key
        self.user_token = user_token
        self._refresh_token = None
        if self.api_key is None and self.user_token is None and self.form_token is None:
            self.auth(
                email=email,
                password=password,
                client_id=client_id,
                client_secret=client_secret
            )

    def auth(self, email: Optional[str] = None, password: Optional[str] = None,
             client_id: Optional[str] = None, client_secret: Optional[str] = None) -> None:
        if email is not None and password is not None:
            self.user_token = login_with_user_credentials(
                email=email,
                password=password,
                environment=self.environment,
                tenant=self.tenant
            )
        elif client_id is not None and client_secret is not None:
            self.user_token, self._refresh_token = login_with_client_credentials(
                client_id=client_id,
                client_secret=client_secret,
                environment=self.environment,
                tenant=self.tenant
            )
        else:
            raise ValueError("Authentication error, "
                             "either email and password or client_id and client_secret must be provided")

    def renew_token(self) -> None:
        if self._refresh_token is None:
            altscore_email = config("ALTSCORE_EMAIL", None)
            altscore_password = config("ALTSCORE_PASSWORD", None)
            if altscore_email is None or altscore_password is None:
                raise ValueError("Authentication error, "
                                 "refresh token not found and no credentials provided as environment variables")
            self.user_token = login_with_user_credentials(
                email=config("ALTSCORE_EMAIL"),
                password=config("ALTSCORE_PASSWORD"),
                environment=self.environment,
                tenant=self.tenant
            )
        elif isinstance(self._refresh_token, str):
            try:
                self.user_token, self._refresh_token = refresh_api_token(
                    refresh_token=self._refresh_token,
                    environment=self.environment,
                    tenant=self.tenant
                )
            # If the refresh token is invalid, we need to re-authenticate
            except:
                logger.info("Refresh token invalid, re-authenticating, make sure ALTSCORE_CLIENT_ID and "
                            "ALTSCORE_CLIENT_SECRET are set as environment variables")
                self.auth(
                    client_id=config("ALTSCORE_CLIENT_ID"),
                    client_secret=config("ALTSCORE_CLIENT_SECRET")
                )
        else:
            raise ValueError("Authentication error, "
                             "refresh token not found")

    def __repr__(self):
        return f"AltScore({self.tenant}, {self.environment})"

    @property
    def _altdata_base_url(self):
        return "https://data.altscore.ai"

    @property
    def _borrower_central_base_url(self):
        if self.environment == "production":
            return "https://bc.altscore.ai"
        elif self.environment == "staging":
            return "https://borrower-central-staging-zosvdgvuuq-uc.a.run.app"
        elif self.environment == "sandbox":
            return "https://bc.sandbox.altscore.ai"
        elif self.environment == "local":
            return config("ALTSCORE_LOCAL_BC_URL", None)
        else:
            raise ValueError(f"Unknown environment: {self.environment}")

    @property
    def _cms_base_url(self):
        if self.environment == "production":
            return "https://api.altscore.ai"
        elif self.environment == "staging":
            return "https://api.stg.altscore.ai"
        elif self.environment == "sandbox":
            return "https://api.sandbox.altscore.ai"
        elif self.environment == "local":
            return config("ALTSCORE_LOCAL_CMS_URL", None)
        else:
            raise ValueError(f"Unknown environment: {self.environment}")

    @property
    def _webhooks_base_url(self):
        if self.environment == "production":
            return "https://api.altscore.ai"
        elif self.environment == "staging":
            return "https://api.stg.altscore.ai"
        elif self.environment == "sandbox":
            return "https://api.sandbox.altscore.ai"
        elif self.environment == "local":
            return config("ALTSCORE_LOCAL_CMS_URL", None)
        else:
            raise ValueError(f"Unknown environment: {self.environment}")

    def get_tenant_from_token(self) -> str:
        return jwt.decode(
            self.user_token,
            options={"verify_signature": False}
        )["tenantId"]


class AltScore(AltScoreBase):
    _async_mode = False

    def __init__(self, tenant: str = "default", environment: str = "production",
                 api_key: str = None, user_token: Optional[str] = None,
                 email: Optional[str] = None, password: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 form_token: Optional[str] = None, partner_id: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            tenant=tenant,
            environment=environment,
            user_token=user_token,
            form_token=form_token,
            email=email,
            password=password,
            client_id=client_id,
            client_secret=client_secret,
            partner_id=partner_id)
        self.borrower_central = BorrowerCentralSync(self)
        self.altdata = AltDataSync(self)
        self.cms = CMSSync(self)
        self.macros = MacrosSync(self)
        self.comms = CommsSync(self)

    @property
    def partner_id(self) -> Optional[str]:
        if self._partner_id is None:
            try:
                partner_id = self.cms.partners.me().data.partner_id
                self._partner_id = partner_id
            except:
                return None
        return self._partner_id


class AltScoreAsync(AltScoreBase):
    _async_mode = True

    def __init__(self, tenant: str = "default", environment: str = "production",
                 api_key: str = None, user_token: Optional[str] = None,
                 email: Optional[str] = None, password: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 form_token: Optional[str] = None, partner_id: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            tenant=tenant,
            environment=environment,
            user_token=user_token,
            form_token=form_token,
            email=email,
            password=password,
            client_id=client_id,
            client_secret=client_secret,
            partner_id=partner_id)
        self.borrower_central = BorrowerCentralAsync(self)
        self.altdata = AltDataAsync(self)
        self.cms = CMSAsync(self)
        self.macros = MacrosAsync(self)
        self.comss = CommsAsync(self)

    @property
    def partner_id(self) -> Optional[str]:
        if self._partner_id is None:
            try:
                partner_id = asyncio.run(self.cms.partners.me())
                self._partner_id = partner_id.data.partner_id
            except:
                return None
        return self._partner_id


def borrower_sign_up_with_form(
        persona: str,
        template_slug: str,
        tenant: str,
        environment: str = "production",
        async_mode: bool = False
) -> (Union[AltScore, AltScoreAsync], str, str, str):
    client = AltScore(tenant=tenant, environment=environment)
    form_id = client.borrower_central.forms.create({
        "templateSlug": template_slug,
        "tenant": tenant
    })
    new_borrower = client.borrower_central.forms.command_borrower_sign_up(
        {
            "formId": form_id,
            "tenant": tenant,
            "persona": persona
        }
    )
    if async_mode:
        altscore_module = AltScoreAsync(
            form_token=new_borrower.form_token,
            tenant=tenant,
            environment=environment,
        )
    else:
        altscore_module = AltScore(
            form_token=new_borrower.form_token,
            tenant=tenant,
            environment=environment,
        )
    return altscore_module, new_borrower.borrower_id, form_id


def login_with_user_credentials(
        email: str, password: str, environment: str, tenant: str = "default"
) -> str:
    auth_urls = {
        "production": "https://auth.altscore.ai",
        "sandbox": "https://auth.sandbox.altscore.ai",
        "staging": "https://altscore-stg.us.frontegg.com",
        "local": config("ALTSCORE_LOCAL_AUTH_URL", None)
    }
    headers = {}
    if tenant != "default":
        headers["frontegg-tenant-id"] = tenant
    with httpx.Client() as client:
        response = client.post(
            url=f"{auth_urls[environment]}/identity/resources/auth/v1/user",
            data={
                "email": email,
                "password": password
            }
        )
        raise_for_status_improved(response)
        data = response.json()
        return data["accessToken"]


def login_with_client_credentials(
        client_id: str, client_secret: str, environment: str, tenant: str = "default"
) -> (str, str):
    auth_urls = {
        "production": "https://auth.altscore.ai",
        "sandbox": "https://auth.sandbox.altscore.ai",
        "staging": "https://altscore-stg.us.frontegg.com",
        "local": config("ALTSCORE_LOCAL_AUTH_URL", None)
    }
    headers = {}
    if tenant != "default":
        headers["frontegg-tenant-id"] = tenant
    with httpx.Client() as client:
        response = client.post(
            url=f"{auth_urls[environment]}/identity/resources/auth/v1/api-token",
            data={
                "clientId": client_id,
                "secret": client_secret
            }
        )
        raise_for_status_improved(response)
        data = response.json()
        return data["accessToken"], data["refreshToken"]


def refresh_api_token(
        refresh_token: str, environment: str, tenant: str = "default"
) -> (str, str):
    auth_urls = {
        "production": "https://auth.altscore.ai",
        "sandbox": "https://auth.sandbox.altscore.ai",
        "staging": "https://altscore-stg.us.frontegg.com",
        "local": config("ALTSCORE_LOCAL_AUTH_URL", None)
    }
    headers = {}
    if tenant != "default":
        headers["frontegg-tenant-id"] = tenant
    with httpx.Client() as client:
        response = client.post(
            url=f"{auth_urls[environment]}/identity/resources/auth/v2/api-token/token/refresh",
            data={
                "refreshToken": refresh_token,
            }
        )
        raise_for_status_improved(response)
        data = response.json()
        return data["access_token"], data["refresh_token"]
