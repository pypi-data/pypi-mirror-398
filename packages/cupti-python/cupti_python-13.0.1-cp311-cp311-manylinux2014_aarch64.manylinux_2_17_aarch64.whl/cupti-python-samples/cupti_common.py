# Copyright 2024-2025 NVIDIA Corporation. All rights reserved.
#
# Common code uses by CUPTI Python samples.
#
import pprint
import math
import sys, getopt
from cupti import cupti
from cuda.bindings import driver as cuda
from cuda.bindings import runtime as cudart
from cuda.bindings import nvrtc
from enum import Enum

try:
    from validation import validate_activities

    skip_validation = False
except ImportError:
    skip_validation = True
    pass
from dataclasses import dataclass

vector_length = 1024 * 1024
threads_per_block = 128
blocks_per_grid = (vector_length + (threads_per_block - 1)) // threads_per_block
ProfOutput = Enum("ProfOutput", ["BRIEF", "DETAILED", "NONE"])
header_row_printed = False
global_error_count = 0


def invalid_args_exit(usage_str):
    print(usage_str)
    sys.exit(2)


default_activity_list: list[cupti.ActivityKind] = [
    cupti.ActivityKind.CONCURRENT_KERNEL,
    cupti.ActivityKind.MEMCPY,
    cupti.ActivityKind.DRIVER,
    cupti.ActivityKind.RUNTIME,
    cupti.ActivityKind.MEMORY2,
    cupti.ActivityKind.CONTEXT,
    cupti.ActivityKind.GRAPH_TRACE,
    cupti.ActivityKind.EXTERNAL_CORRELATION,
    cupti.ActivityKind.NAME,
    cupti.ActivityKind.MARKER,
    cupti.ActivityKind.MARKER_DATA,
    cupti.ActivityKind.STREAM,
    cupti.ActivityKind.SYNCHRONIZATION,
    cupti.ActivityKind.JIT,
    cupti.ActivityKind.OVERHEAD,
    cupti.ActivityKind.MEMORY_POOL,
    cupti.ActivityKind.MEMSET,
    cupti.ActivityKind.DEVICE,
    cupti.ActivityKind.MEMCPY2,
]


@dataclass
class CommandLineConfig:
    prof_output: ProfOutput = ProfOutput.BRIEF
    profiling_enabled: bool = False
    profile_range: bool = False
    validation: bool = False


def get_app_args(argv, short_opts, long_opts, usage_str) -> CommandLineConfig:
    """Parse command line options for the CUPTI python samples"""

    try:
        opts, args = getopt.getopt(argv, short_opts, long_opts)
    except getopt.GetoptError:
        invalid_args_exit(usage_str)

    command_line_config = CommandLineConfig()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_str)
            sys.exit()
        elif opt in ("-p", "--profile"):
            command_line_config.profiling_enabled = True
        elif opt in ("-r", "--define-profile-range"):
            command_line_config.profile_range = True
        elif opt in ("-o", "--output"):
            if arg == "brief":
                command_line_config.prof_output = ProfOutput.BRIEF
            elif arg == "detailed":
                command_line_config.prof_output = ProfOutput.DETAILED
            elif arg == "none":
                command_line_config.prof_output = ProfOutput.NONE
            else:
                invalid_args_exit(usage_str)
        elif opt in ("-v", "--validate"):
            command_line_config.validation = True
        else:
            invalid_args_exit(usage_str)

    return command_line_config


def verify_result(A, B, C):
    """Verify result of vector addition C = A + B"""
    for i in range(A.size):
        if math.fabs(A[i] + B[i] - C[i]) > 1e-5:
            print("Result verification failed at element ", i)
            return -1
    print("verify_result: PASS")
    return 0


