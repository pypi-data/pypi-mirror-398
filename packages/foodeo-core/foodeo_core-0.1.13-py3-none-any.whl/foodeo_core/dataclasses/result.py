from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypeVar, Generic


class ResultType(Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"
    CANCELED = "Canceled"


@dataclass(frozen=True)
class Result:
    result_type: ResultType
    message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.result_type == ResultType.SUCCESS

    @property
    def is_canceled(self) -> bool:
        return self.result_type == ResultType.CANCELED

    @property
    def is_failure(self) -> bool:
        return self.result_type == ResultType.FAILURE

    @property
    def http_status_code(self) -> int:
        if self.result_type == ResultType.FAILURE:
            return 500
        elif self.result_type == ResultType.CANCELED:
            return 400
        else:
            return 200

    @staticmethod
    def success(message: str = None) -> 'Result':
        return Result(ResultType.SUCCESS, message)

    @staticmethod
    def failure(error: str) -> 'Result':
        if not error:
            raise ValueError("Error message must not be empty.")
        return Result(ResultType.FAILURE, error)

    @staticmethod
    def canceled(reason: Optional[str] = None) -> 'Result':
        return Result(ResultType.CANCELED, reason)


T = TypeVar('T')


@dataclass(frozen=True)
class ResultWithValue(Generic[T], Result):
    value: Optional[T] = None

    @property
    def has_value(self) -> bool:
        return self.is_success and self.value is not None

    @staticmethod
    def success_value(value: T, message: str = None) -> 'ResultWithValue[T]':
        return ResultWithValue(ResultType.SUCCESS, message, value)

    @staticmethod
    def failure(error: str) -> 'ResultWithValue[T]':
        if not error:
            raise ValueError("Error message must not be empty.")
        return ResultWithValue(ResultType.FAILURE, error, None)

    @staticmethod
    def canceled(reason: Optional[str] = None) -> 'ResultWithValue[T]':
        return ResultWithValue(ResultType.CANCELED, reason, None)

    @staticmethod
    def from_result(result: Result,  value: T = None) -> 'ResultWithValue[T]':
        return ResultWithValue(result.result_type, result.message, value)