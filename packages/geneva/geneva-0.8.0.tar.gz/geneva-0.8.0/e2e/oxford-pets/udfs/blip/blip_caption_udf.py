# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
BLIP caption UDF for GPU-accelerated image captioning.

This UDF uses Salesforce's BLIP model to generate image captions.
"""

import io
import logging
from collections.abc import Callable

import geneva

_LOG = logging.getLogger(__name__)


@geneva.udf(version="0.1", num_gpus=1.0)
class GenCaption(Callable):
    """
    Generate image captions using BLIP model.

    This is a GPU-accelerated stateful UDF.
    """

    def __init__(self) -> None:
        self.is_loaded = False

    def setup(self) -> None:
        from transformers import BlipForConditionalGeneration, BlipProcessor

        _LOG.info("Loading BLIP model for caption generation")
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )

        # Move to GPU if available
        import torch

        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
            _LOG.info("BLIP model loaded on GPU")
        else:
            _LOG.warning("GPU not available, BLIP model will run on CPU (slower)")

        self.is_loaded = True

    def __call__(self, image: bytes) -> str:
        import torch
        from PIL import Image

        if not self.is_loaded:
            self.setup()

        image_stream = io.BytesIO(image)
        raw_image = Image.open(image_stream).convert("RGB")

        inputs = self.processor([raw_image], return_tensors="pt")

        # Move inputs to GPU if model is on GPU
        if next(self.model.parameters()).is_cuda:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=50)

        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption
