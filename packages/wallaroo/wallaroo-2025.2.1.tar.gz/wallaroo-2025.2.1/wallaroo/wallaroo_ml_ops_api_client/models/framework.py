from enum import Enum


class Framework(str, Enum):
    CUSTOM = "custom"
    HUGGING_FACE_AUTOMATIC_SPEECH_RECOGNITION = (
        "hugging-face-automatic-speech-recognition"
    )
    HUGGING_FACE_FEATURE_EXTRACTION = "hugging-face-feature-extraction"
    HUGGING_FACE_IMAGE_CLASSIFICATION = "hugging-face-image-classification"
    HUGGING_FACE_IMAGE_SEGMENTATION = "hugging-face-image-segmentation"
    HUGGING_FACE_IMAGE_TO_TEXT = "hugging-face-image-to-text"
    HUGGING_FACE_OBJECT_DETECTION = "hugging-face-object-detection"
    HUGGING_FACE_QUESTION_ANSWERING = "hugging-face-question-answering"
    HUGGING_FACE_SENTIMENT_ANALYSIS = "hugging-face-sentiment-analysis"
    HUGGING_FACE_STABLE_DIFFUSION_TEXT_2_IMG = (
        "hugging-face-stable-diffusion-text-2-img"
    )
    HUGGING_FACE_SUMMARIZATION = "hugging-face-summarization"
    HUGGING_FACE_TEXT_CLASSIFICATION = "hugging-face-text-classification"
    HUGGING_FACE_TEXT_GENERATION = "hugging-face-text-generation"
    HUGGING_FACE_TRANSLATION = "hugging-face-translation"
    HUGGING_FACE_ZERO_SHOT_CLASSIFICATION = "hugging-face-zero-shot-classification"
    HUGGING_FACE_ZERO_SHOT_IMAGE_CLASSIFICATION = (
        "hugging-face-zero-shot-image-classification"
    )
    HUGGING_FACE_ZERO_SHOT_OBJECT_DETECTION = "hugging-face-zero-shot-object-detection"
    KERAS = "keras"
    MLFLOW = "mlflow"
    ONNX = "onnx"
    PYTHON = "python"
    PYTORCH = "pytorch"
    SKLEARN = "sklearn"
    TENSORFLOW = "tensorflow"
    VLLM = "vllm"
    XGBOOST = "xgboost"

    def __str__(self) -> str:
        return str(self.value)
