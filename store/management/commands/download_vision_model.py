import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from store.local_vision import LABELS_FILE, MODEL, MODEL_FILE


MODEL_SHA256 = "c0c3f76d93fa3fd6580652a45618618a220fced18babf65774ed169de0432ad5"


class Command(BaseCommand):
    help = "Descarga el clasificador MobileNetV2 y sus etiquetas desde Hugging Face."

    def handle(self, *args, **options):
        directory = settings.BASE_DIR / ".models"
        directory.mkdir(exist_ok=True)
        files = {
            MODEL_FILE: f"https://huggingface.co/{MODEL}/resolve/main/{MODEL_FILE}",
            LABELS_FILE: f"https://huggingface.co/datasets/huggingface/label-files/resolve/main/{LABELS_FILE}",
        }
        for name, url in files.items():
            try:
                response = requests.get(url, timeout=(8, 60))
                response.raise_for_status()
                data = response.content
                if name == MODEL_FILE and hashlib.sha256(data).hexdigest() != MODEL_SHA256:
                    raise ValueError("La suma SHA-256 del modelo no coincide.")
                if name == LABELS_FILE:
                    labels = json.loads(data)
                    if not isinstance(labels, dict) or len(labels) != 1000:
                        raise ValueError("El archivo no contiene las 1000 etiquetas de ImageNet.")
                with NamedTemporaryFile(dir=directory, delete_on_close=False) as stream:
                    stream.write(data)
                    stream.flush()
                    Path(stream.name).replace(directory / name)
            except (requests.RequestException, OSError, ValueError) as exc:
                raise CommandError(f"No se pudo preparar {name}: {exc}") from exc
        self.stdout.write(self.style.SUCCESS("Modelo de Hugging Face listo para ejecutar en Fedora."))
