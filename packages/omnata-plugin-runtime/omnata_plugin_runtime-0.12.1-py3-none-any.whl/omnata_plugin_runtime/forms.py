"""
Contains form elements for Omnata plugin configuration
"""
from __future__ import annotations
import sys
from typing import List, Callable, Literal, Union, ForwardRef, Optional

if tuple(sys.version_info[:2]) >= (3, 9):
    # Python 3.9 and above
    from typing import Annotated
else:
    # Python 3.8 and below
    from typing_extensions import Annotated
from abc import ABC
from types import MethodType
from pydantic import BaseModel, Field, field_validator  # pylint: disable=no-name-in-module
from .configuration import (
    SubscriptableBaseModel,
    NgrokTunnelSettings,
    SyncConfigurationParameters,
    ConnectionConfigurationParameters,
    StoredConfigurationValue,
)


class FormOption(SubscriptableBaseModel):
    """
    An option used by certain form forms (like Dropdowns).

    :param str value: The value to set in the field if this option is selected
    :param str label: The label to show in the list. This value is not stored.
    :param dict metadata: An arbitrary dictionary to store with the value, which can be retrieved by the plugin
    :param bool required: When populating field mapping options, this flag indicates that this field is mandatory
    :param bool unique: When populating field mapping options, this flag indicates that this field requires a unique value (i.e. be mapped from a unique column)
    :param bool default: Indicates that this option should be the default selected
    :param bool disabled: Indicates that the option should appear in the list, but be unselectable
    :param str data_type_icon: The data type icon to show next to the option (where applicable)
    :return: nothing
    """

    value: str
    label: str
    metadata: dict = Field(default_factory=dict)
    required: bool = Field(default=False)
    unique: bool = Field(default=False)
    default: bool = Field(default=False)
    disabled: bool = Field(default=False)
    data_type_icon: str = "unknown"


class FormInputField(SubscriptableBaseModel):
    """
    An input field, which collects a single line of free-form text from the user and no metadata.
    """

    name: str
    label: str
    default_value: Union[str, bool] = Field(default="")
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    secret: bool = Field(default=False)
    type: Literal["input"] = "input"


class FormTextAreaField(SubscriptableBaseModel):
    """
    A text area field, which collects multi-line free-form text from the user and no metadata.

    :param str name: The name of the form field. This value must be unique, and is used to retrieve the value from within the plugin code.
    :param str label: The label for the form field
    :param str default_value: The default value presented initially in the field
    :param bool required: If True, means that the form cannot be submitted without a value present
    :param str depends_on: The name of another form field. If provided, this form field will not be rendered until there is a value in the field it depends on.
    :param str help_text: A longer description of what the field is used for. If provided, a help icon is shown and must be hovered over to display this text.
    :param bool secret: Indicates that the text entered must be masked in the browser, and stored/access securely
    :param bool reload_on_change: If True, the entire form is reloaded after the value is changed. This is used to conditionally render fields based on values provided in others, but should be used only when strictly necessary.
    :return: nothing
    """

    name: str
    label: str
    default_value: str = Field(default="")
    secret: bool = Field(default=False)
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    type: Literal["textarea"] = "textarea"

    variables: bool = Field(default=False)

class InformationField(SubscriptableBaseModel):
    """
    A field which allows information to be displayed to the user in plain markdown, but not edited.

    :param str name: The name of the form field. This value must be unique.
    :param str markdown_content: The markdown to include.
    :return: nothing
    """
    name: str
    markdown_content: str
    depends_on: Optional[str] = Field(default=None)
    type: Literal["information"] = "information"
    reload_on_change: bool = Field(default=False)
    secret: bool = Field(default=False)

class InformationBoxField(SubscriptableBaseModel):
    """
    A field which allows information to be displayed to the user, but not edited.
    This variant renders it inside a box, with an icon and a different background colour.

    :param str name: The name of the form field. This value must be unique.
    :param str markdown_content: The markdown to include.
    :param str box_type: The type of box to render. One of "info", "warning", "error"
    :param str box_icon: The name of the icon to render in the box. If not provided, no icon will be used.
    :return: nothing
    """
    name: str
    markdown_content: str
    depends_on: Optional[str] = Field(default=None)
    type: Literal["information_box"] = "information_box"
    reload_on_change: bool = Field(default=False)
    box_type: Literal["info", "warning", "error"] = "info"
    box_icon: Optional[str] = Field(default=None)
    secret: bool = Field(default=False)

