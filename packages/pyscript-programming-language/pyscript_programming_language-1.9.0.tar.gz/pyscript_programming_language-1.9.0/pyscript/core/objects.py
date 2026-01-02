from .bases import Pys
from .context import PysContext, PysClassContext
from .exceptions import PysTraceback, PysSignal
from .results import PysRunTimeResult
from .symtab import PysSymbolTable
from .utils.similarity import get_closest
from .utils.string import join

from types import MethodType

class PysObject(Pys):
    __slots__ = ()

class PysCode(PysObject):

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PysPythonFunction(PysObject):

    def __init__(self, func):
        from .handlers import handle_call  # circular import problem solved

        self.__name__ = getattr(func, '__name__', '<function>')
        self.__qualname__ = getattr(func, '__qualname__', '<function>')
        self.__doc__ = getattr(func, '__doc__', None)
        self.__func__ = func
        self.__code__ = PysCode(
            position=None,
            context=None,
            handle_call=handle_call
        )

    def __repr__(self):
        return f'<python function {self.__qualname__} at 0x{id(self):016X}>'

    def __get__(self, instance, owner):
        return self if instance is None else MethodType(self, instance)

    def __call__(self, *args, **kwargs):
        func = self.__func__
        code = self.__code__

        code.handle_call(func, code.context, code.position)
        return func(self, *args, **kwargs)

class PysBuiltinFunction(PysPythonFunction):

    def __repr__(self):
        return f'<built-in function {self.__qualname__}>'

class PysFunction(PysObject):

    def __init__(self, name, qualname, parameters, body, position, context):
        from .interpreter import visit  # circular import problem solved

        context = context.parent if isinstance(context, PysClassContext) else context

        self.__name__ = '<function>' if name is None else name
        self.__qualname__ = ('' if qualname is None else qualname + '.') + self.__name__
        self.__code__ = PysCode(
            parameters=parameters,
            body=body,
            position=position,
            context=context,
            visit=visit,
            call_context=context,
            parameters_length=len(parameters),
            argument_names=tuple(item for item in parameters if not isinstance(item, tuple)),
            keyword_argument_names=tuple(item[0] for item in parameters if isinstance(item, tuple)),
            parameter_names=tuple(item[0] if isinstance(item, tuple) else item for item in parameters),
            keyword_arguments={item[0]: item[1] for item in parameters if isinstance(item, tuple)}
        )

    def __repr__(self):
        return f'<function {self.__qualname__} at 0x{id(self):016X}>'

    def __get__(self, instance, owner):
        return self if instance is None else MethodType(self, instance)

    def __call__(self, *args, **kwargs):
        qualname = self.__qualname__
        code = self.__code__
        code_position = code.position
        code_context = code.context
        code_call_context = code.call_context
        code_parameters_length = code.parameters_length
        code_parameter_names = code.parameter_names
        arguments_length = len(args)

        result = PysRunTimeResult()
        symbol_table = PysSymbolTable(code_context.symbol_table)
        registered_arguments = set()

        add_argument = registered_arguments.add
        set_symbol = symbol_table.set

        for name, arg in zip(code.argument_names, args):
            set_symbol(name, arg)
            add_argument(name)

        combined_keyword_arguments = code.keyword_arguments | kwargs
        pop_keyword_arguments = combined_keyword_arguments.pop

        for name, arg in zip(code.keyword_argument_names, args[len(registered_arguments):]):
            set_symbol(name, arg)
            add_argument(name)
            pop_keyword_arguments(name, None)

        for name, value in combined_keyword_arguments.items():

            if name in registered_arguments:
                raise PysSignal(
                    result.failure(
                        PysTraceback(
                            TypeError(f"{qualname}() got multiple values for argument {name!r}"),
                            code_call_context,
                            code_position
                        )
                    )
                )

            elif name not in code_parameter_names:
                closest_argument = get_closest(code_parameter_names, name)

                raise PysSignal(
                    result.failure(
                        PysTraceback(
                            TypeError(
                                "{}() got an unexpected keyword argument {!r}{}".format(
                                    qualname,
                                    name,
                                    '' if closest_argument is None else f". Did you mean {closest_argument!r}?"
                                )
                            ),
                            code_call_context,
                            code_position
                        )
                    )
                )

            set_symbol(name, value)
            add_argument(name)

        total_registered = len(registered_arguments)

        if total_registered < code_parameters_length:
            missing_arguments = [repr(name) for name in code_parameter_names if name not in registered_arguments]
            total_missing = len(missing_arguments)

            raise PysSignal(
                result.failure(
                    PysTraceback(
                        TypeError(
                            "{}() missing {} required positional argument{}: {}".format(
                                qualname,
                                total_missing,
                                '' if total_missing == 1 else 's',
                                join(missing_arguments, conjunction='and')
                            )
                        ),
                        code_call_context,
                        code_position
                    )
                )
            )

        elif total_registered > code_parameters_length or arguments_length > code_parameters_length:
            given_arguments = arguments_length if arguments_length > code_parameters_length else total_registered

            raise PysSignal(
                result.failure(
                    PysTraceback(
                        TypeError(
                            f"{qualname}() takes no arguments ({given_arguments} given)"
                            if code_parameters_length == 0 else
                            "{}() takes {} positional argument{} but {} were given".format(
                                qualname,
                                code_parameters_length,
                                '' if code_parameters_length == 1 else 's',
                                given_arguments
                            )
                        ),
                        code_call_context,
                        code_position
                    )
                )
            )

        result.register(
            code.visit(
                code.body,
                PysContext(
                    file=code_context.file,
                    name=self.__name__,
                    qualname=qualname,
                    symbol_table=symbol_table,
                    parent=code_call_context,
                    parent_entry_position=code_position
                )
            )
        )

        if result.should_return() and not result.func_should_return:
            raise PysSignal(result)

        return result.func_return_value