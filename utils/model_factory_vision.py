# utils/model_factory_vision.py
from __future__ import annotations

import os
import warnings
from typing import Any, Callable, Dict, Optional


VisionCallable = Callable[[bytes], Optional[str]]


class VisionModelFactory:
    """
    provider 抽象化のみを担当する Factory。

    - 無料/有料の区別はしない（models_vision.py が制御）
    - 実体に触れた瞬間だけ warning → None
    - Router がローテーションと最終失敗を担当する
    """

    @staticmethod
    def create(config: Dict[str, Any]) -> Optional[VisionCallable]:
        provider = config.get("provider")

        try:
            if provider == "openai":
                return VisionModelFactory._create_openai_callable(config)
            if provider == "anthropic":
                return VisionModelFactory._create_anthropic_callable(config)
            if provider == "google":
                return VisionModelFactory._create_google_callable(config)

            warnings.warn(f"Unsupported provider '{provider}'. Skipping.")
            return None

        except Exception as e:
            warnings.warn(f"Failed to initialize model '{config}': {e}. Skipping.")
            return None

    # -------------------------
    # OpenAI Vision
    # -------------------------
    @staticmethod
    def _create_openai_callable(config: Dict[str, Any]) -> Optional[VisionCallable]:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            warnings.warn("OPENAI_API_KEY missing. Skipping.")
            return None

        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            warnings.warn(f"Failed to initialize OpenAI client: {e}. Skipping.")
            return None

        model = config["model"]

        def model_callable(image_bytes: bytes) -> Optional[str]:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_image", "image": image_bytes},
                                {"type": "text", "text": "Extract text from this image."},
                            ],
                        }
                    ],
                )
                return resp.choices[0].message.content
            except Exception as e:
                warnings.warn(f"OpenAI vision model '{model}' failed: {e}. Skipping.")
                return None

        return model_callable

    # -------------------------
    # Anthropic Vision
    # -------------------------
    @staticmethod
    def _create_anthropic_callable(config: Dict[str, Any]) -> Optional[VisionCallable]:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            warnings.warn("ANTHROPIC_API_KEY missing. Skipping.")
            return None

        try:
            client = Anthropic(api_key=api_key)
        except Exception as e:
            warnings.warn(f"Failed to initialize Anthropic client: {e}. Skipping.")
            return None

        model = config["model"]

        def model_callable(image_bytes: bytes) -> Optional[str]:
            try:
                resp = client.messages.create(
                    model=model,
                    max_tokens=2048,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_image", "image": image_bytes},
                                {"type": "text", "text": "Extract text from this image."},
                            ],
                        }
                    ],
                )
                return resp.content[0].text
            except Exception as e:
                warnings.warn(f"Anthropic vision model '{model}' failed: {e}. Skipping.")
                return None

        return model_callable

    # -------------------------
    # Google Gemini Vision
    # -------------------------
    @staticmethod
    def _create_google_callable(config: Dict[str, Any]) -> Optional[VisionCallable]:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            warnings.warn("GOOGLE_API_KEY missing. Skipping.")
            return None

        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            warnings.warn(f"Failed to configure Google API: {e}. Skipping.")
            return None

        model_name = config["model"]

        try:
            model = genai.GenerativeModel(model_name)
        except Exception as e:
            warnings.warn(f"Failed to initialize Google vision model '{model_name}': {e}. Skipping.")
            return None

        def model_callable(image_bytes: bytes) -> Optional[str]:
            try:
                resp = model.generate_content(
                    [
                        {"mime_type": "image/jpeg", "data": image_bytes},
                        "Extract text from this image.",
                    ]
                )
                return resp.text
            except Exception as e:
                warnings.warn(f"Google vision model '{model_name}' failed: {e}. Skipping.")
                return None

        return model_callable
