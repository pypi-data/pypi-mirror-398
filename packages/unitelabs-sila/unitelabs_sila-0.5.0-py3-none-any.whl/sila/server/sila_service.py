# ruff: noqa: ARG002

import dataclasses

from ..framework import (
    Constrained,
    DefinedExecutionError,
    Element,
    Feature,
    FeatureIdentifier,
    FullyQualifiedIdentifier,
    Length,
    List,
    MaximalLength,
    Metadata,
    Pattern,
    Schema,
    Serializer,
    String,
)
from .server import Server
from .unobservable_command import UnobservableCommand
from .unobservable_property import UnobservableProperty

UnimplementedFeature = DefinedExecutionError.create(
    identifier="UnimplementedFeature",
    display_name="Unimplemented Feature",
    description="The Feature specified by the given Feature identifier is not implemented by the server.",
)


@dataclasses.dataclass
class SiLAService(Feature):
    """
    This Feature MUST be implemented by each SiLA Server.

    It specifies Commands and Properties to discover the Features a SiLA Server implements as well as details
    about the SiLA Server, like name, type, description, vendor and UUID.

    Any interaction described in this feature MUST not affect the behaviour of any other Feature.
    """

    sila2_version: str = "1.0"
    version: str = "1.0"
    maturity_level: str = "Normative"
    originator: str = "org.silastandard"
    category: str = "core"
    identifier: str = "SiLAService"
    display_name: str = "SiLA Service"
    description: str = (
        "This Feature MUST be implemented by each SiLA Server.\n\n"
        "It specifies Commands and Properties to discover the Features a SiLA Server implements as well as details"
        "about the SiLA Server, like name, type, description, vendor and UUID.\n\n"
        "Any interaction described in this feature MUST not affect the behaviour of any other Feature."
    )

    def __post_init__(self):
        UnobservableCommand(
            identifier="GetFeatureDefinition",
            display_name="Get Feature Definition",
            description=(
                "Get the Feature Definition of an implemented Feature by its fully qualified Feature Identifier. "
                "This command has no preconditions and no further dependencies and can be called at any time."
            ),
            parameters={
                "feature_identifier": Element(
                    identifier="FeatureIdentifier",
                    display_name="Feature Identifier",
                    description=(
                        "The fully qualified Feature identifier for which the Feature definition shall be retrieved."
                    ),
                    data_type=Constrained.create(
                        data_type=String,
                        constraints=[FullyQualifiedIdentifier(FullyQualifiedIdentifier.Type.FEATURE_IDENTIFIER)],
                    ),
                ),
            },
            responses={
                "FeatureDefinition": Element(
                    identifier="FeatureDefinition",
                    display_name="Feature Definition",
                    description="The Feature definition in XML format (according to the Feature Definition Schema).",
                    data_type=Constrained.create(
                        data_type=String,
                        constraints=[
                            Schema(
                                type=Schema.Type.XML,
                                url="https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd",
                            )
                        ],
                    ),
                ),
            },
            errors={UnimplementedFeature.identifier: UnimplementedFeature},
            function=self.get_feature_definition,
            feature=self,
        )

        UnobservableCommand(
            identifier="SetServerName",
            display_name="Set Server Name",
            description=(
                "Sets a human readable name to the Server Name Property. Command has no preconditions and "
                "no further dependencies and can be called at any time."
            ),
            parameters={
                "server_name": Element(
                    identifier="ServerName",
                    display_name="Server Name",
                    description="The human readable name to assign to the SiLA Server.",
                    data_type=Constrained.create(data_type=String, constraints=[MaximalLength(255)]),
                ),
            },
            function=self.set_server_name,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerName",
            display_name="Server Name",
            description=(
                "Human readable name of the SiLA Server. The name can be set using the 'Set Server Name' command."
            ),
            data_type=Constrained.create(String, [MaximalLength(255)]),
            function=self.get_server_name,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerType",
            display_name="Server Type",
            description=(
                "The type of this server. It, could be, e.g., in the case of a SiLA Device the model name. "
                "It is specified by the implementer of the SiLA Server and MAY not be unique."
            ),
            data_type=Constrained.create(String, [Pattern(r"[A-Z][a-zA-Z0-9]*")]),
            function=self.get_server_type,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerUUID",
            display_name="Server UUID",
            description=(
                "Globally unique identifier that identifies a SiLA Server. The Server UUID MUST be generated once "
                "and remain the same for all times."
            ),
            data_type=Constrained.create(
                String,
                [Length(36), Pattern(r"[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}")],
            ),
            function=self.get_server_uuid,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerDescription",
            display_name="Server Description",
            description="Description of the SiLA Server. This should include the use and purpose of this SiLA Server.",
            data_type=String,
            function=self.get_server_description,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerVersion",
            display_name="Server Version",
            description=(
                'Returns the version of the SiLA Server. A "Major" and a "Minor" version number (e.g. 1.0) MUST '
                "be provided, a Patch version number MAY be provided. Optionally, an arbitrary text, separated by "
                'an underscore MAY be appended, e.g. "3.19.373_mighty_lab_devices".'
            ),
            data_type=Constrained.create(
                String, [Pattern(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?(_[_a-zA-Z0-9]+)?")]
            ),
            function=self.get_server_version,
            feature=self,
        )

        UnobservableProperty(
            identifier="ServerVendorURL",
            display_name="Server Vendor URL",
            description=(
                "Returns the URL to the website of the vendor or the website of the product of this SiLA Server. "
                "This URL SHOULD be accessible at all times.\n"
                "The URL is a Uniform Resource Locator as defined in RFC 1738."
            ),
            data_type=Constrained.create(String, [Pattern(r"https?://.+")]),
            function=self.get_vendor_url,
            feature=self,
        )

        UnobservableProperty(
            identifier="ImplementedFeatures",
            display_name="Implemented Features",
            description=(
                "Returns a list of fully qualified Feature identifiers of all implemented Features of this "
                "SiLA Server. This list SHOULD remain the same throughout the lifetime of the SiLA Server."
            ),
            data_type=List.create(
                data_type=Constrained.create(
                    data_type=String,
                    constraints=[FullyQualifiedIdentifier(FullyQualifiedIdentifier.Type.FEATURE_IDENTIFIER)],
                ),
            ),
            function=self.get_implemented_features,
            feature=self,
        )

    async def get_server_name(self, *, metadata: Metadata) -> dict[str, str]:
        """Human readable name of the SiLA Server. The name can be set using the 'Set Server Name' command."""
        assert isinstance(self.context, Server)

        return {"ServerName": self.context.name}

    def set_server_name(self, server_name: str, *, metadata: Metadata) -> None:
        """
        Set a human readable name to the Server Name Property.

        Command has no preconditions and no further dependencies and can be called at any time.
        """

        assert isinstance(self.context, Server)

        self.context.name = server_name

    async def get_server_type(self, *, metadata: Metadata) -> dict[str, str]:
        """
        Get the type of this server.

        It, could be, e.g., in the case of a SiLA Device the model name.
        It is specified by the implementer of the SiLA Server and MAY not be unique.
        """

        assert isinstance(self.context, Server)

        return {"ServerType": self.context.type}

    async def get_server_uuid(self, *, metadata: Metadata) -> dict[str, str]:
        """
        Globally unique identifier that identifies a SiLA Server.

        The Server UUID MUST be generated once and remain the same for all times.
        """

        assert isinstance(self.context, Server)

        return {"ServerUUID": self.context.uuid}

    async def get_server_description(self, *, metadata: Metadata) -> dict[str, str]:
        """
        Get the description of the SiLA Server.

        This should include the use and purpose of this SiLA Server.
        """

        assert isinstance(self.context, Server)

        return {"ServerDescription": self.context.description}

    async def get_server_version(self, *, metadata: Metadata) -> dict[str, str]:
        """
        Return the version of the SiLA Server.

        A "Major" and a "Minor" version number (e.g. 1.0) MUST
        be provided, a Patch version number MAY be provided. Optionally, an arbitrary text, separated by
        an underscore MAY be appended, e.g. "3.19.373_mighty_lab_devices".
        """

        assert isinstance(self.context, Server)

        return {"ServerVersion": self.context.version}

    async def get_vendor_url(self, *, metadata: Metadata) -> dict[str, str]:
        """
        Get the URL to the website of the vendor or the website of the product of this SiLA Server.

        This URL SHOULD be accessible at all times.

        The URL is a Uniform Resource Locator as defined in RFC 1738.
        """

        assert isinstance(self.context, Server)

        return {"ServerVendorURL": self.context.vendor_url}

    async def get_implemented_features(self, *, metadata: Metadata) -> dict[str, list[str]]:
        """
        Return a list of fully qualified Feature identifiers of all implemented Features of this SiLA Server.

        This list SHOULD remain the same throughout the lifetime of the SiLA Server.
        """

        return {"ImplementedFeatures": list(self.context.features)}

    async def get_feature_definition(self, feature_identifier: str, *, metadata: Metadata) -> dict[str, str]:
        """
        Get the Feature Definition of an implemented Feature by its fully qualified Feature Identifier.

        This command has no preconditions and no further dependencies and can be called at any time.
        """

        identifier = FeatureIdentifier(feature_identifier)

        if identifier not in self.context.features:
            raise UnimplementedFeature

        feature = self.context.features[identifier]

        serializer = Serializer()
        feature.serialize(serializer)

        return {"FeatureDefinition": serializer.buffer.getvalue()}
