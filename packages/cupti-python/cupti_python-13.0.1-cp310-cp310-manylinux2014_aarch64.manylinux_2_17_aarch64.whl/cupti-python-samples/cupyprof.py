# Copyright 2024-2025 NVIDIA Corporation. All rights reserved.
#
# CUPTI Python sample which shows how to profile a CUDA Python application
# using the CUPTI Python APIs without having to modify the CUDA Python application code.
#
import argparse
from cupti import cupti
from typing import Union, List
import atexit
import cupti_common
import sys
import linecache
import inspect
import runpy


def main():
    # Helper functions and variables
    default_activity_choices = {
        "concurrent_kernel": cupti.ActivityKind.CONCURRENT_KERNEL,
        "memcpy": cupti.ActivityKind.MEMCPY,
        "driver": cupti.ActivityKind.DRIVER,
        "runtime": cupti.ActivityKind.RUNTIME,
        "memory2": cupti.ActivityKind.MEMORY2,
        "context": cupti.ActivityKind.CONTEXT,
        "graph_trace": cupti.ActivityKind.GRAPH_TRACE,
        "external_correlation": cupti.ActivityKind.EXTERNAL_CORRELATION,
        "name": cupti.ActivityKind.NAME,
        "marker": cupti.ActivityKind.MARKER,
        "marker_data": cupti.ActivityKind.MARKER_DATA,
        "stream": cupti.ActivityKind.STREAM,
        "synchronization": cupti.ActivityKind.SYNCHRONIZATION,
        "jit": cupti.ActivityKind.JIT,
        "overhead": cupti.ActivityKind.OVERHEAD,
        "memory_pool": cupti.ActivityKind.MEMORY_POOL,
        "memset": cupti.ActivityKind.MEMSET,
        "device": cupti.ActivityKind.DEVICE,
        "memcpy2": cupti.ActivityKind.MEMCPY2,
    }

    additional_activity_choices = {
        "kernel": cupti.ActivityKind.KERNEL,
        "environment": cupti.ActivityKind.ENVIRONMENT,
        "unified_memory_counter": cupti.ActivityKind.UNIFIED_MEMORY_COUNTER,
        "function": cupti.ActivityKind.FUNCTION,
        "device_attribute": cupti.ActivityKind.DEVICE_ATTRIBUTE,
        "mem_decompress": cupti.ActivityKind.MEM_DECOMPRESS,
        "device_graph_trace": cupti.ActivityKind.DEVICE_GRAPH_TRACE,
    }

    def get_activity_from_user_choice(user_choice: str):
        if user_choice in default_activity_choices:
            return default_activity_choices[user_choice]

        elif user_choice in additional_activity_choices:
            return additional_activity_choices[user_choice]

        else:
            return None

    def get_activity_list(user_activity_choices: List[str] = None) -> list:
        activities = []
        for user_activity_choice in user_activity_choices:
            activity_enum = get_activity_from_user_choice(user_activity_choice)
            if activity_enum is not None:
                if (
                    activity_enum not in activities
                ):  # To avoid enabling the same activity again
                    activities.append(activity_enum)
            else:
                raise Exception(f'Unknown Activity "{user_activity_choice}"')
        return activities

    def on_profiler_start(
        activity_list: list, prof_output: cupti_common.ProfOutput, validation: bool
    ):
        cupti_common.cupti_initialize(
            activity_list=activity_list, prof_output=prof_output, validation=validation
        )

    def on_profiler_stop(activity_list: list):
        cupti.activity_flush_all(0)
        cupti_common.cupti_activity_disable(activity_list)

    def at_exit_handler():
        cupti.activity_flush_all(1)

    def callback(userdata, domain, callback_id, callback_data):
        activity_list = userdata["activity_list"]
        prof_output = userdata["prof_output"]
        validation = userdata["validation"]

        if callback_id == cupti.driver_api_trace_cbid.cuProfilerStart:
            if callback_data.callback_site == cupti.ApiCallbackSite.API_EXIT:
                on_profiler_start(activity_list, prof_output, validation)
        if callback_id == cupti.driver_api_trace_cbid.cuProfilerStop:
            if callback_data.callback_site == cupti.ApiCallbackSite.API_ENTER:
                on_profiler_stop(activity_list)

    def comma_seperated_list(value):
        if value is None:
            all_available_activities = list(default_activity_choices.keys())
            return all_available_activities
        return value.split(",")

    default_activities = list(default_activity_choices.keys())
    all_available_activities = default_activities + list(
        additional_activity_choices.keys()
    )  # Returns a list of all activities which can be enabled
    parser = argparse.ArgumentParser(
        description="CUPTI Python CUDA Python Application Profiler Sample"
    )
    parser.add_argument("python_file_path", type=str, help="Path to the Python file.")
    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        choices=["from_start", "range"],
        default="from_start",
        help="Enable profiling for entire CUDA python program, or only for the subset between cuProfilerStart and cuProfilerStop",
    )
    parser.add_argument(
        "-a",
        "--activity",
        type=comma_seperated_list,
        default=default_activities,
        help=f'Comma-separated list of activities to profile (e.g., "kernel,memcpy"). Available choices are : {all_available_activities}.',
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["brief", "detailed", "none"],
        default="brief",
        help="Output options: brief, detailed, none.",
    )
    parser.add_argument(
        "-v",
        "--validate",
        action="store_true",
        help="This option is not supported in the public release. It is used for internal validation purposes.",
    )

    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for the Python application"
    )
    args = parser.parse_args()

    # Accessing parsed arguments
    python_file_path = args.python_file_path
    profiling_mode = args.profile
    user_activity_choices = args.activity
    output_arg = args.output
    python_app_args = args.args
    validation = args.validate

    # Setting the prof_output
    if output_arg == "brief":
        prof_output = cupti_common.ProfOutput.BRIEF
    elif output_arg == "detailed":
        prof_output = cupti_common.ProfOutput.DETAILED
    elif output_arg == "none":
        prof_output = cupti_common.ProfOutput.NONE

    # Registering atexit handler
    atexit.register(at_exit_handler)

    # Fetching the list of activity enums from the list of user activity choices
    activity_list = get_activity_list(user_activity_choices)

    # Enable profiling
    if profiling_mode == "from_start":
        cupti_common.cupti_initialize(
            activity_list, prof_output=prof_output, validation=validation
        )
    elif profiling_mode == "range":
        userdata = dict()
        userdata[
            "activity_list"
        ] = activity_list  # Using userdata to store activity list
        userdata["prof_output"] = prof_output  # Using userdata to store prof_output
        userdata["validation"] = validation

        subscriber_handle = cupti_common.cupti_subscribe(callback, userdata, "cupyprof")
        cupti.enable_callback(
            1,
            subscriber_handle,
            cupti.CallbackDomain.DRIVER_API,
            cupti.driver_api_trace_cbid.cuProfilerStart,
        )
        cupti.enable_callback(
            1,
            subscriber_handle,
            cupti.CallbackDomain.DRIVER_API,
            cupti.driver_api_trace_cbid.cuProfilerStop,
        )

    sys.argv = [
        python_file_path
    ] + python_app_args  # runpy.run_path relies on the state of sys.argv, so setting this here allows to pass the arguments to the CUDA application

    # Running the target CUDA application
    runpy.run_path(python_file_path, run_name="__main__")

    # Cleanup: Disabling the activities
    cupti_common.cupti_activity_disable(activity_list)

    if cupti_common.global_error_count != 0:
        return -2

    return 0


if __name__ == "__main__":
    error_code = main()
    if error_code:
        print(f"Failed with error code: {error_code}")
    sys.exit(error_code)
