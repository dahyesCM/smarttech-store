import io
import logging
import os

import requests
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import local_vision
from .api import ProductSerializer
from .models import Product

logger = logging.getLogger(__name__)
MODEL = "google/vit-base-patch16-224"
MODEL_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL}"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def classify(request):
    upload = request.FILES.get("image")
    if not upload or upload.size > 5 * 1024 * 1024:
        return Response({"detail": "Selecciona una imagen de hasta 5 MB."}, status=400)
    try:
        with Image.open(upload) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"} or image.width * image.height > 16_000_000:
                return Response({"detail": "Usa JPEG, PNG o WebP de hasta 16 megapíxeles."}, status=400)
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((768, 768))

    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        return Response({"detail": "El archivo no se pudo leer como imagen."}, status=400)

    token = os.environ.get("HF_TOKEN")
    model = MODEL if token else local_vision.MODEL
    try:
        if token:
            payload = io.BytesIO()
            image.save(payload, format="JPEG")
            result = requests.post(
                MODEL_URL, data=payload.getvalue(), timeout=(5, 45),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"},
            )
            result.raise_for_status()
            predictions = result.json()
        else:
            predictions = local_vision.predict(image)
        if not isinstance(predictions, list) or not all(
            isinstance(item, dict) and isinstance(item.get("label"), str) for item in predictions
        ):
            raise ValueError("Formato inesperado")
    except (FileNotFoundError, ImportError):
        return Response({"detail": "Instala las dependencias y ejecuta python manage.py download_vision_model."}, status=503)
    except Exception:
        logger.exception("Falló la clasificación de imágenes con %s", model)
        return Response({"detail": "No se pudo clasificar la imagen. Inténtalo de nuevo."}, status=502)

    labels = {
        label.strip().casefold()
        for prediction in predictions[:3]
        for label in prediction["label"].split(",")
    }
    matches = [
        product for product in Product.objects.filter(active=True).exclude(ai_labels="")
        if labels.intersection(label.strip().casefold() for label in product.ai_labels.split(","))
    ]
    return Response({"model": model, "predictions": predictions[:3],
                     "products": ProductSerializer(matches, many=True).data})
