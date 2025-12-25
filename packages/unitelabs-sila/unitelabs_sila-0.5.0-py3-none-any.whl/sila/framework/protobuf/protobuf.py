import grpc
import typing_extensions as typing

if typing.TYPE_CHECKING:
    from ..common import Context
    from ..data_types import Element, Native, Structure


class Protobuf:
    """
    A collection of protobuf messages and services.

    Args:
      context: The context for this protobuf collection.
    """

    def __init__(self, context: "Context") -> None:
        self.__context = context
        self.__messages: dict[str, type["Structure"]] = {}
        self.__services: dict[str, dict[str, grpc.RpcMethodHandler]] = {}

    @property
    def messages(self) -> dict[str, type["Structure"]]:
        """Receive all protobuf messages registered in this collection."""

        return self.__messages

    @property
    def services(self) -> dict[str, dict[str, grpc.RpcMethodHandler]]:
        """Receive all protobuf services registered in this collection."""

        return self.__services

    def get_message(self, path: str, /) -> type["Structure"]:
        """
        Receive a protobuf message from the collection of registered messages.

        Args:
          path: The complete path of the registered message including its
            package and name.

        Returns:
          The registered protobuf message.

        Raises:
          ValueError: If no message is registered under the given path.
        """

        try:
            return self.__messages[path]
        except KeyError:
            msg = f"Could not find any message registered under the given path '{path}'."
            raise ValueError(msg) from None

    @typing.overload
    def register_message(
        self, /, *, message: type["Structure"], package: typing.Optional[str] = None
    ) -> type["Structure"]:
        """
        Register a protobuf message in the optional package.

        Overrides previously registered messages with the same package
        and name combination.

        Args:
          message: The protobuf message to register.
          package: The package name to register the message under.

        Returns:
          The registered protobuf message.
        """

    @typing.overload
    def register_message(
        self,
        /,
        *,
        message: dict[str, "Element"],
        package: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ) -> type["Structure"]:
        """
        Register a protobuf message with the given name in the optional package.

        Overrides previously registered messages with the same package
        and name combination.

        Args:
          message: The protobuf message to register.
          package: The package name to register the message under.
          name: The name of the protobuf message to register.
          description: An optional description of the protobuf message.

        Returns:
          The registered protobuf message.
        """

    def register_message(  # noqa: D102
        self,
        /,
        *,
        message: typing.Union[type["Structure"], dict[str, "Element"]],
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        package: typing.Optional[str] = None,
    ) -> type["Structure"]:
        from ..data_types import Structure

        if not isinstance(message, dict):
            name = message.__name__

        name = name or "Structure"
        if isinstance(message, dict):
            message = Structure.create(name=name, description=description, elements=message)

        path = f"{package}.{name}" if package is not None else name
        self.__messages[path] = message

        return message

    def register_service(
        self,
        /,
        name: str,
        service: dict[str, grpc.RpcMethodHandler],
        *,
        package: typing.Optional[str] = None,
        force: bool = False,
    ) -> dict[str, grpc.RpcMethodHandler]:
        """
        Register a protobuf service with the given name in the optional package.

        If a service with the same package and name combination already
        exists, the methods of both services are merged and the merged
        service is registered. Methods with the same name override
        previously registered methods. Use the `force` flag to completely
        replace existing services.

        Args:
          name: The name of the protobuf service to register.
          service: The protobuf service to register containing the
            available methods.
          package: The package name to register the service under.
          force: Set True to completely replace any existing service with
            the same package and name combination and prevent merging.

        Returns:
          The registered protobuf service with its methods.
        """

        path = f"{package}.{name}" if package is not None else name

        if not force:
            service = self.__services.get(path, {}) | service

        self.__services[path] = service

        return service

    async def decode(self, path: str, buffer: bytes) -> dict[str, "Native"]:
        """
        Use a registered message to decode a byte stream into a python dictionary.

        Args:
          path: The path of the registered message used for decoding.
          buffer: The byte stream to decode.

        Returns:
          The decoded message as a dictionary.

        Raises:
          ValueError: If no message is registered under the given path.
          DecodeError: If there was an error while decoding the message.
          ConversionError: If there was an error while converting the
            message to its native python format.
        """

        data_type = self.get_message(path)
        data_value = data_type.decode(buffer)
        return await data_value.to_native(self.__context)

    async def encode(self, path: str, value: dict[str, "Native"]) -> bytes:
        """
        Use a registered message to encode a python dictionary into a byte stream.

        Args:
          path: The path of the registered message used for encoding.
          value: The python dictionary to encode.

        Returns:
          The encoded message as a byte stream.

        Raises:
          ValueError: If no message is registered under the given path.
          EncodeError: If there was an error while encoding the message.
          ConversionError: If there was an error while converting the
            message from its native python format.
        """

        data_type = self.get_message(path)
        data_value = await data_type.from_native(self.__context, value)
        return data_value.encode()

    def merge(self, protobuf: "Protobuf") -> None:
        """
        Merge another collection of protobuf messages and services in place.

        Args:
          protobuf: The other protobuf messages and services to merge.
        """

        self.__messages.update(protobuf.__messages)
        for path, service in protobuf.__services.items():
            self.__services[path] = self.__services.get(path, {}) | service