def print_activity(activity: object):
    """prints cupti activity"""

    def get_activity_object_kind_id(object_kind, object_id):
        if object_kind == cupti.ActivityObjectKind.PROCESS:
            object_kind_id = object_id.pt.process_id
        elif object_kind == cupti.ActivityObjectKind.THREAD:
            object_kind_id = object_id.pt.thread_id
        elif object_kind == cupti.ActivityObjectKind.DEVICE:
            object_kind_id = object_id.dcs.device
        elif object_kind == cupti.ActivityObjectKind.CONTEXT:
            object_kind_id = object_id.dcs.context_id
        elif object_kind == cupti.ActivityObjectKind.STREAM:
            object_kind_id = object_id.dcs.stream_id
        else:
            object_kind_id = 0xFFFFFFFF
        return object_kind_id

    activity_name = get_activity_kind_name(activity.kind)
    if (
        activity.kind == cupti.ActivityKind.CONCURRENT_KERNEL
        or activity.kind == cupti.ActivityKind.KERNEL
    ):
        print(
            f'{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, "{activity.name}", correlation_id {activity.correlation_id}, cache_config_requested {activity.cache_config.config.requested}, cache_config_executed {activity.cache_config.config.executed}\n',
            f"\tgrid [{activity.grid_x}, {activity.grid_y}, {activity.grid_z}], block [{activity.block_x}, {activity.block_y}, {activity.block_z}], cluster [{activity.cluster_x}, {activity.cluster_y}, {activity.cluster_z}], shared_memory ({activity.static_shared_memory}, {activity.dynamic_shared_memory})\n",
            f"\tdevice_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, graph_id {activity.graph_id}, graph_node_id {activity.graph_node_id}, channel_id {activity.channel_id}, channel_type {cupti.ChannelType(activity.channel_type).name}\n",
        )

    if activity.kind == cupti.ActivityKind.MEMCPY:
        print(
            f'{activity_name} "{cupti.ActivityMemcpyKind(activity.copy_kind).name}" [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, size {activity.bytes}, src_kind {activity.src_kind}, dst_kind {activity.dst_kind}, correlation_id {activity.correlation_id} \n',
            f"\tdevice_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, graph_id {activity.graph_id}, graph_node_id {activity.graph_node_id}, channel_id {activity.channel_id}, channel_type {cupti.ChannelType(activity.channel_type).name}\n",
        )

    if (
        activity.kind == cupti.ActivityKind.DRIVER
        or activity.kind == cupti.ActivityKind.RUNTIME
    ):
        print(
            f'{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, "{cupti.get_callback_name(cupti.CallbackDomain.DRIVER_API if activity.kind == cupti.ActivityKind.DRIVER else cupti.CallbackDomain.RUNTIME_API, activity.cbid)}", cbid {activity.cbid}, process_id {activity.process_id}, thread_id {activity.thread_id}, correlation_id {activity.correlation_id}\n'
        )

    if activity.kind == cupti.ActivityKind.MEMORY2:
        print(
            f"{activity_name} [ {activity.timestamp} ] memory_operation_type {cupti.ActivityMemoryOperationType(activity.memory_operation_type).name}, memory_kind {cupti.ActivityMemoryKind(activity.memory_kind).name}, size {activity.bytes}, address {activity.address}, pc {activity.pc},\n",
            f"  device_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, process_id {activity.process_id}, correlation_id {activity.correlation_id}, is_async {activity.is_async},\n",
            f"  memory_pool {cupti.ActivityMemoryPoolType(activity.memory_pool_config.memory_pool_type).name}, memory_pool_address {activity.memory_pool_config.address},  memory_pool_threshold {activity.memory_pool_config.release_threshold}\n",
            f'source "{activity.source}"\n',
        )

    if activity.kind == cupti.ActivityKind.CONTEXT:
        print(
            f"{activity_name} compute_api_kind {cupti.ActivityComputeApiKind(activity.compute_api_kind).name}, context_id {activity.context_id}, device_id {activity.device_id}, null_stream_id {activity.null_stream_id}, cig_mode {activity.cig_mode}\n"
        )

    if activity.kind == cupti.ActivityKind.UNIFIED_MEMORY_COUNTER:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, counter_kind {cupti.ActivityUnifiedMemoryCounterKind(activity.counter_kind).name}, value {activity.value}, address {activity.address}, src_id {activity.src_id}, dst_id {activity.dst_id}, process_id {activity.process_id}\n"
        )

    if activity.kind == cupti.ActivityKind.MODULE:
        print(
            f"{activity_name} context_id {activity.context_id}, id {activity.id}, cubin_size {activity.cubin_size}\n"
        )

    if activity.kind == cupti.ActivityKind.DEVICE_ATTRIBUTE:
        print(
            f"{activity_name} {activity.attribute.cupti}, device_id {activity.device_id}, value {hex(activity.value.v_uint64)}\n"
        )

    if activity.kind == cupti.ActivityKind.CUDA_EVENT:
        print(
            f"{activity_name} context_id {activity.context_id}, stream_id {activity.stream_id}, correlation_id {activity.correlation_id}, event_id {activity.event_id} cuda_event_sync_id {activity.cuda_event_sync_id}\n"
        )

    if activity.kind == cupti.ActivityKind.STREAM:
        print(
            f"{activity_name} type {cupti.ActivityStreamFlag(activity.flag).name}, priority {activity.priority}, context_id {activity.context_id}, stream_id {activity.stream_id}, correlation_id {activity.correlation_id}\n"
        )

    if activity.kind == cupti.ActivityKind.SYNCHRONIZATION:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, type {cupti.ActivitySynchronizationType(activity.type).name}, context_id {activity.context_id}, stream_id {activity.stream_id}, correlation_id {activity.correlation_id}, event_id {activity.cuda_event_id} cuda_event_sync_id {activity.cuda_event_sync_id} \n"
        )

    if activity.kind == cupti.ActivityKind.EXTERNAL_CORRELATION:
        print(
            f"{activity_name} external_kind {cupti.ExternalCorrelationKind(activity.external_kind).name}, correlation_id {activity.correlation_id}, external_id {activity.external_id}\n"
        )

    if activity.kind == cupti.ActivityKind.GRAPH_TRACE:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, correlation_id {activity.correlation_id}\n device_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, graph_id {activity.graph_id}\n"
        )

    if activity.kind == cupti.ActivityKind.JIT:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, device_id {activity.device_id}, correlation_id {activity.correlation_id}, process_id {activity.process_id}, thread_id {activity.thread_id}\n",
            f"jitEntryType {cupti.ActivityJitEntryType(activity.jit_entry_type).name}, jitOperationType {cupti.ActivityJitOperationType(activity.jit_operation_type).name}, jitOperationCorrelationId {activity.jit_operation_correlation_id}\n cache_size {activity.cache_size}, cache_path {activity.cache_path}\n",
        )
    if activity.kind == cupti.ActivityKind.NAME:
        object_kind_id = get_activity_object_kind_id(
            activity.object_kind, activity.object_id
        )
        if activity.object_kind == cupti.ActivityObjectKind.CONTEXT:
            print(
                f"{activity_name} {cupti.ActivityObjectKind(activity.object_kind).name} {object_kind_id} {cupti.ActivityObjectKind.DEVICE.name} id {get_activity_object_kind_id(cupti.ActivityObjectKind.DEVICE, activity.object_id)}, name {activity.name}\n"
            )

        if activity.object_kind == cupti.ActivityObjectKind.STREAM:
            print(
                f"{activity_name} {cupti.ActivityObjectKind(activity.object_kind).name} {object_kind_id} {cupti.ActivityObjectKind.CONTEXT.name} id {get_activity_object_kind_id(cupti.ActivityObjectKind.CONTEXT, activity.object_id)}, {cupti.ActivityObjectKind.DEVICE.name} id {get_activity_object_kind_id(cupti.ActivityObjectKind.DEVICE, activity.object_id)} name {activity.name}\n"
            )
        else:
            print(
                f"{activity_name} {cupti.ActivityObjectKind(activity.object_kind).name} id {object_kind_id}, name {activity.name}\n"
            )

    if activity.kind == cupti.ActivityKind.MARKER:
        print(
            f"{activity_name} [ {activity.timestamp} ] id {activity.id}, domain {activity.domain}, name {activity.name}\n"
        )

    if activity.kind == cupti.ActivityKind.MARKER_DATA:
        print(
            f"{activity_name} id {activity.id}, color {hex(activity.color)}, category {activity.category}, payload {activity.payload.metric_value_uint64}/{activity.payload.metric_value_double}\n"
        )

    if activity.kind == cupti.ActivityKind.OVERHEAD:
        object_kind_id = get_activity_object_kind_id(
            activity.object_kind, activity.object_id
        )
        print(
            f"{activity_name} {cupti.ActivityOverheadKind(activity.overhead_kind).name} [{activity.start} , {activity.end} ] duration {activity.end - activity.start}, {cupti.ActivityObjectKind(activity.object_kind).name}, id {object_kind_id}, correlation id {activity.correlation_id}\n"
        )

    if activity.kind == cupti.ActivityKind.MEMORY_POOL:
        print(
            f"{activity_name} [ {activity.timestamp} ] memory_pool_operation {cupti.ActivityMemoryPoolOperationType(activity.memory_pool_operation_type).name}, memory_pool {cupti.ActivityMemoryPoolType(activity.memory_pool_type).name}, address {activity.address}, size {activity.size_}, utilized_size {activity.utilized_size}, release_threshold {activity.release_threshold},\n"
            f"  device_id {activity.device_id}, process_id {activity.process_id}, correlation_id {activity.correlation_id}\n"
        )

    if activity.kind == cupti.ActivityKind.MEMSET:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] duration {activity.end - activity.start}, value {activity.value}, size {activity.bytes}, correlation_id {activity.correlation_id}\n"
            f"\tdevice_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, graph_id {activity.graph_id}, graph_node_id {activity.graph_node_id}, channel_id {activity.channel_id}, channel_type {cupti.ChannelType(activity.channel_type).name}\n"
        )

    if activity.kind == cupti.ActivityKind.DEVICE:
        print(f"{activity_name} {activity.name} [ {activity.id} ]\n")

    if activity.kind == cupti.ActivityKind.FUNCTION:
        print(
            f"{activity_name} id {activity.id}, context_id {activity.context_id}, module_id {activity.module_id}, function_index {activity.function_ind_ex}, name {activity.name}\n"
        )

    if activity.kind == cupti.ActivityKind.DEVICE_GRAPH_TRACE:
        print(f"{activity_name} [ start {activity.start}, end {activity.end} ]\n")
        print(
            f"  device_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, graph_id {activity.graph_id}, launcher_graph_id {activity.launcher_graph_id}\n"
        )

    if activity.kind == cupti.ActivityKind.MEM_DECOMPRESS:
        print(
            f"{activity_name} [ {activity.start}, {activity.end} ] device_id {activity.device_id}, context_id {activity.context_id}, stream_id {activity.stream_id}, correlation_id {activity.correlation_id}\n"
        )
        print(
            f"channel_id {activity.channel_id}, number_of_operations {activity.number_of_operations}, source_bytes {activity.source_bytes}\n"
        )


def get_activity_kind_name(activity_kind: int):
    kind = cupti.ActivityKind(activity_kind)
    return kind.name


def cupti_initialize(
    activity_list: list[cupti.ActivityKind],
    prof_output: ProfOutput,
    validation: bool = False,
):
    """Initialize CUPTI
    Enable CUPTI activities
    Register buffer requested and buffer completed callbacks"""

    def func_buffer_completed(activities: list):
        global header_row_printed
        if prof_output == ProfOutput.BRIEF and not header_row_printed:
            print(
                "{:<30} {:<20} {:<20} {:<20} {}".format(
                    "Activity Kind", "Start", "Duration", "correlationId", "Name"
                )
            )
            header_row_printed = True

        for activity in activities:
            if prof_output == ProfOutput.BRIEF:

                kind_str = get_activity_kind_name(activity.kind)
                start = activity.start if hasattr(activity, "start") else "nil"
                end = activity.end if hasattr(activity, "end") else "nil"
                duration = end - start if start != "nil" and end != "nil" else "nil"
                correlation_id = (
                    activity.correlation_id
                    if hasattr(activity, "correlation_id")
                    else "nil"
                )
                name = (
                    cupti.get_callback_name(
                        cupti.CallbackDomain.DRIVER_API
                        if activity.kind == cupti.ActivityKind.DRIVER
                        else cupti.CallbackDomain.RUNTIME_API,
                        activity.cbid,
                    )
                    if activity.kind == cupti.ActivityKind.DRIVER
                    or activity.kind == cupti.ActivityKind.RUNTIME
                    else activity.name
                    if hasattr(activity, "name")
                    else "nil"
                )

                print(
                    f"{kind_str:<30} {start:<20} {duration:<20} {correlation_id:<20} {name}"
                )

            elif prof_output == ProfOutput.DETAILED:
                print_activity(activity)  # Detailed print of activity record

        if validation and not skip_validation:
            validate_activities(activities)

    def func_buffer_requested():
        buffer_size = 8 * 1024 * 1024
        max_num_records = 0  # Limiting it to 10 records was causing BufferRequested callback to be called multiple times.Have disabled max_num_records
        return buffer_size, max_num_records

    try:
        for activity in activity_list:
            cupti.activity_enable(activity)

    except cupti.cuptiError as e:
        print(f"Error while enabling Activity Kind {activity.name} : {e}")
        sys.exit(3)

    cupti.activity_register_callbacks(func_buffer_requested, func_buffer_completed)