class FormSshKeypair(SubscriptableBaseModel):
    """
    An SSH Keypair field, which generates public and private keys for asymmetric cryptography.
    """
    name: str
    label: str
    default_value: Optional[str] = Field(default=None)
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    local_side: Literal["public", "private"] = "public"
    """
    The side of the keypair which belongs to Snowflake. This value will be stored as the secret value, and the other side
    can be copied/downloaded only during the connection process.
    """
    allow_user_provided: bool = Field(default=True)
    """
    Allows the user to provide Snowflake's side of the keypair, for cases where one is generated on the outside
    """
    type: Literal["ssh_keypair"] = "ssh_keypair"
    secret: bool = Field(default=True)

class FormX509Certificate(SubscriptableBaseModel):
    """
    An X509 certificate in PEM format.
    Like a textarea field, except it decodes and shows information about the certificate.
    """
    name: str
    label: str
    default_value: Optional[str] = Field(default=None)
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    type: Literal["x509_certificate"] = "x509_certificate"
    secret: bool = Field(default=True)

class FormGpgKeypair(SubscriptableBaseModel):
    """
    An GPG Keypair field, which generates public and private GPG keys for asymmetric cryptography.
    """

    name: str
    label: str
    default_value: Optional[str] = Field(default=None)
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    local_side: Literal["public", "private"] = "public"
    """
    The side of the keypair which belongs to Snowflake. This value will be stored as the secret value, and the other side
    can be copied/downloaded only during the connection process.
    """
    allow_user_provided: bool = Field(default=True)
    """
    Allows the user to provide Snowflake's side of the keypair, for cases where one is generated on the outside
    """
    type: Literal["gpg_keypair"] = "gpg_keypair"
    secret: bool = Field(default=True)


class FormCheckboxField(SubscriptableBaseModel):
    """
    A field which presents a checkbox
    """

    name: str
    label: str
    default_value: bool = Field(default=False)
    required: bool = Field(default=False)
    secret: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    type: Literal["checkbox"] = "checkbox"


class FormSliderField(SubscriptableBaseModel):
    """
    A field which presents a slider
    """

    name: str
    label: str
    default_value: Optional[Union[str,int]] = Field(default=None)
    secret: bool = Field(default=False)
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    type: Literal["slider"] = "slider"

    min_value: int = Field(default=0)
    max_value: int = Field(default=100)
    step_size: int = Field(default=1)


class FormSnowflakeStageField(SubscriptableBaseModel):
    """
    A field which represents a stage which can be selected from a list shared to the plugin.
    """

    name: str
    label: str
    default_value: Union[str, bool] = Field(default="")
    required: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    secret: bool = Field(default=False)
    type: Literal["snowflake_stage"] = "snowflake_stage"


class FormJinjaTemplate(SubscriptableBaseModel):
    """
    Uses text area to allow the user to create a template, which can include column values from the source
    """

    mapper_type: Literal["jinja_template"] = "jinja_template"
    label: str = "Jinja Template"
    depends_on: Optional[str] = Field(default=None)


# ----------------------------------------------------------------------------
# Everything above here has no dependencies on other BaseModels in this module
# ----------------------------------------------------------------------------

NewOptionCreator = ForwardRef("NewOptionCreator")  # type: ignore


class StaticFormOptionsDataSource(SubscriptableBaseModel):
    """
    A Data Source for providing a static set of form options

    :param List[FormOption] values: The list of values to return
    :param NewOptionCreator new_option_creator: If provided, it means that values can be added to the datasource via the provided mechanism
    :return: nothing
    """

    values: List[FormOption] = Field(default_factory=list)
    new_option_creator: Optional[NewOptionCreator] = Field(default=None)
    type: Literal["static"] = "static"


class DynamicFormOptionsDataSource(SubscriptableBaseModel):
    """
    A Data Source for providing a set of form options that load dynamically from the server
    """

    source_function: Union[
        Callable[[SyncConfigurationParameters], List[FormOption]], str
    ]
    new_option_creator: Optional[NewOptionCreator] = Field(default=None)
    type: Literal["dynamic"] = "dynamic"

    @field_validator("source_function", mode='after')
    @classmethod
    def function_name_convertor(cls, v) -> str:
        return v.__name__ if isinstance(v, MethodType) else v


