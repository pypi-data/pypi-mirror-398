from enum import Enum


class Quantization(str, Enum):
    AQLM = "aqlm"
    AWQ = "awq"
    AWQ_MARLIN = "awq_marlin"
    BITSANDBYTES = "bitsandbytes"
    COMPRESSED_TENSORS = "compressed-tensors"
    DEEPSPEEDFP = "deepspeedfp"
    EXPERTS_INT8 = "experts_int8"
    FBGEMM_FP8 = "fbgemm_fp8"
    FP8 = "fp8"
    GGUF = "gguf"
    GPTQ = "gptq"
    GPTQ_MARLIN = "gptq_marlin"
    GPTQ_MARLIN24 = "gptq_marlin24"
    HQQ = "hqq"
    IPEX = "ipex"
    MARLIN = "marlin"
    MODELOPT = "modelopt"
    MXFP6 = "mxfp6"
    NEURON_QUANT = "neuron_quant"
    NONE = "none"
    QQQ = "qqq"
    TPU_INT8 = "tpu_int8"

    def __str__(self) -> str:
        return str(self.value)
