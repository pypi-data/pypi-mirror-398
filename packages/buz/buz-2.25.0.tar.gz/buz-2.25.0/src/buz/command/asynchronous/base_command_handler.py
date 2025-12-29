from typing import Generic, Type, TypeVar, cast, get_type_hints, Any

from buz.command import Command
from buz.command.asynchronous.command_handler import CommandHandler

TCommand = TypeVar("TCommand", bound=Command)


class BaseCommandHandler(Generic[TCommand], CommandHandler[TCommand]):
    @classmethod
    def fqn(cls) -> str:
        return f"command_handler.{cls.__module__}.{cls.__name__}"

    @classmethod
    def handles(cls) -> Type[TCommand]:
        handle_types = get_type_hints(cls.handle)

        t_command = handle_types.get("command")
        if t_command is None:
            raise TypeError(
                f"The method 'handle' in '{cls.fqn()}' doesn't have a parameter named 'command'. Found parameters: {cls.__get_method_parameter_names(handle_types)}"
            )

        # TypeVar mask the actual bound type
        if hasattr(t_command, "__bound__"):
            t_command = t_command.__bound__

        if not issubclass(t_command, Command):
            raise TypeError(f"The parameter 'command' in '{cls.fqn()}.handle' is not a 'buz.command.Command' subclass")

        return cast(Type[TCommand], t_command)

    @classmethod
    def __get_method_parameter_names(cls, handle_types: dict[str, Any]) -> list[str]:
        handle_types_copy: dict = handle_types.copy()
        handle_types_copy.pop("return", None)
        return list(handle_types_copy.keys())
