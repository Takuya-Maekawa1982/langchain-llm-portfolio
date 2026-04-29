# utils/text_llm_router.py
from __future__ import annotations

from typing import Dict, Any, List

from .models_texts import TEXT_LLM_MODELS
from .model_factory_text import TextModelFactory


class TextLLMRouter:
    """
    Text LLM のローテーション戦略を担当する Router。

    - Factory は provider 抽象化のみ
    - Router が retry に応じて rotate
    - Factory.create(config) が None → 次のモデルへ（止めない）
    - 全モデル失敗時は構造化された失敗情報を返す
    """

    @staticmethod
    def rotate_models(retry: int = 0) -> List[Dict[str, Any]]:
        """
        retry 回数に応じて TEXT_LLM_MODELS を rotate して返す。
        """
        if not TEXT_LLM_MODELS:
            return []

        retry = retry % len(TEXT_LLM_MODELS)
        return TEXT_LLM_MODELS[retry:] + TEXT_LLM_MODELS[:retry]

    @staticmethod
    def get_callable(retry: int = 0) -> Dict[str, Any]:
        """
        rotate → Factory.create(config) → callable or None
        全モデル失敗時は構造化された失敗情報を返す。
        """
        errors: List[str] = []

        for config in TextLLMRouter.rotate_models(retry):
            model_callable = TextModelFactory.create(config)

            if model_callable is not None:
                return {
                    "ok": True,
                    "callable": model_callable,
                    "model": config,
                }

            errors.append(f"Failed to initialize: {config}")

        # 全部失敗
        return {
            "ok": False,
            "reason": "all_models_failed",
            "errors": errors,
        }
