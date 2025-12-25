# Copyright 2024-2025 NVIDIA Corporation. All rights reserved.
#
# CUPTI Python sample which shows use of CUPTI Callback APIs.
# This sample uses CUDA Python with Numba.
# It is a simple code which does element by element vector addition.
#
import sys
import pprint
import numpy as np
from numba import cuda
from cupti import cupti
import cupti_common


@cuda.jit(lineinfo=True)
def vector_add(A, B, C):
    idx = cuda.grid(1)
    if idx < A.size:
        C[idx] = A[idx] + B[idx]


def driver_api_callback(user_data, domain, callback_id, cbdata):

    if (
        domain == cupti.CallbackDomain.DRIVER_API
        or domain == cupti.CallbackDomain.RUNTIME_API
    ):
        current_record = None
        if cbdata.callback_site == cupti.ApiCallbackSite.API_ENTER:
            start_timestamp = cupti.get_timestamp()
            current_record = dict()  # create a record for the API
            user_data.append(
                current_record
            )  # append the record into the user_data list
            current_record["start"] = start_timestamp

        if cbdata.callback_site == cupti.ApiCallbackSite.API_EXIT:
            end_timestamp = cupti.get_timestamp()
            current_record = user_data[
                len(user_data) - 1
            ]  # API record is already created and is located at the end of the list
            current_record["end"] = end_timestamp

        current_record["function_name"] = cbdata.function_name
        current_record["correlation_id"] = cbdata.correlation_id

    elif domain == cupti.CallbackDomain.RESOURCE:
        print("SUCCESS : CallbackDomain RESOURCE enabled successfully")
        print(f"RESOURCE CBID : {cupti.CallbackIdResource(callback_id).name}")
    elif domain == cupti.CallbackDomain.SYNCHRONIZE:
        print("SUCCESS : CallbackDomain SYNCHRONIZE enabled successfully")
        print(f"SYNCHRONIZE CBID : {cupti.CallbackIdSync(callback_id).name}")
    elif domain == cupti.CallbackDomain.STATE:
        print("SUCCESS : CallbackDomain STATE enabled successfully")
        if callback_id == cupti.CallbackIdState.FATAL_ERROR:
            print(
                f"notification.result = {cupti.Result(cbdata._anon_pod_member0.notification.result).name}"
            )
            print(
                f"notification.message = {cbdata._anon_pod_member0.notification.message}"
            )


def display_api_records(driver_api_records, prof_output):
    if prof_output == cupti_common.ProfOutput.BRIEF:
        print(
            "{:<20} {:<20} {:<20} {:<20} {}".format(
                "Start", "End", "Duration", "correlationId", "Name"
            )
        )
        for record in driver_api_records:
            start = record["start"]
            end = record["end"]
            correlation_id = record["correlation_id"]
            name = record["function_name"]
            duration = end - start
            print(f"{start:<20} {end:<20} {duration:<20} {correlation_id:<20} {name}")

    elif prof_output == cupti_common.ProfOutput.DETAILED:
        for record in driver_api_records:
            pprint.pp(record)  # pretty print the driver_api record


def main(argv):
    command_line_config: cupti_common.CommandLineConfig = cupti_common.get_app_args(
        argv,
        "hpo:",
        ["help", "profile", "output="],
        f"Usage: {sys.argv[0]} --profile --output [brief|detailed|none]",
    )
    print(f"profiling_enabled: {command_line_config.profiling_enabled}")
    print(f"prof_output: {command_line_config.prof_output}")
    userdata = list()
    if command_line_config.profiling_enabled:
        subscriber_obj = cupti_common.cupti_subscribe(
            driver_api_callback, userdata, "CuptiVectorAddNumbaCallback"
        )
        cupti.enable_domain(1, subscriber_obj, cupti.CallbackDomain.DRIVER_API)
        cupti.enable_domain(1, subscriber_obj, cupti.CallbackDomain.RUNTIME_API)
        cupti.enable_domain(1, subscriber_obj, cupti.CallbackDomain.RESOURCE)
        cupti.enable_domain(1, subscriber_obj, cupti.CallbackDomain.SYNCHRONIZE)
        cupti.enable_domain(1, subscriber_obj, cupti.CallbackDomain.STATE)

    A = np.random.rand(cupti_common.vector_length)
    B = np.random.rand(cupti_common.vector_length)
    C = np.zeros_like(A)

    print(f"vector_length: {cupti_common.vector_length}")
    print(f"threads_per_block: {cupti_common.threads_per_block}")
    print(f"blocks_per_grid: {cupti_common.blocks_per_grid}")

    vector_add[cupti_common.blocks_per_grid, cupti_common.threads_per_block](A, B, C)

    cuda.synchronize()

    if command_line_config.profiling_enabled:
        cupti.unsubscribe(subscriber_obj)
        display_api_records(userdata, command_line_config.prof_output)

    if cupti_common.verify_result(A, B, C) != 0:
        return -1

    if cupti_common.global_error_count != 0:
        return -2

    return 0


if __name__ == "__main__":
    error_code = main(sys.argv[1:])
    if error_code:
        print("Failed with error code: ", error_code)
    sys.exit(error_code)
