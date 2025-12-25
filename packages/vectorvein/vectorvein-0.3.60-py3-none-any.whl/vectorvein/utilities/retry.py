# @Author: Bi Ying
# @Date:   2024-06-07 16:16:49
import time
from collections.abc import Callable
from typing import Any, TypeVar, Generic


ResultType = TypeVar("ResultType")


class Retry(Generic[ResultType]):
    def __init__(self, function: Callable[..., ResultType]):
        self.function: Callable[..., ResultType] = function
        self.__retry_times: int = 3
        self.__sleep_time: int | float = 1
        self.__timeout: int = 180
        self.__result_check: Callable[[ResultType], bool] | None = None
        self.pargs: list = []
        self.kwargs: dict = {}

    def args(self, *args: Any, **kwargs: Any) -> "Retry[ResultType]":
        self.pargs = list(args)
        self.kwargs = kwargs
        return self

    def retry_times(self, retry_times: int) -> "Retry[ResultType]":
        self.__retry_times = retry_times
        return self

    def sleep_time(self, sleep_time: int | float) -> "Retry[ResultType]":
        self.__sleep_time = sleep_time
        return self

    def result_check(self, check_function: Callable[[ResultType], bool]) -> "Retry[ResultType]":
        self.__result_check = check_function
        return self

    def _check_result(self, result: ResultType) -> bool:
        try:
            if self.__result_check is None:
                return True
            return self.__result_check(result)
        except Exception as e:
            print(f"Retry result check error: {e}")
            return False

    def run(self) -> tuple[bool, ResultType | None]:
        try_times = 0
        start_time = time.time()

        while try_times <= self.__retry_times and time.time() - start_time < self.__timeout:
            try:
                result: ResultType = self.function(*self.pargs, **self.kwargs)
                if self._check_result(result):
                    return True, result
                try_times += 1
                time.sleep(self.__sleep_time)
            except Exception as e:
                print(f"{self.function.__name__} function error: {e}")
                try_times += 1
                time.sleep(self.__sleep_time)

        return False, None
