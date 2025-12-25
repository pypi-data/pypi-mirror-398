# Copyright 2024-2025 NVIDIA Corporation. All rights reserved.
#
# CUPTI Python sample which shows use of CUPTI Activity APIs.
# This sample uses CUDA Python Driver APIs.
# It launches a simple CUDA kernel which does element by element vector addition.
#
import atexit
import sys
import numpy as np
import cupti_common
from cuda.bindings import nvrtc
from cuda.bindings import driver as cuda
from cupti import cupti
from cupti_common import checkCudaErrors, get_gpu_architecture


def on_profiler_start(prof_output, validation):
    cupti_common.cupti_initialize(
        activity_list=cupti_common.default_activity_list,
        prof_output=prof_output,
        validation=validation,
    )  # enables CUPTI activities and registers the buffer completed and buffer requested callbacks


def on_profiler_stop():
    cupti.activity_flush_all(0)
    cupti_common.cupti_activity_disable(cupti_common.default_activity_list)


def at_exit_handler():
    cupti.activity_flush_all(1)


def callback(userdata, domain, callback_id, callback_data):

    prof_output = userdata["prof_output"]
    validation = userdata["validation"]

    if callback_id == cupti.driver_api_trace_cbid.cuProfilerStart:
        if callback_data.callback_site == cupti.ApiCallbackSite.API_EXIT:
            on_profiler_start(prof_output, validation)
    if callback_id == cupti.driver_api_trace_cbid.cuProfilerStop:
        if callback_data.callback_site == cupti.ApiCallbackSite.API_ENTER:
            on_profiler_stop()


def main(argv):
    command_line_config: cupti_common.CommandLineConfig = cupti_common.get_app_args(
        argv,
        "hpvro:",
        ["help", "profile", "validate", "define-profile-range", "output="],
        f"Usage: {sys.argv[0]} --profile --define-profile-range --output {{brief|detailed|none}}",
    )

    print(f"profiling_enabled: {command_line_config.profiling_enabled}")
    print(f"prof_output: {command_line_config.prof_output}")
    print(f"profile_range: {command_line_config.profile_range}")

    if command_line_config.profiling_enabled:
        atexit.register(at_exit_handler)
        if command_line_config.profile_range:
            userdata = dict()
            userdata["prof_output"] = command_line_config.prof_output
            userdata["validation"] = command_line_config.validation

            subscriber_handle = cupti_common.cupti_subscribe(
                callback, userdata, "CuptiVectorAddDrv"
            )
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
        else:
            cupti_common.cupti_initialize(
                activity_list=cupti_common.default_activity_list,
                prof_output=command_line_config.prof_output,
                validation=command_line_config.validation,
            )

    vector_add_kernel = """\
    extern "C" __global__ void vector_add(int *a, int *b, int *c, int N){

            int i = blockIdx.x * blockDim.x + threadIdx.x;
            if(i < N){
            c[i] = a[i] + b[i];
            }

    }

    """
    # initialize CUDA Driver API
    checkCudaErrors(cuda.cuInit(0))
    cuDevice = checkCudaErrors(cuda.cuDeviceGet(0))
    context = checkCudaErrors(cuda.cuCtxCreate(None, 0, cuDevice))

    # Compile the program to PTX
    prog = checkCudaErrors(
        nvrtc.nvrtcCreateProgram(
            str.encode(vector_add_kernel), b"vector_add.cu", 0, [], []
        )
    )
    arch_args = get_gpu_architecture(0)
    opts = [b"--fmad=false", arch_args, b"--generate-line-info"]
    checkCudaErrors(nvrtc.nvrtcCompileProgram(prog, 2, opts))

    ptxSize = checkCudaErrors(nvrtc.nvrtcGetPTXSize(prog))

    ptx = b" " * ptxSize
    checkCudaErrors(nvrtc.nvrtcGetPTX(prog, ptx))

    # Create PTX Module and extracting the  kernel
    ptx = np.char.array(ptx)
    module = checkCudaErrors(cuda.cuModuleLoadData(ptx.ctypes.data))
    kernel = checkCudaErrors(cuda.cuModuleGetFunction(module, b"vector_add"))

    print(f"vector_length: {cupti_common.vector_length}")
    print(f"threads_per_block: {cupti_common.threads_per_block}")
    print(f"blocks_per_grid: {cupti_common.blocks_per_grid}")

    # Prepare Host Data
    hX = np.ones(cupti_common.vector_length, dtype=np.int32)
    hY = np.ones(cupti_common.vector_length, dtype=np.int32)
    hOut = np.empty_like(hX, dtype=np.int32)
    BUFFER_SIZE = cupti_common.vector_length * hX.itemsize

    # Allocate memory on device
    dXclass = checkCudaErrors(cuda.cuMemAlloc(BUFFER_SIZE))
    dYclass = checkCudaErrors(cuda.cuMemAlloc(BUFFER_SIZE))
    dOutclass = checkCudaErrors(cuda.cuMemAlloc(BUFFER_SIZE))

    stream = checkCudaErrors(cuda.cuStreamCreate(0))

    if command_line_config.profile_range:
        checkCudaErrors(cuda.cuProfilerStart())

    checkCudaErrors(
        cuda.cuMemcpyHtoDAsync(dXclass, hX.ctypes.data, BUFFER_SIZE, stream)
    )
    checkCudaErrors(
        cuda.cuMemcpyHtoDAsync(dYclass, hY.ctypes.data, BUFFER_SIZE, stream)
    )
    checkCudaErrors(
        cuda.cuMemcpyHtoDAsync(dOutclass, hOut.ctypes.data, BUFFER_SIZE, stream)
    )

    dX = np.array([int(dXclass)], dtype=np.uint64)
    dY = np.array([int(dYclass)], dtype=np.uint64)
    dOut = np.array([int(dOutclass)], dtype=np.uint64)

    # Prepare input arguments for kernel
    n = np.array(
        cupti_common.threads_per_block * cupti_common.blocks_per_grid, dtype=np.uint32
    )
    args = [dX, dY, dOut, n]
    args = np.array([arg.ctypes.data for arg in args], dtype=np.uint64)

    # Launch the CUDA kernel
    checkCudaErrors(
        cuda.cuLaunchKernel(
            kernel,
            cupti_common.blocks_per_grid,  # grid x dim
            1,  # grid y dim
            1,  # grid z dim
            cupti_common.threads_per_block,  # block x dim
            1,  # block y dim
            1,  # block z dim
            0,  # dynamic shared memory
            stream,  # stream
            args,  # kernel arguments
            0,  # extra (ignore)
        )
    )

    if command_line_config.profile_range:
        checkCudaErrors(cuda.cuProfilerStop())

    # Get the output vector from device to host
    checkCudaErrors(
        cuda.cuMemcpyDtoHAsync(hOut.ctypes.data, dOutclass, BUFFER_SIZE, stream)
    )

    checkCudaErrors(cuda.cuStreamSynchronize(stream))

    # Freeing device memory
    checkCudaErrors(cuda.cuMemFree(dXclass))
    checkCudaErrors(cuda.cuMemFree(dYclass))
    checkCudaErrors(cuda.cuMemFree(dOutclass))

    if command_line_config.profiling_enabled:
        if not command_line_config.profile_range:
            cupti_common.cupti_activity_flush()

    if cupti_common.verify_result(hX, hY, hOut) != 0:
        return -1

    if cupti_common.global_error_count != 0:
        return -2

    return 0


if __name__ == "__main__":
    error_code = main(sys.argv[1:])
    if error_code:
        print(f"Failed with error code: {error_code}")
    sys.exit(error_code)
