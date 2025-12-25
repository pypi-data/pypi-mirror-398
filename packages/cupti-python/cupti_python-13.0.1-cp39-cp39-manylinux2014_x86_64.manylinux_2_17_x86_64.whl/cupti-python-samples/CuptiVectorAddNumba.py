# Copyright 2024-2025 NVIDIA Corporation. All rights reserved.
#
# CUPTI Python sample which shows use of CUPTI Activity APIs.
# This sample uses CUDA Python with Numba.
# It is a simple code which does element by element vector addition.
#
import sys
import numpy as np
import cupti_common
from numba import cuda


@cuda.jit(lineinfo=True)
def vector_add(A, B, C):
    idx = cuda.grid(1)
    if idx < A.size:
        C[idx] = A[idx] + B[idx]


def main(argv):
    command_line_config: cupti_common.CommandLineConfig = cupti_common.get_app_args(
        argv,
        "hpvo:",
        ["help", "profile", "validate", "output="],
        f"Usage: {sys.argv[0]} --profile --output [brief|detailed|none]",
    )

    print(f"profiling_enabled: {command_line_config.profiling_enabled}")
    print(f"prof_output: {command_line_config.prof_output}")

    if command_line_config.profiling_enabled:
        cupti_common.cupti_initialize(
            activity_list=cupti_common.default_activity_list,
            prof_output=command_line_config.prof_output,
            validation=command_line_config.validation,
        )  # enables CUPTI activities and registers the buffer completed and buffer requested callbacks

    A = np.random.rand(cupti_common.vector_length)
    B = np.random.rand(cupti_common.vector_length)
    C = np.zeros_like(A)

    print(f"vector_length: {cupti_common.vector_length}")
    print(f"threads_per_block: {cupti_common.threads_per_block}")
    print(f"blocks_per_grid: {cupti_common.blocks_per_grid}")

    vector_add[cupti_common.blocks_per_grid, cupti_common.threads_per_block](A, B, C)

    cuda.synchronize()

    if command_line_config.profiling_enabled:
        cupti_common.cupti_activity_flush()

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
