from typing import TypeVar, Generic, Any, Dict

T = TypeVar("T")


class Singleton(type, Generic[T]):
    _instances: Dict["Singleton[T]", T] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
