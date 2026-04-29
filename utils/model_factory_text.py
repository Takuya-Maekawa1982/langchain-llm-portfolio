# utils/model_factory_text.py
from __future__ import annotations

import os
import warnings
from typing import Any, Callable, Dict, Optional


TextCallable = Callable[[str], Optional[str]]


class TextModelFactory:
    """
    provider 抽象化のみを担当する Factory。

    - 無料/有料の区別はしない（models_texts.py が制御）
    - 実体に触れた瞬間だけ warning → None
    - Router がローテーションと最終失敗を担当する
    """

    @staticmethod
    def create(config: Dict[str, Any]) -> Optional[TextCallable]:
        provider = config.get("provider")

        try:
            if provider == "openrouter":
                return TextModelFactory._create_openrouter_callable(config)
            if provider == "google":
                return TextModelFactory._create_google_callable(config)
            if provider == "groq":
                return TextModelFactory._create_groq_callable(config)

            warnings.warn(f"Unsupported provider '{provider}'. Skipping.")
            return None

        except Exception as e:
            warnings.warn(f"Failed to initialize model '{config}': {e}. Skipping.")
            return None

    # -------------------------
    # OpenRouter
    # -------------------------
    @staticmethod
    def _create_openrouter_callable(config: Dict[str, Any]) -> Optional[TextCallable]:
        import requests

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            warnings.warn("OPENROUTER_API_KEY missing. Skipping.")
            return None

        model = config["model"]
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        def model_callable(prompt: str) -> Optional[str]:
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                warnings.warn(f"OpenRouter model '{model}' failed: {e}. Skipping.")
                return None

        return model_callable

    # -------------------------
    # Google Gemini
    # -------------------------
    @staticmethod
    def _create_google_callable(config: Dict[str, Any]) -> Optional[TextCallable]:
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

        # 実体に触れる瞬間
        try:
            model = genai.GenerativeModel(model_name)
        except Exception as e:
            warnings.warn(f"Failed to initialize Google model '{model_name}': {e}. Skipping.")
            return None

        def model_callable(prompt: str) -> Optional[str]:
            try:
                resp = model.generate_content(prompt)
                return resp.text
            except Exception as e:
                warnings.warn(f"Google model '{model_name}' failed: {e}. Skipping.")
                return None

        return model_callable

    # -------------------------
    # Groq
    # -------------------------
    @staticmethod
    def _create_groq_callable(config: Dict[str, Any]) -> Optional[TextCallable]:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            warnings.warn("GROQ_API_KEY missing. Skipping.")
            return None

        try:
            client = Groq(api_key=api_key)
        except Exception as e:
            warnings.warn(f"Failed to initialize Groq client: {e}. Skipping.")
            return None

        model = config["model"]

        def model_callable(prompt: str) -> Optional[str]:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.choices[0].message.content
            except Exception as e:
                warnings.warn(f"Groq model '{model}' failed: {e}. Skipping.")
                return None

        return model_callable
