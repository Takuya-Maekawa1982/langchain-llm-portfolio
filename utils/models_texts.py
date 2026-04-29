# utils/models_texts.py

TEXT_LLM_MODELS = [
    # =========================================================
    # 【無料枠】（無料 API のみを有効化）
    # =========================================================

    # ---------------------------------------------------------
    # OpenRouter（Qwen 系）※無料・高速・日本語強い
    # ---------------------------------------------------------
    {
        "provider": "openrouter",
        "model": "qwen/qwen-2.5-7b-instruct:free",
        # パラメータ: 7B
        # 特徴: 日本語強い / JSON安定 / 軽量
        # 用途: 軽量タスク・構造化出力
    },
    {
        "provider": "openrouter",
        "model": "qwen/qwen-2.5-14b-instruct:free",
        # パラメータ: 14B
        # 特徴: 7B より精度向上
        # 用途: 日本語の構造化・抽出タスク
    },
    {
        "provider": "openrouter",
        "model": "qwen/qwen-2.5-vl-7b-instruct:free",
        # パラメータ: 7B（Vision対応）
        # 特徴: 画像＋テキスト混在の理解が強い
        # 用途: 画像内テキストの補正・構造化
    },

    # ---------------------------------------------------------
    # Google Gemini（無料枠広い）
    # ---------------------------------------------------------
    {
        "provider": "google",
        "model": "gemini-2.5-flash-lite",
        # パラメータ: 非公開（軽量系）
        # 無料枠: 1,000 RPD（最も広い）
        # 用途: 高速・大量処理・軽量構造化
    },
    {
        "provider": "google",
        "model": "gemini-2.5-flash",
        # パラメータ: 非公開（中量級）
        # 無料枠: 250 RPD
        # 用途: 精度と速度のバランス
    },

    # ---------------------------------------------------------
    # Groq（Llama 系 / 超高速）
    # ---------------------------------------------------------
    {
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        # パラメータ: 8B
        # 特徴: 超高速 / 軽量
        # 用途: 単純抽出・軽量構造化
    },
    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        # パラメータ: 70B
        # 無料枠: 1,000 RPD / 6,000 TPM
        # 特徴: 高精度 / 日本語構造化に強い
        # 用途: 複雑なインボイス・表構造の抽出
    },
    {
        "provider": "groq",
        "model": "llama-4-scout-17b-16e-instruct",
        # パラメータ: 17B（Mixture-of-Experts）
        # 特徴: 新世代 / 高速・高精度のバランス
        # 用途: 構造化・推論タスク
    },
]

# =========================================================
# 【有料候補】（コメントアウトで保持 / accidental charges 防止）
# =========================================================

# --- OpenRouter (Qwen 有料) ---
# {
#     "provider": "openrouter",
#     "model": "qwen/qwen-2.5-72b-instruct",
#     # パラメータ: 72B
#     # 特徴: 日本語・構造化の最高精度クラス
# },

# {
#     "provider": "openrouter",
#     "model": "qwen/qwen3-30b-a3b",
#     # パラメータ: 30B（A3B）
#     # 特徴: thinking mode 対応
# },

# --- Google Gemini (有料) ---
# {
#     "provider": "google",
#     "model": "gemini-2.5-pro",
#     # パラメータ: 非公開（大型）
#     # 特徴: 最高精度 / 1M context
# },

# --- Groq (有料) ---
# {
#     "provider": "groq",
#     "model": "openai/gpt-oss-120b",
#     # パラメータ: 120B
#     # 特徴: Groq 上で最高精度
# },