FormOptionsDataSourceBase = Annotated[
    Union[StaticFormOptionsDataSource, DynamicFormOptionsDataSource],
    Field(discriminator="type"),
]


class FormFieldWithDataSource(SubscriptableBaseModel):
    """
    Denotes that the field uses a data source
    """

    data_source: FormOptionsDataSourceBase


class FormRadioField(FormFieldWithDataSource, BaseModel):
    """
    A field which presents a set of radio options
    :param str name: The name of the form field. This value must be unique, and is used to retrieve the value from within the plugin code.
    :param str label: The label for the form field
    :param FormOptionsDataSourceBase data_source provides the values for the radio group
    :param str default_value: The default value presented initially in the field
    :param bool required: If True, means that the form cannot be submitted without a value present
    :param str depends_on: The name of another form field. If provided, this form field will not be rendered until there is a value in the field it depends on.
    :param str help_text: A longer description of what the field is used for. If provided, a help icon is shown and must be hovered over to display this text.
    :param bool reload_on_change: If True, the entire form is reloaded after the value is changed. This is used to conditionally render fields based on values provided in others, but should be used only when strictly necessary.
    :return: nothing
    """

    name: str
    label: str
    default_value: Optional[str] = Field(default=None)
    required: bool = Field(default=False)
    secret: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    type: Literal["radio"] = "radio"


class FormDropdownField(FormFieldWithDataSource, BaseModel):
    """
    A field which presents a dropdown list of options

    """

    name: str
    label: str
    default_value: Optional[str] = Field(default=None)
    required: bool = Field(default=False)
    secret: bool = Field(default=False)
    depends_on: Optional[str] = Field(default=None)
    help_text: str = Field(default="")
    reload_on_change: bool = Field(default=False)
    type: Literal["dropdown"] = "dropdown"

    multi_select: bool = Field(default=False)


FormFieldBase = Annotated[
    Union[
        FormInputField,
        FormTextAreaField,
        FormSshKeypair,
        FormX509Certificate,
        FormGpgKeypair,
        FormRadioField,
        FormCheckboxField,
        FormSliderField,
        FormDropdownField,
        InformationField,
        InformationBoxField,
        FormSnowflakeStageField
    ],
    Field(discriminator="type"),
]


class ConfigurationFormBase(BaseModel, ABC):
    """
    Defines a form for configuring a sync. Includes zero or more form fields.

    :param List[FormFieldBase] fields: A list of fields to display to the user
        :return: nothing
    """

    fields: List[FormFieldBase]


class NewOptionCreator(SubscriptableBaseModel):
    """
    Allows for options to be added to a datasource by the user.
    It does this by presenting the user with a form, then building a StoredConfigurationValue from the provided values.
    Since this StoredConfigurationValue won't be present in the data source (at least not initially), there is
    also a function (construct_form_option) to convert the StoredConfigurationValue into a FormOption which can be added to the data source.
    This means that all the presentation options (e.g. required, unique) must be derivable from the metadata in StoredConfigurationValue.
    """

    creation_form_function: Union[
        Callable[[SyncConfigurationParameters], ConfigurationFormBase], str
    ]
    creation_complete_function: Union[
        Callable[[SyncConfigurationParameters], StoredConfigurationValue], str
    ]
    construct_form_option: Union[
        Callable[[StoredConfigurationValue], FormOption], str
    ]
    allow_create: bool = Field(default=True)

    @field_validator("creation_form_function", mode='after')
    @classmethod
    def function_name_convertor(cls, v) -> str:
        return v.__name__ if isinstance(v, MethodType) else v

    @field_validator("creation_complete_function", mode='after')
    @classmethod
    def function_name_convertor_2(cls, v) -> str:
        return v.__name__ if isinstance(v, MethodType) else v
    
    @field_validator("construct_form_option", mode='after')
    @classmethod
    def function_name_convertor_3(cls, v) -> str:
        return v.__name__ if isinstance(v, MethodType) else v


StaticFormOptionsDataSource.model_rebuild()
DynamicFormOptionsDataSource.model_rebuild()


