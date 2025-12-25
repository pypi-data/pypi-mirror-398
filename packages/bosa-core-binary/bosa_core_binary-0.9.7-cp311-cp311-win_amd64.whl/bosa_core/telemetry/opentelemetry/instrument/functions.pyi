from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from typing import Collection

class BOSAFunctionsInstrumentor(BaseInstrumentor):
    """OpenTelemetry Generic Function Instrumentor.

    Supports:
        - Class functions (CustomClass.function)
        - Module functions (module.function)
        - Static methods (@staticmethod)
        - Class methods (@classmethod)

    Not Supported:
        - Passing bound instance methods (obj.method) directly to ``instrument``
        - Abstract methods (abc.abstractmethod)
        - Overridden methods (overridden from parent class, include implementation of abstract method)

    Params:
        methods (list[Callable]): List of methods to instrument.
        max_length (int): Maximum length for function args, kwargs, and return value string. Defaults to 200.

    Example:
        ```
        ### Below source code from `module/classes/custom_class.py`
        class CustomClass:

            def method(self, ...):
                ...

            @classmethod
            def class_method(cls, ...):
                ...

            @staticmethod
            def static_method(...):
                ...

            async def async_method(self, ...):
                ...

            @classmethod
            async def async_class_method(cls, ...):
                ...

            @staticmethod
            async def async_static_method(...):
                ...

        ### Below source code from `module/functions.py`
        def sync_function(...):
            ...

        async def async_function(...):
            ...

        ### Instrumenting the above methods in different modules
        from module import functions
        from module.classes.custom_class import CustomClass

        # Instrument all functions in the module
        BOSAFunctionsInstrumentor().instrument(
            methods=[
                functions.sync_function, functions.async_function,
                CustomClass.method, CustomClass.class_method,
                CustomClass.static_method, CustomClass.async_method,
                CustomClass.async_class_method, CustomClass.async_static_method
            ],
            max_length=100
        )

        obj = CustomClass()
        # Call the methods
        obj.method(...)
        CustomClass.class_method(...)
        CustomClass.static_method(...)

        await obj.async_method(...)
        await CustomClass.async_class_method(...)
        await CustomClass.async_static_method(...)

        functions.sync_function(...)
        await functions.async_function(...)

        # Uninstrument all functions in the module
        BOSAFunctionsInstrumentor().uninstrument()
        ```

    Note:
        To use instrumented function inside a module, you must use the function with module prefix. For example,
        if you have a function `sync_function` in a module `functions`,
        you must use it as `functions.sync_function(...)`.
    """
    DEFAULT_MAX_LENGTH: int
    def instrumentation_dependencies(self) -> Collection[str]:
        """Returns a collection of dependencies required for instrumentation.

        Returns:
            Collection[str]: A collection of dependency names.
        """
    def instrument(self, **kwargs) -> None:
        """Instruments generic custom classes.

        Args:
            **kwargs: Additional keyword arguments.
                methods (list): List of methods to instrument.
                max_length (int): Maximum length for trimming non-dict/list data. Defaults to 200.

        Raises:
            TypeError: If any method is not callable.
        """
    def uninstrument(self, **kwargs) -> None:
        """Uninstrument the instrumented methods.

        Args:
            **kwargs: Additional keyword arguments.
        """
