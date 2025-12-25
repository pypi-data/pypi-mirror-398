from pydantic import ValidationError
from altscore.borrower_central.model.identities import CreateIdentityDTO
from altscore.borrower_central.model.borrower_fields import CreateBorrowerFieldDTO
from altscore.borrower_central.model.attachments import AttachmentInput
from altscore.borrower_central.model.addresses import CreateAddressDTO
from altscore.borrower_central.model.points_of_contact import CreatePointOfContactDTO
from altscore.borrower_central.model.documents import CreateDocumentDTO
from altscore.borrower_central.model.authorizations import CreateAuthorizationDTO
import copy


def validate_borrower_data(borrower_data: dict):
    # Do not modify the original data
    borrower_data_copy = copy.deepcopy(borrower_data)
    if borrower_data_copy.get("persona") is None:
        raise ValueError("Missing persona key")
    root_identities = [k for k in borrower_data_copy.keys() if k.startswith("identity.")]
    malformed_identities = [k for k in root_identities if len(k.split(".")[-1]) == 0]
    root_borrower_fields = [k for k in borrower_data_copy.keys() if k.startswith("borrower_field.")]
    malformed_fields = [k for k in root_borrower_fields if len(k.split(".")[-1]) == 0]
    if len(malformed_fields + malformed_identities) > 0:
        raise ValueError(f"Found malformed keys: {malformed_fields + malformed_identities}")
    validate_many_against_model(
        entity="identity", data=borrower_data_copy.get("identities", []), model=CreateIdentityDTO
    )
    validate_many_against_model(
        entity="borrower_field", data=borrower_data_copy.get("borrower_fields", []), model=CreateBorrowerFieldDTO
    )
    validate_many_against_model(
        entity="address", data=borrower_data_copy.get("addresses", []), model=CreateAddressDTO
    )
    validate_many_against_model(
        entity="point_of_contact", data=borrower_data_copy.get("points_of_contact", []), model=CreatePointOfContactDTO
    )
    validate_many_against_model(
        entity="document", data=borrower_data_copy.get("documents", []), model=CreateDocumentDTO
    )
    validate_many_against_model(
        entity="authorization", data=borrower_data_copy.get("authorizations", []), model=CreateAuthorizationDTO
    )
    return set(root_identities), set(root_borrower_fields)


def validate_many_against_model(entity: str, data: list[dict], model):
    for item in data:
        validate_against_model(entity=entity, data=item, model=model)
        if len(item.get("attachments", [])) > 0:
            for attachment in item["attachments"]:
                validate_against_model(entity=entity, data=attachment, model=AttachmentInput)


def validate_against_model(entity: str, data: dict, model):
    try:
        # we inject a dummie borrower_id to avoid validation errors because its going to be
        # created at execution time
        data["borrowerId"] = "dummy"
        model.parse_obj(data)
    except ValidationError as e:
        pretty_errors = _format_pydantic_errors(e)
        formatted_error_message = f"Validation error on {entity}:\n" + pretty_errors
        raise ValueError(formatted_error_message)


def _format_pydantic_errors(validation_error: ValidationError) -> str:
    """Formats Pydantic ValidationError details into a more readable string."""
    errors = validation_error.errors()
    pretty_errors_list = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
    return "\n".join(pretty_errors_list)
