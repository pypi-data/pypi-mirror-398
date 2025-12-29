from enum import Enum

class SourceEnum(str, Enum):
    modelscope = "modelscope"
    huggingface = "huggingface"
