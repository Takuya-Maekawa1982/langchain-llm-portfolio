# utils/vision_llm_router.py
from __future__ import annotations

from typing import Dict, Any, List

from .models_vision import VISION_OCR_MODELS
from .model_factory_vision import VisionModelFactory


class VisionLLMRouter:
    """
    Vision LLM のローテーション戦略を担当する Router。

    - Factory は provider 抽象化のみ
    - Router が retry に応じて rotate
    - Factory.create(config) が None → 次のモデルへ（止めない）
    - 全モデル失敗時は構造化された失敗情報を返す
    """

    @staticmethod
    def rotate_models(retry: int = 0) -> List[Dict[str, Any]]:
        if not VISION_OCR_MODELS:
            return []

        retry = retry % len(VISION_OCR_MODELS)
        return VISION_OCR_MODELS[retry:] + VISION_OCR_MODELS[:retry]

    @staticmethod
    def get_callable(retry: int = 0) -> Dict[str, Any]:
        errors: List[str] = []

        for config in VisionLLMRouter.rotate_models(retry):
            model_callable = VisionModelFactory.create(config)

            if model_callable is not None:
                return {
                    "ok": True,
                    "callable": model_callable,
                    "model": config,
                }

            errors.append(f"Failed to initialize: {config}")

        return {
            "ok": False,
            "reason": "all_models_failed",
            "errors": errors,
        }