class FormFieldMappingSelector(FormFieldWithDataSource, BaseModel):
    """
    Uses a visual column->field mapper, to allow the user to define how source columns map to app fields

    :param FormOptionsDataSourceBase data_source: A data source which provides the app field options
    :param str depends_on: Provide the name of another field to make it dependant, so that the mapper won't display until a value has been provided
    :return: nothing
    """

    mapper_type: Literal["field_mapping_selector"] = "field_mapping_selector"
    label: str = "Field Mappings"
    depends_on: Optional[str] = Field(default=None)


Mapper = Annotated[
    Union[FormFieldMappingSelector, FormJinjaTemplate],
    Field(discriminator="mapper_type"),
]


class OutboundSyncConfigurationForm(ConfigurationFormBase):
    """
    Defines a form for configuring an outbound sync.
    Includes the zero or more form fields from the base class, and optionally a column->field mapper
    to map Snowflake columns to app fields/payloads.
    """

    mapper: Optional[Mapper] = Field(default=None)


class InboundSyncConfigurationForm(ConfigurationFormBase):
    """
    Defines a form for configuring an inbound sync, prior to stream selection.
    The form values provided via these fields are passed into the inbound_list_streams function.
    """

    fields: List[FormFieldBase] = Field(default_factory=list)

class SecurityIntegrationTemplateAuthorizationCode(BaseModel):
    """
    Provides values used to populate a security integration instructions template, which
    in turn allows the customer to create an OAuth based secret object
    """
    oauth_docs_url: Optional[str] = Field(default=None)
    oauth_grant: Literal["authorization_code"] = "authorization_code"
    oauth_client_id: str = Field(default='<client id>')
    oauth_client_secret: str = Field(default='<client secret>')
    oauth_token_endpoint: str = Field(default='<token endpoint>')
    oauth_authorization_endpoint: str = Field(default='<authorization endpoint>')
    oauth_allowed_scopes: List[str] = Field(default=[])

class SecurityIntegrationTemplateClientCredentials(BaseModel):
    """
    Provides values used to populate a security integration instructions template, which
    in turn allows the customer to create an OAuth based secret object
    """
    oauth_docs_url: Optional[str] = Field(default=None)
    oauth_grant: Literal["client_credentials"] = "client_credentials"
    oauth_client_id: str = Field(default='<client id>')
    oauth_client_secret: str = Field(default='<client secret>')
    oauth_token_endpoint: str = Field(default='<token endpoint>')
    oauth_allowed_scopes: List[str] = []

SecurityIntegrationTemplate = Annotated[
    Union[SecurityIntegrationTemplateAuthorizationCode, SecurityIntegrationTemplateClientCredentials],
    Field(discriminator="oauth_grant"),
]

class NGrokMTLSTunnel(SubscriptableBaseModel):
    """
    Designates a ConnectionMethod as connecting via an ngrok tunnel.
    """
    SupportEdgeTermination: bool = Field(default=True)
    post_tunnel_fields_function: Union[
        Callable[[ConnectionConfigurationParameters], List[FormFieldBase]], str
    ]
    @field_validator("post_tunnel_fields_function", mode='after')
    @classmethod
    def function_name_convertor(cls, v) -> str:
        return v.__name__ if isinstance(v, MethodType) else v

class ConnectionMethod(SubscriptableBaseModel):
    """
    Defines a method of connecting to an application.
    :param str data_source: The name of the connection method, e.g. "OAuth", "API Key", "Credentials"
    :param List[FormFieldBase] fields: A list of fields that are used to collect the connection information from the user.
    :param Optional[SecurityIntegrationTemplate] oauth_template: If provided, the user will be guided through the process
    of creating a security integration, followed by a secret and performing the OAuth flow. Once this secret is completed,
    the rest of the values from the form will be captured and then the connection will be tested.
    :param str description: A markdown description of the connection method, which will be displayed to the user.
        This should be concise as it will be displayed in a sidebar, but you can include a link to the connection section
        of the plugin's documentation.
    """

    name: str
    fields: List[FormFieldBase]
    oauth_template: Optional[SecurityIntegrationTemplate] = Field(default=None)
    # This is now deprecated, instead signal ngrok support via the plugin manifest
    ngrok_tunnel_configuration: Optional[NGrokMTLSTunnel] = Field(default=None)
    description: str = Field(default="")
