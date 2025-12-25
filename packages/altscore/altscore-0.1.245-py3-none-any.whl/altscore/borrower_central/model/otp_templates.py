from pydantic import BaseModel, Field
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from typing import Optional, Dict


class OTPTemplateAPIDTO(BaseModel):
    id: str = Field(alias="id")
    channel: str = Field(alias="channel")
    label: str = Field(alias="label")
    lang: Optional[str] = Field(alias="lang")
    sender: Optional[str] = Field(alias="sender")
    subject: Optional[str] = Field(alias="subject")
    title: Optional[str] = Field(alias="title")
    header_logo: Optional[str] = Field(alias="headerLogo")
    header_logo_height: Optional[str] = Field(alias="headerLogoHeight", default="40px")
    pre_otp_blurb: Optional[str] = Field(alias="preOtpBlurb")
    pos_otp_blurb: Optional[str] = Field(alias="posOtpBlurb")
    did_not_ask_message: Optional[str] = Field(alias="didNotAskMessage")
    footer_blurb: Optional[str] = Field(alias="footerBlurb")
    footer_link: Optional[str] = Field(alias="footerLink")
    footer_link_label: Optional[str] = Field(alias="footerLinkLabel")
    footer_slogan: Optional[str] = Field(alias="footerSlogan")
    footer_logo: Optional[str] = Field(alias="footerLogo")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateOTPTemplateDTO(BaseModel):
    channel: str = Field(alias="channel")
    label: str = Field(alias="label")
    lang: Optional[str] = Field(alias="lang")
    sender: Optional[str] = Field(alias="sender")
    subject: Optional[str] = Field(alias="subject")
    title: Optional[str] = Field(alias="title")
    header_logo: Optional[str] = Field(alias="headerLogo")
    header_logo_height: Optional[str] = Field(alias="headerLogoHeight", default="40px")
    pre_otp_blurb: Optional[str] = Field(alias="preOtpBlurb")
    pos_otp_blurb: Optional[str] = Field(alias="posOtpBlurb")
    did_not_ask_message: Optional[str] = Field(alias="didNotAskMessage")
    footer_blurb: Optional[str] = Field(alias="footerBlurb")
    footer_link: Optional[str] = Field(alias="footerLink")
    footer_link_label: Optional[str] = Field(alias="footerLinkLabel")
    footer_slogan: Optional[str] = Field(alias="footerSlogan")
    footer_logo: Optional[str] = Field(alias="footerLogo")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class OTPTemplatesSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "otp-templates",header_builder, renew_token, OTPTemplateAPIDTO.parse_obj(data))


class OTPTemplatesAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "otp-templates",header_builder, renew_token, OTPTemplateAPIDTO.parse_obj(data))


class OTPTemplatesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=OTPTemplatesSync,
                         retrieve_data_model=OTPTemplateAPIDTO,
                         create_data_model=CreateOTPTemplateDTO,
                         update_data_model=CreateOTPTemplateDTO,
                         resource="otp-templates")


class OTPTemplatesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=OTPTemplatesAsync,
                         retrieve_data_model=OTPTemplateAPIDTO,
                         create_data_model=CreateOTPTemplateDTO,
                         update_data_model=CreateOTPTemplateDTO,
                         resource="otp-templates")