def cupti_activity_disable(activity_list: list[cupti.ActivityKind]):
    """Disable CUPTI activities"""
    for activity in activity_list:
        cupti.activity_disable(activity)


def cupti_activity_flush():
    """Flush CUPTI activity records"""
    cupti.activity_flush_all(1)


def cupti_subscribe(callback, userdata, subscriber_name):
    p_params = cupti.SubscriberParams()
    p_params.struct_size = cupti.SUBSCRIBER_PARAMS_SIZE
    p_params.subscriber_name = subscriber_name
    try:
        subscriber_handle = cupti.subscribe_v2(callback, userdata, p_params.ptr)
        return subscriber_handle
    except cupti.cuptiError as e:
        print(f"Error while subscribing to CUPTI: {cupti.Result(e.status).name}")
        if e.status == cupti.Result.ERROR_MULTIPLE_SUBSCRIBERS_NOT_SUPPORTED:
            print(f"old subscriber name = {p_params.old_subscriber_name}")
        sys.exit(3)


def configure_uvm_activity():
    uvm_counter_kinds = [
        cupti.ActivityUnifiedMemoryCounterKind.BYTES_TRANSFER_HTOD,
        cupti.ActivityUnifiedMemoryCounterKind.BYTES_TRANSFER_DTOH,
        cupti.ActivityUnifiedMemoryCounterKind.CPU_PAGE_FAULT_COUNT,
        cupti.ActivityUnifiedMemoryCounterKind.GPU_PAGE_FAULT,
        cupti.ActivityUnifiedMemoryCounterKind.THRASHING,
        cupti.ActivityUnifiedMemoryCounterKind.THROTTLING,
        cupti.ActivityUnifiedMemoryCounterKind.REMOTE_MAP,
        cupti.ActivityUnifiedMemoryCounterKind.BYTES_TRANSFER_DTOD,
    ]

    uvm_configs = cupti.ActivityUnifiedMemoryCounterConfig(len(uvm_counter_kinds))
    uvm_configs.scope = 1
    uvm_configs.device_id = 0
    uvm_configs.enable = 1
    for index, uvm_counter_kind in enumerate(uvm_counter_kinds):
        uvm_configs[index].kind = uvm_counter_kind

    cupti.activity_configure_unified_memory_counter(
        uvm_configs.ptr, len(uvm_counter_kinds)
    )


