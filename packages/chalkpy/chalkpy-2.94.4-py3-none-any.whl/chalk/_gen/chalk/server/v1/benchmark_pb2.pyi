from chalk._gen.chalk.auth.v1 import permissions_pb2 as _permissions_pb2
from chalk._gen.chalk.common.v1 import online_query_pb2 as _online_query_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class BenchmarkStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BENCHMARK_STATUS_UNSPECIFIED: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_QUEUED: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_WORKING: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_COMPLETED: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_FAILED: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_SKIPPED: _ClassVar[BenchmarkStatus]
    BENCHMARK_STATUS_CANCELED: _ClassVar[BenchmarkStatus]

BENCHMARK_STATUS_UNSPECIFIED: BenchmarkStatus
BENCHMARK_STATUS_QUEUED: BenchmarkStatus
BENCHMARK_STATUS_WORKING: BenchmarkStatus
BENCHMARK_STATUS_COMPLETED: BenchmarkStatus
BENCHMARK_STATUS_FAILED: BenchmarkStatus
BENCHMARK_STATUS_SKIPPED: BenchmarkStatus
BENCHMARK_STATUS_CANCELED: BenchmarkStatus

class SimpleOnlineQueryBulkRequest(_message.Message):
    __slots__ = ("input_features", "output_features")
    INPUT_FEATURES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FEATURES_FIELD_NUMBER: _ClassVar[int]
    input_features: _containers.RepeatedScalarFieldContainer[str]
    output_features: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self, input_features: _Optional[_Iterable[str]] = ..., output_features: _Optional[_Iterable[str]] = ...
    ) -> None: ...

class CreateBenchmarkRequest(_message.Message):
    __slots__ = ("warmup_qps", "warmup_duration", "qps", "duration", "query_bulk", "simple_query_bulk")
    WARMUP_QPS_FIELD_NUMBER: _ClassVar[int]
    WARMUP_DURATION_FIELD_NUMBER: _ClassVar[int]
    QPS_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    QUERY_BULK_FIELD_NUMBER: _ClassVar[int]
    SIMPLE_QUERY_BULK_FIELD_NUMBER: _ClassVar[int]
    warmup_qps: int
    warmup_duration: _duration_pb2.Duration
    qps: int
    duration: _duration_pb2.Duration
    query_bulk: _online_query_pb2.OnlineQueryBulkRequest
    simple_query_bulk: SimpleOnlineQueryBulkRequest
    def __init__(
        self,
        warmup_qps: _Optional[int] = ...,
        warmup_duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...,
        qps: _Optional[int] = ...,
        duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...,
        query_bulk: _Optional[_Union[_online_query_pb2.OnlineQueryBulkRequest, _Mapping]] = ...,
        simple_query_bulk: _Optional[_Union[SimpleOnlineQueryBulkRequest, _Mapping]] = ...,
    ) -> None: ...

class CreateBenchmarkResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: BenchmarkStatus
    def __init__(self, status: _Optional[_Union[BenchmarkStatus, str]] = ...) -> None: ...
