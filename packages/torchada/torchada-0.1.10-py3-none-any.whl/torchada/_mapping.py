"""
CUDA to MUSA mapping rules for source code porting.

This module contains the comprehensive mapping dictionary for converting
CUDA-specific symbols to their MUSA equivalents during extension builds.
"""

# Extension file suffix mappings
# Convert .cu/.cuh to .mu/.muh so torch_musa's musa_compile rule works correctly
# The musa_compile rule in torch_musa only adds -x musa for .mu/.muh files
# Without this conversion, .cu files would be treated as CUDA files by mcc
# and the --offload-arch=mp_XX flag would fail with clang's CUDA support
EXT_REPLACED_MAPPING = {
    "cuh": "muh",
    "cu": "mu",
    "cc": "cc",
    "cpp": "cpp",
    "cxx": "cxx",
}

# Comprehensive CUDA to MUSA symbol mapping
_MAPPING_RULE = {
    # ATen header mappings (use torch_musa specific paths)
    "#include <ATen/cuda/Atomic.cuh>": '#include "torch_musa/share/generated_cuda_compatible/include/ATen/musa/Atomic.muh"',
    "#include <ATen/cuda/CUDAContext.h>": '#include "torch_musa/csrc/aten/musa/MUSAContext.h"',
    "#include <ATen/cuda/CUDADataType.h>": '#include "torch_musa/csrc/aten/musa/MUSADtype.muh"',
    "#include <ATen/cuda/CUDAGeneratorImpl.h>": '#include "torch_musa/csrc/aten/musa/CUDAGeneratorImpl.h"',
    "#include <ATen/cuda/detail/UnpackRaw.cuh>": '#include "torch_musa/csrc/aten/musa/UnpackRaw.muh"',
    "#include <ATen/cuda/Exceptions.h>": '#include "torch_musa/csrc/aten/musa/Exceptions.h"',
    "at::cuda": "at::musa",
    "torch::kCUDA": "torch::kMUSA",
    # File extension mappings for include statements (.cuh -> .muh)
    # Both quoted includes and angle-bracket includes
    '.cuh"': '.muh"',
    ".cuh>": ".muh>",
    # C10 header mappings (use torch_musa specific paths)
    "#include <c10/cuda/CUDAException.h>": '#include "torch_musa/csrc/core/MUSAException.h"',
    "#include <c10/cuda/CUDAGuard.h>": '#include "torch_musa/csrc/core/MUSAGuard.h"',
    "#include <c10/cuda/CUDAStream.h>": '#include "torch_musa/csrc/core/MUSAStream.h"',
    "c10::cuda": "c10::musa",
    # C10 CUDA macros
    "C10_CUDA_KERNEL_LAUNCH_CHECK": "C10_MUSA_KERNEL_LAUNCH_CHECK",
    "C10_CUDA_CHECK": "C10_MUSA_CHECK",
    "C10_CUDA_ERROR_HANDLED": "C10_MUSA_ERROR_HANDLED",
    "C10_CUDA_IGNORE_ERROR": "C10_MUSA_IGNORE_ERROR",
    # C10 CUDA header file mappings (must come before generic c10/cuda mapping)
    "c10/cuda/CUDAException.h": "c10/musa/MUSAException.h",
    "c10/cuda/CUDAStream.h": "c10/musa/MUSAStream.h",
    "c10/cuda/CUDAGuard.h": "c10/musa/MUSAGuard.h",
    "c10/cuda/CUDAFunctions.h": "c10/musa/MUSAFunctions.h",
    "c10/cuda/CUDAMacros.h": "c10/musa/MUSAMacros.h",
    "c10/cuda/CUDACachingAllocator.h": "c10/musa/MUSACachingAllocator.h",
    "<c10/cuda/CUDAStream.h>": '"torch_musa/csrc/core/MUSAStream.h"',
    # Generic c10/cuda mapping (after specific mappings)
    "c10/cuda": "c10/musa",
    # CUDA standard library -> MUSA standard library
    "cuda/std": "musa/std",
    "<cuda/functional>": "<musa/functional>",
    "<cuda/std/": "<musa/std/",
    "#include <cuda/": "#include <musa/",
    # CUDA namespaces and paths
    "torch::cuda": "torch::musa",
    "torch.cuda": "torch.musa",
    "at::kCUDA": "at::kMUSA",
    "at::DeviceType::CUDA": "at::DeviceType::MUSA",
    "c10::DeviceType::CUDA": "c10::DeviceType::MUSA",
    # cuBLAS -> muBLAS
    "cublas": "mublas",
    "CUBLAS": "MUBLAS",
    "cublasHandle_t": "mublasHandle_t",
    "cublasStatus_t": "mublasStatus_t",
    "cublasCreate": "mublasCreate",
    "cublasDestroy": "mublasDestroy",
    "cublasSetStream": "mublasSetStream",
    "cublasGetStream": "mublasGetStream",
    "cublasSgemm": "mublasSgemm",
    "cublasDgemm": "mublasDgemm",
    "cublasHgemm": "mublasHgemm",
    "cublasGemmEx": "mublasGemmEx",
    "cublasGemmBatchedEx": "mublasGemmBatchedEx",
    "cublasGemmStridedBatchedEx": "mublasGemmStridedBatchedEx",
    "cublasSgemmBatched": "mublasSgemmBatched",
    "cublasDgemmBatched": "mublasDgemmBatched",
    "cublasSgemmStridedBatched": "mublasSgemmStridedBatched",
    "cublasDgemmStridedBatched": "mublasDgemmStridedBatched",
    # cuBLASLt specific mappings
    "CUBLASLT_MATMUL_DESC_A_SCALE_POINTER": "MUBLASLT_MATMUL_DESC_A_SCALE_POINTER",
    "CUBLASLT_MATMUL_DESC_B_SCALE_POINTER": "MUBLASLT_MATMUL_DESC_B_SCALE_POINTER",
    "CUBLASLT_MATMUL_DESC_FAST_ACCUM": "MUBLASLT_MATMUL_DESC_FAST_ACCUM",
    "CUBLASLT_MATMUL_DESC_TRANSA": "MUBLASLT_MATMUL_DESC_TRANSA",
    "CUBLASLT_MATMUL_DESC_TRANSB": "MUBLASLT_MATMUL_DESC_TRANSB",
    "CUBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES": "MUBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES",
    "CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT": "MUBLASLT_MATRIX_LAYOUT_BATCH_COUNT",
    "CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET": "MUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET",
    "CUBLAS_COMPUTE_32F": "MUBLAS_COMPUTE_32F",
    "CUBLAS_OP_N": "MUBLAS_OP_N",
    "CUBLAS_OP_T": "MUBLAS_OP_T",
    "CUBLAS_STATUS_NOT_SUPPORTED": "MUBLAS_STATUS_NOT_IMPLEMENTED",
    "CUBLAS_STATUS_SUCCESS": "MUBLAS_STATUS_SUCCESS",
    "cublasComputeType_t": "mublasComputeType_t",
    "cublasGetStatusString": "mublasGetStatusString",
    "cublasLtHandle_t": "mublasLtHandle_t",
    "cublasLtMatmul": "mublasLtMatmul",
    "cublasLtMatmulAlgoGetHeuristic": "mublasLtMatmulAlgoGetHeuristic",
    "cublasLtMatmulDescAttributes_t": "mublasLtMatmulDescAttributes_t",
    "cublasLtMatmulDescCreate": "mublasLtMatmulDescCreate",
    "cublasLtMatmulDescDestroy": "mublasLtMatmulDescDestroy",
    "cublasLtMatmulDescOpaque_t": "mublasLtMatmulDescOpaque_t",
    "cublasLtMatmulDescSetAttribute": "mublasLtMatmulDescSetAttribute",
    "cublasLtMatmulDesc_t": "mublasLtMatmulDesc_t",
    "cublasLtMatmulHeuristicResult_t": "mublasLtMatmulHeuristicResult_t",
    "cublasLtMatmulPreferenceAttributes_t": "mublasLtMatmulPreferenceAttributes_t",
    "cublasLtMatmulPreferenceCreate": "mublasLtMatmulPreferenceCreate",
    "cublasLtMatmulPreferenceDestroy": "mublasLtMatmulPreferenceDestroy",
    "cublasLtMatmulPreferenceOpaque_t": "mublasLtMatmulPreferenceOpaque_t",
    "cublasLtMatmulPreferenceSetAttribute": "mublasLtMatmulPreferenceSetAttribute",
    "cublasLtMatmulPreference_t": "mublasLtMatmulPreference_t",
    "cublasLtMatrixLayoutAttribute_t": "mublasLtMatrixLayoutAttribute_t",
    "cublasLtMatrixLayoutCreate": "mublasLtMatrixLayoutCreate",
    "cublasLtMatrixLayoutDestroy": "mublasLtMatrixLayoutDestroy",
    "cublasLtMatrixLayoutOpaque_t": "mublasLtMatrixLayoutOpaque_t",
    "cublasLtMatrixLayoutSetAttribute": "mublasLtMatrixLayoutSetAttribute",
    "cublasLtMatrixLayout_t": "mublasLtMatrixLayout_t",
    # cuRAND -> muRAND
    "curand": "murand",
    "CURAND": "MURAND",
    "curandState": "murandState",
    "curandStatePhilox4_32_10_t": "murandStatePhilox4_32_10_t",
    "curand_init": "murand_init",
    "curand_uniform": "murand_uniform",
    "curand_uniform4": "murand_uniform4",
    "curand_normal": "murand_normal",
    "curand_normal4": "murand_normal4",
    # cuDNN -> muDNN
    "cudnn": "mudnn",
    "CUDNN": "MUDNN",
    "cudnnHandle_t": "mudnnHandle_t",
    "cudnnCreate": "mudnnCreate",
    "cudnnDestroy": "mudnnDestroy",
    # CUDA Runtime
    "cudaMalloc": "musaMalloc",
    "cudaFree": "musaFree",
    "cudaMemcpy": "musaMemcpy",
    "cudaMemcpyAsync": "musaMemcpyAsync",
    "cudaMemset": "musaMemset",
    "cudaMemsetAsync": "musaMemsetAsync",
    "cudaDeviceSynchronize": "musaDeviceSynchronize",
    "cudaStreamSynchronize": "musaStreamSynchronize",
    "cudaGetDevice": "musaGetDevice",
    "cudaSetDevice": "musaSetDevice",
    "cudaGetDeviceCount": "musaGetDeviceCount",
    "cudaGetDeviceProperties": "musaGetDeviceProperties",
    "cudaDeviceGetAttribute": "musaDeviceGetAttribute",
    # CUDA Stream/Event
    "cudaStream_t": "musaStream_t",
    "cudaEvent_t": "musaEvent_t",
    "cudaStreamCreate": "musaStreamCreate",
    "cudaStreamDestroy": "musaStreamDestroy",
    "cudaEventCreate": "musaEventCreate",
    "cudaEventDestroy": "musaEventDestroy",
    "cudaEventRecord": "musaEventRecord",
    "cudaEventSynchronize": "musaEventSynchronize",
    "cudaEventElapsedTime": "musaEventElapsedTime",
    "cudaStreamWaitEvent": "musaStreamWaitEvent",
    # CUDA Error handling
    "cudaError_t": "musaError_t",
    "cudaSuccess": "musaSuccess",
    "cudaGetLastError": "musaGetLastError",
    "cudaGetErrorString": "musaGetErrorString",
    "cudaPeekAtLastError": "musaPeekAtLastError",
    # CUDA Memory types
    "cudaMemcpyHostToDevice": "musaMemcpyHostToDevice",
    "cudaMemcpyDeviceToHost": "musaMemcpyDeviceToHost",
    "cudaMemcpyDeviceToDevice": "musaMemcpyDeviceToDevice",
    "cudaMemcpyHostToHost": "musaMemcpyHostToHost",
    # Data types
    # Note: __half and half are the same in MUSA, no mapping needed
    "__nv_bfloat16": "__mt_bfloat16",
    "__nv_bfloat162": "__mt_bfloat162",
    "nv_bfloat16": "__mt_bfloat16",
    "nv_bfloat162": "__mt_bfloat162",
    "__nv_half": "__half",
    "nv_half": "__half",
    # FP8 data types
    "__NV_E4M3": "__MT_E4M3",
    "__NV_E5M2": "__MT_E5M2",
    "__NV_SATFINITE": "__MT_SATFINITE",
    "__nv_cvt_float2_to_fp8x2": "__musa_cvt_float2_to_fp8x2",
    "__nv_fp8_e4m3": "__mt_fp8_e4m3",
    "__nv_fp8_e5m2": "__mt_fp8_e5m2",
    "__nv_fp8x2_e4m3": "__mt_fp8x2_e4m3",
    "__nv_fp8x2_e5m2": "__mt_fp8x2_e5m2",
    "__nv_fp8x2_storage_t": "__mt_fp8x2_storage_t",
    "__nv_fp8x4_e4m3": "__mt_fp8x4_e4m3",
    "__nv_fp8x4_e5m2": "__mt_fp8x4_e5m2",
    "__nv_fp8x4_storage_t": "__mt_fp8x4_storage_t",
    "#include <cuda_fp8.h>": "#include <musa_fp8.h>",
    "CUDA_R_8F_E4M3": "MUSA_R_8F_E4M3",
    "CUDA_R_8F_E5M2": "MUSA_R_8F_E5M2",
    # Cutlass -> Mutlass
    '#include "cutlass/array.h"': "#include <mutlass/array.h>",
    "#include <cutlass/array.h>": "#include <mutlass/array.h>",
    "#include <cutlass/cutlass.h>": "#include <mutlass/mutlass.h>",
    "#include <cutlass/numeric_types.h>": "#include <mutlass/numeric_types.h>",
    "cutlass::AlignedArray": "mutlass::AlignedArray",
    "cutlass::bfloat16_t": "mutlass::bfloat16_t",
    "cutlass::half_t": "mutlass::half_t",
    "cutlass": "mutlass",
    "CUTLASS": "MUTLASS",
    "cutlass/": "mutlass/",
    "cutlass::": "mutlass::",
    # CUB - MUSA provides cub directly, no conversion needed (no mapping needed)
    # Thrust
    "thrust::cuda": "thrust::musa",
    # NCCL -> MCCL
    "nccl": "mccl",
    "NCCL": "MCCL",
    "ncclComm_t": "mcclComm_t",
    "ncclDataType_t": "mcclDataType_t",
    "ncclRedOp_t": "mcclRedOp_t",
    "ncclResult_t": "mcclResult_t",
    "ncclSuccess": "mcclSuccess",
    # cuSPARSE -> muSPARSE
    "cusparse": "musparse",
    "CUSPARSE": "MUSPARSE",
    "cusparseHandle_t": "musparseHandle_t",
    "cusparseCreate": "musparseCreate",
    "cusparseDestroy": "musparseDestroy",
    # cuSOLVER -> muSOLVER
    "cusolver": "musolver",
    "CUSOLVER": "MUSOLVER",
    "cusolverDnHandle_t": "musolverDnHandle_t",
    "cusolverDnCreate": "musolverDnCreate",
    "cusolverDnDestroy": "musolverDnDestroy",
    # cuFFT -> muFFT
    "cufft": "mufft",
    "CUFFT": "MUFFT",
    "cufftHandle": "mufftHandle",
    "cufftPlan1d": "mufftPlan1d",
    "cufftPlan2d": "mufftPlan2d",
    "cufftPlan3d": "mufftPlan3d",
    "cufftExecC2C": "mufftExecC2C",
    "cufftExecR2C": "mufftExecR2C",
    "cufftExecC2R": "mufftExecC2R",
    # CUDA kernel launch syntax - same in MUSA, no mapping needed
    # CUDA device attributes
    "cudaDevAttrMaxThreadsPerBlock": "musaDevAttrMaxThreadsPerBlock",
    "cudaDevAttrMaxBlockDimX": "musaDevAttrMaxBlockDimX",
    "cudaDevAttrMaxBlockDimY": "musaDevAttrMaxBlockDimY",
    "cudaDevAttrMaxBlockDimZ": "musaDevAttrMaxBlockDimZ",
    "cudaDevAttrMaxGridDimX": "musaDevAttrMaxGridDimX",
    "cudaDevAttrMaxGridDimY": "musaDevAttrMaxGridDimY",
    "cudaDevAttrMaxGridDimZ": "musaDevAttrMaxGridDimZ",
    "cudaDevAttrMaxSharedMemoryPerBlock": "musaDevAttrMaxSharedMemoryPerBlock",
    "cudaDevAttrWarpSize": "musaDevAttrWarpSize",
    "cudaDevAttrMultiProcessorCount": "musaDevAttrMultiProcessorCount",
    # Additional PyTorch CUDA utilities
    "getCurrentCUDAStream": "getCurrentMUSAStream",
    "getDefaultCUDAStream": "getDefaultMUSAStream",
    "CUDAStream": "MUSAStream",
    "CUDAGuard": "MUSAGuard",
    "OptionalCUDAGuard": "OptionalMUSAGuard",
    "CUDAStreamGuard": "MUSAStreamGuard",
    "CUDAEvent": "MUSAEvent",
    # CUDA includes to MUSA
    "cuda_runtime.h": "musa_runtime.h",
    "cuda_runtime_api.h": "musa_runtime_api.h",
    "cuda.h": "musa.h",
    "cuda_fp16.h": "musa_fp16.h",
    "cuda_bf16.h": "musa_bf16.h",
    # Additional CUDA runtime functions
    "cudaHostAlloc": "musaHostAlloc",
    "cudaHostFree": "musaHostFree",
    "cudaMallocHost": "musaMallocHost",
    "cudaFreeHost": "musaFreeHost",
    "cudaMallocManaged": "musaMallocManaged",
    "cudaMallocAsync": "musaMallocAsync",
    "cudaFreeAsync": "musaFreeAsync",
    "cudaMemcpy2D": "musaMemcpy2D",
    "cudaMemcpy2DAsync": "musaMemcpy2DAsync",
    "cudaMemcpy3D": "musaMemcpy3D",
    "cudaMemcpy3DAsync": "musaMemcpy3DAsync",
    "cudaMemGetInfo": "musaMemGetInfo",
    "cudaMemPrefetchAsync": "musaMemPrefetchAsync",
    "cudaPointerGetAttributes": "musaPointerGetAttributes",
    # CUDA stream flags and types
    "cudaStreamDefault": "musaStreamDefault",
    "cudaStreamNonBlocking": "musaStreamNonBlocking",
    "cudaStreamCreateWithFlags": "musaStreamCreateWithFlags",
    "cudaStreamCreateWithPriority": "musaStreamCreateWithPriority",
    "cudaStreamQuery": "musaStreamQuery",
    "cudaStreamGetPriority": "musaStreamGetPriority",
    "cudaStreamGetFlags": "musaStreamGetFlags",
    # CUDA event flags
    "cudaEventDefault": "musaEventDefault",
    "cudaEventBlockingSync": "musaEventBlockingSync",
    "cudaEventDisableTiming": "musaEventDisableTiming",
    "cudaEventCreateWithFlags": "musaEventCreateWithFlags",
    "cudaEventQuery": "musaEventQuery",
    # CUDA memory flags
    "cudaHostAllocDefault": "musaHostAllocDefault",
    "cudaHostAllocPortable": "musaHostAllocPortable",
    "cudaHostAllocMapped": "musaHostAllocMapped",
    "cudaHostAllocWriteCombined": "musaHostAllocWriteCombined",
    "cudaMemoryTypeHost": "musaMemoryTypeHost",
    "cudaMemoryTypeDevice": "musaMemoryTypeDevice",
    "cudaMemoryTypeManaged": "musaMemoryTypeManaged",
    # Device management
    "cudaDeviceReset": "musaDeviceReset",
    "cudaDeviceSetCacheConfig": "musaDeviceSetCacheConfig",
    "cudaDeviceGetCacheConfig": "musaDeviceGetCacheConfig",
    "cudaDeviceSetSharedMemConfig": "musaDeviceSetSharedMemConfig",
    "cudaDeviceGetSharedMemConfig": "musaDeviceGetSharedMemConfig",
    "cudaGetDeviceFlags": "musaGetDeviceFlags",
    "cudaSetDeviceFlags": "musaSetDeviceFlags",
    "cudaDeviceCanAccessPeer": "musaDeviceCanAccessPeer",
    "cudaDeviceEnablePeerAccess": "musaDeviceEnablePeerAccess",
    "cudaDeviceDisablePeerAccess": "musaDeviceDisablePeerAccess",
    # CUDA occupancy
    "cudaOccupancyMaxActiveBlocksPerMultiprocessor": "musaOccupancyMaxActiveBlocksPerMultiprocessor",
    "cudaOccupancyMaxPotentialBlockSize": "musaOccupancyMaxPotentialBlockSize",
    # Additional device properties
    "cudaDeviceProp": "musaDeviceProp",
    "cudaFuncAttributes": "musaFuncAttributes",
    "cudaFuncGetAttributes": "musaFuncGetAttributes",
    "cudaFuncSetAttribute": "musaFuncSetAttribute",
    "cudaFuncSetCacheConfig": "musaFuncSetCacheConfig",
    # CUDA texture/surface (if supported)
    "cudaTextureObject_t": "musaTextureObject_t",
    "cudaSurfaceObject_t": "musaSurfaceObject_t",
    "cudaCreateTextureObject": "musaCreateTextureObject",
    "cudaDestroyTextureObject": "musaDestroyTextureObject",
    "cudaCreateSurfaceObject": "musaCreateSurfaceObject",
    "cudaDestroySurfaceObject": "musaDestroySurfaceObject",
    # CUDA cooperative groups - same in MUSA, no mapping needed
    # Additional cuBLAS functions
    "cublasSetMathMode": "mublasSetMathMode",
    "cublasGetMathMode": "mublasGetMathMode",
    "CUBLAS_DEFAULT_MATH": "MUBLAS_DEFAULT_MATH",
    "CUBLAS_TENSOR_OP_MATH": "MUBLAS_TENSOR_OP_MATH",
    "cublasLtCreate": "mublasLtCreate",
    "cublasLtDestroy": "mublasLtDestroy",
    "cublasLtHandle_t": "mublasLtHandle_t",
    "cublasLtMatmul": "mublasLtMatmul",
    # Additional cuDNN functions
    "cudnnStatus_t": "mudnnStatus_t",
    "cudnnSetStream": "mudnnSetStream",
    "cudnnGetStream": "mudnnGetStream",
    "cudnnTensorDescriptor_t": "mudnnTensorDescriptor_t",
    "cudnnFilterDescriptor_t": "mudnnFilterDescriptor_t",
    "cudnnConvolutionDescriptor_t": "mudnnConvolutionDescriptor_t",
    "cudnnPoolingDescriptor_t": "mudnnPoolingDescriptor_t",
    "cudnnActivationDescriptor_t": "mudnnActivationDescriptor_t",
    "cudnnDropoutDescriptor_t": "mudnnDropoutDescriptor_t",
    "cudnnRNNDescriptor_t": "mudnnRNNDescriptor_t",
    "cudnnCreateTensorDescriptor": "mudnnCreateTensorDescriptor",
    "cudnnDestroyTensorDescriptor": "mudnnDestroyTensorDescriptor",
    "cudnnSetTensor4dDescriptor": "mudnnSetTensor4dDescriptor",
    "cudnnSetTensorNdDescriptor": "mudnnSetTensorNdDescriptor",
    # Flash attention and transformer related - same names, no mapping needed
    # Paged attention (vLLM specific) - same names, no mapping needed
    # Additional NCCL functions
    "ncclCommInitRank": "mcclCommInitRank",
    "ncclCommInitAll": "mcclCommInitAll",
    "ncclCommDestroy": "mcclCommDestroy",
    "ncclCommCount": "mcclCommCount",
    "ncclCommCuDevice": "mcclCommCuDevice",
    "ncclCommUserRank": "mcclCommUserRank",
    "ncclAllReduce": "mcclAllReduce",
    "ncclBroadcast": "mcclBroadcast",
    "ncclReduce": "mcclReduce",
    "ncclAllGather": "mcclAllGather",
    "ncclReduceScatter": "mcclReduceScatter",
    "ncclGroupStart": "mcclGroupStart",
    "ncclGroupEnd": "mcclGroupEnd",
    "ncclSend": "mcclSend",
    "ncclRecv": "mcclRecv",
    "ncclGetUniqueId": "mcclGetUniqueId",
    "ncclUniqueId": "mcclUniqueId",
    # CUDA math intrinsics - same in MUSA, no mapping needed
    # (__shfl_sync, __shfl_xor_sync, __shfl_up_sync, __shfl_down_sync,
    #  __ballot_sync, __any_sync, __all_sync, __syncthreads, __syncwarp,
    #  __threadfence, __threadfence_block, __threadfence_system)
    # Atomic operations - same in MUSA, no mapping needed
    # (atomicAdd, atomicSub, atomicExch, atomicMin, atomicMax, atomicInc,
    #  atomicDec, atomicCAS, atomicAnd, atomicOr, atomicXor)
    # CUDA math functions - same in MUSA, no mapping needed
    # (__float2half, __half2float, __float2half_rn, __float22half2_rn,
    #  __half22float2, __hadd, __hsub, __hmul, __hdiv, __hfma,
    #  __hadd2, __hsub2, __hmul2, __hfma2)
    # Common macros
    "CUDA_KERNEL_LOOP": "MUSA_KERNEL_LOOP",
    "CUDA_1D_KERNEL_LOOP": "MUSA_1D_KERNEL_LOOP",
    "CUDA_2D_KERNEL_LOOP": "MUSA_2D_KERNEL_LOOP",
    "CUDA_NUM_THREADS": "MUSA_NUM_THREADS",
    # GET_BLOCKS and DIVUP are common macros that don't need mapping
    # PyTorch C++ API cuda utilities
    "torch::cuda::getCurrentCUDAStream": "torch::musa::getCurrentMUSAStream",
    "torch::cuda::getDefaultCUDAStream": "torch::musa::getDefaultMUSAStream",
    "torch::cuda::getStreamFromPool": "torch::musa::getStreamFromPool",
    # torch::kCUDA maps to c10::DeviceType::PrivateUse1 (MUSA uses PrivateUse1 device type)
    # This is always available without needing extra includes
    "torch::kCUDA": "c10::DeviceType::PrivateUse1",
    # Device index utilities
    "cudaDeviceIndex": "musaDeviceIndex",
    "CUDADeviceIndex": "MUSADeviceIndex",
    # CUDA driver API -> MUSA driver API
    "CUdeviceptr": "MUdeviceptr",
    "CUdevice": "MUdevice",
    "CUcontext": "MUcontext",
    "CUmodule": "MUmodule",
    "CUfunction": "MUfunction",
    "CUstream": "MUstream",
    "CUevent": "MUevent",
    "CUresult": "MUresult",
    "cuPointerGetAttribute": "muPointerGetAttribute",
    "cuMemGetAddressRange": "muMemGetAddressRange",
    "cuCtxGetCurrent": "muCtxGetCurrent",
    "cuCtxSetCurrent": "muCtxSetCurrent",
    "cuDeviceGet": "muDeviceGet",
    "cuDeviceGetCount": "muDeviceGetCount",
    "cuInit": "muInit",
    "CU_POINTER_ATTRIBUTE_RANGE_START_ADDR": "MU_POINTER_ATTRIBUTE_RANGE_START_ADDR",
    "CU_POINTER_ATTRIBUTE_RANGE_SIZE": "MU_POINTER_ATTRIBUTE_RANGE_SIZE",
    "CU_POINTER_ATTRIBUTE_MEMORY_TYPE": "MU_POINTER_ATTRIBUTE_MEMORY_TYPE",
    "CU_POINTER_ATTRIBUTE_DEVICE_POINTER": "MU_POINTER_ATTRIBUTE_DEVICE_POINTER",
    "CU_POINTER_ATTRIBUTE_HOST_POINTER": "MU_POINTER_ATTRIBUTE_HOST_POINTER",
    "CU_POINTER_ATTRIBUTE_CONTEXT": "MU_POINTER_ATTRIBUTE_CONTEXT",
    "CUDA_SUCCESS": "MUSA_SUCCESS",
    "CUDA_ERROR_INVALID_VALUE": "MUSA_ERROR_INVALID_VALUE",
    "CUDA_ERROR_OUT_OF_MEMORY": "MUSA_ERROR_OUT_OF_MEMORY",
    "CUDA_ERROR_NOT_INITIALIZED": "MUSA_ERROR_NOT_INITIALIZED",
    # HIP -> MUSA mappings (for USE_ROCM code paths)
    "<hip/hip_runtime.h>": "<musa_runtime.h>",
    "hip/hip_runtime.h": "musa_runtime.h",
    "<hipcub/hipcub.hpp>": "<cub/cub.cuh>",
    "hipcub/hipcub.hpp": "cub/cub.cuh",
    "hipcub::": "cub::",
    "__hip_bfloat16": "__mt_bfloat16",
    # THC headers
    "#include <THC/THCAtomics.cuh>": "#include <THC/THCAtomics.muh>",
    # Template keyword fixes for mcc compiler
    ".FlagHeads<VEC_SIZE>": ".template FlagHeads<VEC_SIZE>",
    ".InclusiveSum<VEC_SIZE>": ".template InclusiveSum<VEC_SIZE>",
    ".Reduce<VEC_SIZE>": ".template Reduce<VEC_SIZE>",
    ".Sum<VEC_SIZE>": ".template Sum<VEC_SIZE>",
    "::cast<vec_size>": "::template cast<vec_size>",
    "SCHEDULER::execute": "SCHEDULER::template execute",
    # CUDA launch attributes
    "cudaLaunchAttribute": "musaLaunchAttribute",
    "cudaLaunchAttributeProgrammaticStreamSerialization": "musaLaunchAttributeIgnore",
    "cudaLaunchConfig_t": "musaLaunchConfig_t",
    # FlashInfer specific mappings
    ".is_cuda()": ".is_privateuseone()",
    "->philox_cuda_state": "->philox_musa_state",
    # CUDA arch guards
    "(__CUDA_ARCH__ < 800)": "(__MUSA_ARCH__ < 220)",
    "(__CUDA_ARCH__ >= 900)": "(__MUSA_ARCH__ >= 310)",
    # cuda::std namespace
    "cuda::std::numeric_limits": "musa::std::numeric_limits",
    "#include <cuda/std/functional>": "#include <musa/std/functional>",
    "#include <cuda/std/limits>": "#include <musa/std/limits>",
    # Compute capability checks
    "compute_capacity.first >= 8": "compute_capacity.first >= 3",
    # FlashInfer vec_dtypes.cuh - mcc compiler requires 'template' keyword
    "::cast<vec_size>": "::template cast<vec_size>",
    # FlashInfer norm.cuh - replace math.cuh with MUSA fast math functions
    '#include "math.cuh"': """
// MUSA fast math intrinsics (replacing flashinfer::math functions)
__device__ __forceinline__ float fast_rsqrtf(float x) { return __frsqrt_rn(x); }
__device__ __forceinline__ float fast_rcp(float x) { return __frcp_rn(x); }
""",
    # FlashInfer norm.cuh - replace math:: functions with MUSA intrinsics
    "math::shfl_xor_sync(sum_sq, offset);": "__shfl_xor_sync(0xffffffff, sum_sq, offset);",
    "math::rsqrt(smem[0] / float(d) + eps);": "fast_rsqrtf(smem[0] / float(d) + eps);",
    # FlashInfer sampling.cuh - replace math::ptx_rcp with fast_rcp
    "math::ptx_rcp(max(sum_low, 1e-8));": "fast_rcp(max(sum_low, 1e-8));",
    "math::ptx_rcp(denom);": "fast_rcp(denom);",
    # PTX assembly -> MUSA compatible code
    # ld.global.nc.b64 is non-cached load, st.global.cg.b64 is cache-global store
    # Replace with regular load/store since MUSA doesn't support PTX
    'asm volatile("ld.global.nc.b64 %0,[%1];" : "=l"(tmp) : "l"(src + j) : "memory");': "tmp = src[j];",
    'asm volatile("st.global.cg.b64 [%0],%1;" ::"l"(dst + j), "l"(tmp) : "memory");': "dst[j] = tmp;",
    # Memory barrier and atomic operations - replace PTX with atomics and fence
    'asm volatile("st.release.sys.global.u32 [%1], %0;" ::"r"(flag), "l"(flag_addr));': "__threadfence_system(); atomicExch(flag_addr, flag);",
    'asm volatile("membar.sys; st.volatile.global.u32 [%1], %0;" ::"r"(flag), "l"(flag_addr));': "__threadfence_system(); atomicExch(flag_addr, flag);",
    'asm volatile("ld.acquire.sys.global.u32 %0, [%1];" : "=r"(flag) : "l"(flag_addr));': "flag = atomicAdd(flag_addr, 0); __threadfence_system();",
    'asm volatile("ld.volatile.global.u32 %0, [%1]; membar.gl;" : "=r"(flag) : "l"(flag_addr));': "flag = atomicAdd(flag_addr, 0); __threadfence();",
    'asm volatile("st.volatile.global.u32 [%1], %0;" ::"r"(flag), "l"(flag_addr));': "atomicExch(flag_addr, flag);",
    'asm volatile("ld.volatile.global.u32 %0, [%1];" : "=r"(flag) : "l"(flag_addr));': "flag = atomicAdd(flag_addr, 0);",
    # MUSA compiler issue: __restrict__ in struct members causes copy issues
    # Remove __restrict__ from RankData.ptrs array
    "const void* __restrict__ ptrs[8]": "const void* ptrs[8]",
}
