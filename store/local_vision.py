"""CPU inference for the MobileNetV2 weights published on Hugging Face."""
import json
from functools import lru_cache

from django.conf import settings
from PIL import Image


MODEL = "onnxmodelzoo/mobilenetv2-12"
MODEL_FILE = "mobilenetv2-12.onnx"
LABELS_FILE = "imagenet-1k-id2label.json"


@lru_cache(maxsize=1)
def classifier():
    import onnxruntime

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = 2
    directory = settings.BASE_DIR / ".models"
    with (directory / LABELS_FILE).open(encoding="utf-8") as stream:
        labels = json.load(stream)
    session = onnxruntime.InferenceSession(
        str(directory / MODEL_FILE), sess_options=options, providers=["CPUExecutionProvider"],
    )
    return session, labels


def predict(image):
    import numpy as np

    session, labels = classifier()
    width, height = image.size
    side = min(width, height) * 224 / 256
    left = (width - side) / 2
    top = (height - side) / 2
    cropped = image.resize(
        (224, 224), Image.Resampling.BILINEAR, box=(left, top, left + side, top + side),
    )
    pixels = np.asarray(cropped, dtype=np.float32) / 255.0
    mean = np.array([.485, .456, .406], dtype=np.float32)
    std = np.array([.229, .224, .225], dtype=np.float32)
    tensor = ((pixels - mean) / std).transpose(2, 0, 1)[None, ...]
    scores = session.run(None, {session.get_inputs()[0].name: tensor})[0][0]
    exp = np.exp(scores - scores.max())
    confidence = exp / exp.sum()
    return [
        {"label": labels[str(index)], "score": float(confidence[index])}
        for index in np.argsort(confidence)[-3:][::-1]
    ]
