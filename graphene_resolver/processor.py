"""Simple weighted function execution.  """

import typing


class Processor:
    """A processor can register multiple process, they will executed by weight
    and stop on first value returns.  """

    _process_registry: typing.List[typing.Tuple[float, typing.Callable]]

    def __init__(self) -> None:
        self._process_registry = []

    def register(self, weight: float) -> typing.Callable[[typing.Callable], None]:
        """Get decorator for process registering.

        Args:
            weight (float): Function weight, higher weight will executed first.

        Returns:
            typing.Callable[[typing.Callable], None]: Decorator.
        """

        def _decorator(func: typing.Callable) -> None:
            self._process_registry.append((weight, func))
            self._process_registry.sort(key=lambda v: v[0], reverse=True)
        return _decorator

    def process(self, **kwargs) -> dict:
        """Execute all registered function by weight,
        high weight function execute first.

        Raises:
            NotImplementedError: All function is executed but no one returns a value.

        Returns:
            dict: First return value.
        """

        for _, i in self._process_registry:
            ret = i(**kwargs)
            if ret is not None:
                return ret
        raise NotImplementedError('Process not implemented')