# Helper functions for CUDA API
def get_gpu_architecture(devID: int):
    major = checkCudaErrors(
        cudart.cudaDeviceGetAttribute(
            cudart.cudaDeviceAttr.cudaDevAttrComputeCapabilityMajor, devID
        )
    )
    minor = checkCudaErrors(
        cudart.cudaDeviceGetAttribute(
            cudart.cudaDeviceAttr.cudaDevAttrComputeCapabilityMinor, devID
        )
    )
    _, nvrtc_minor = checkCudaErrors(nvrtc.nvrtcVersion())
    use_cubin = nvrtc_minor >= 1
    prefix = "sm" if use_cubin else "compute"
    arch_arg = bytes(f"--gpu-architecture={prefix}_{major}{minor}", "ascii")
    return arch_arg


def _cudaGetErrorEnum(error):
    if isinstance(error, cuda.CUresult):
        err, name = cuda.cuGetErrorName(error)
        return name if err == cuda.CUresult.CUDA_SUCCESS else "<unknown>"
    elif isinstance(error, cudart.cudaError_t):
        return cudart.cudaGetErrorName(error)[1]
    elif isinstance(error, nvrtc.nvrtcResult):
        return nvrtc.nvrtcGetErrorString(error)[1]
    else:
        raise RuntimeError("Unknown error type: {}".format(error))


def checkCudaErrors(result):
    if result[0].value:
        raise RuntimeError(
            "CUDA error code={}({})".format(
                result[0].value, _cudaGetErrorEnum(result[0])
            )
        )
    if len(result) == 1:
        return None
    elif len(result) == 2:
        return result[1]
    else:
        return result[1:]
