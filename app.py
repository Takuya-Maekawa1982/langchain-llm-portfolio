import streamlit as st
import pandas as pd
import re

from extractors.graph import bill_agent
from utils.files import extract_raw_content
from utils.rate import fetch_usd_jpy_rate          # ★ 為替レート API
from llm_correction.corrector import llm_correction  # ★ LLM Correction（前段）


def clean_currency(value):
    if pd.isna(value) or value == "":
        return 0.0
    clean_val = re.sub(r'[^\d.]', '', str(value))
    try:
        return float(clean_val)
    except ValueError:
        return 0.0


def main():
    st.set_page_config(page_title="Bill Agent Pro (HITL)", layout="wide")

    st.title("Bill Extractor AI with Human‑in‑the‑loop 🤖🧑‍💻")

    # ================================
    # Sidebar Settings
    # ================================
    st.sidebar.title("Pipeline Settings")

    # OCR モード
    ocr_model_type = st.sidebar.selectbox(
        "OCR モード",
        [
            "A: 最速モード（軽量・安定 / いつでも使える）",
            "B: Visionモード（高精度だが少し遅い / 利用できない場合あり）",
        ],
        index=0
    )
    model_type = ocr_model_type.split(":")[0]

    # OCR キャッシュ削除
    if st.sidebar.button("🗑️ OCR キャッシュを削除"):
        st.session_state.ocr_results = {}
        st.success("OCR キャッシュを削除しました。")

    # ================================
    # ★ 為替レート自動取得（デフォルト ON）
    # ================================
    auto_rate = st.sidebar.checkbox(
        "為替レートを自動取得する（USD→JPY）",
        value=True
    )

    if auto_rate:
        rate = fetch_usd_jpy_rate()
        if rate is None:
            st.sidebar.warning("為替レートを取得できませんでした。150 を仮値として使用します。")
            exchange_rate = st.sidebar.number_input("USD/JPY Rate", value=150.0, step=0.1)
        else:
            st.sidebar.success(f"為替レートを取得しました: 1 USD = {rate:.2f} JPY")
            exchange_rate = st.sidebar.number_input("USD/JPY Rate", value=rate, step=0.1)
    else:
        exchange_rate = st.sidebar.number_input("USD/JPY Rate", value=150.0, step=0.1)

    # Audit / Validation
    audit_mode = st.sidebar.toggle("Audit Mode", value=False)
    max_r = st.sidebar.slider("Max Audit Retries", 1, 5, 1) if audit_mode else 0
    validate_mode = st.sidebar.toggle("Validation Mode", value=False)

    # ================================
    # SessionState 初期化
    # ================================
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    if "ocr_results" not in st.session_state:
        st.session_state.ocr_results = {}

    # ================================
    # Step 0: ファイルアップロード
    # ================================
    uploaded = st.file_uploader(
        "Upload bills",
        accept_multiple_files=True,
        key="file_uploader_main"
    )

    if uploaded:
        st.session_state.uploaded_files = uploaded

    files = st.session_state.uploaded_files

    # ================================
    # Step 1: OCR 読み込み
    # ================================
    if files:
        st.subheader("Step 1: OCR 読み込み")

        with st.expander("⚙️ Advanced OCR Settings（上級者向け）"):
            st.caption("※ 通常は変更不要です。手書きの精度が悪い場合のみ調整してください。")

            adv_binarize = st.checkbox("強い二値化", value=False, key="adv_binarize")
            adv_deskew = st.checkbox("傾き補正", value=False, key="adv_deskew")
            adv_denoise = st.checkbox("ノイズ除去", value=True, key="adv_denoise")
            adv_contrast = st.checkbox("コントラスト強調", value=True, key="adv_contrast")

            line_threshold = st.slider(
                "行分割の閾値",
                min_value=0.05, max_value=0.20, value=0.08, step=0.01,
                key="line_threshold"
            )

        if st.button("📥 OCR 読み込みを実行"):
            ocr_results = {}

            for file in files:
                # ★ extract_raw_content が lang を返す前提
                content, detected_type, is_handwritten, lang = extract_raw_content(
                    file,
                    model_type=model_type,
                    adv_binarize=adv_binarize,
                    adv_deskew=adv_deskew,
                    adv_denoise=adv_denoise,
                    adv_contrast=adv_contrast,
                    line_threshold=line_threshold
                )

                ocr_results[file.name] = {
                    "file": file,
                    "content": content,
                    "detected_type": detected_type,
                    "is_handwritten": is_handwritten,
                    "lang": lang,   # ★ 言語を保存
                }

            st.session_state.ocr_results = ocr_results
            st.success("OCR 読み込みが完了しました。下で内容を編集できます。")

    # ================================
    # Step 2: OCR 結果編集
    # ================================
    if st.session_state.ocr_results:
        st.subheader("Step 2: OCR 結果一覧（編集可能）")

        use_llm_correction_global = st.checkbox(
            "LLM Correction（全体 ON/OFF）",
            value=False,
            key="llm_global"
        )

        edited_results = []

        for file_name, data in st.session_state.ocr_results.items():
            file = data["file"]
            content = data["content"]
            detected_type = data["detected_type"]
            is_handwritten = data["is_handwritten"]
            lang = data["lang"]   # ★ OCR が返した言語を使用

            st.write(f"### 📄 {file.name}")

            show_preview = st.checkbox(
                "ファイルプレビューを表示",
                value=False,
                key=f"preview_{file_name}"
            )

            if show_preview:
                st.image(file.read(), caption=f"Preview: {file.name}", use_column_width=True)
                file.seek(0)

            new_type = st.selectbox(
                f"{file.name} のファイル種別",
                ["pdf", "image", "excel", "docx", "text"],
                index=["pdf","image","excel","docx","text"].index(detected_type),
                key=f"type_{file.name}"
            )

            new_handwritten = st.selectbox(
                "手書き判定（編集可能）",
                ["No", "Yes"],
                index=1 if is_handwritten else 0,
                key=f"hand_{file.name}"
            )
            is_handwritten = (new_handwritten == "Yes")
            st.session_state.ocr_results[file_name]["is_handwritten"] = is_handwritten

            edited_text = st.text_area(
                f"OCR結果を編集 ({file.name})",
                content,
                height=200,
                key=f"edit_{file.name}"
            )
            st.session_state.ocr_results[file_name]["content"] = edited_text

            use_llm_correction = st.checkbox(
                "LLM Correction（このファイルのみ）",
                value=use_llm_correction_global,
                key=f"llm_{file.name}"
            )

            # ★ LLM Correction（任意）
            if use_llm_correction:
                correction = llm_correction(
                    text=edited_text,
                    lang=lang,
                    retry_count=0
                )
                corrected_text = correction["corrected_text"]
            else:
                corrected_text = edited_text

            edited_results.append({
                "file": file,
                "content": corrected_text,   # ★ Correction 済みテキスト
                "detected_type": new_type,
                "is_handwritten": is_handwritten,
                "use_llm_correction": use_llm_correction,
                "lang": lang,               # ★ LangGraph にも渡す
            })

        st.divider()

        # ================================
        # Step 3: LangGraph 実行
        # ================================
        if st.button("Run Extraction (編集済みテキストで実行)"):

            display_results = []

            for item in edited_results:
                file = item["file"]

                initial_state = {
                    "file_name": file.name,
                    "raw_content": item["content"],   # ★ Correction 済み
                    "is_handwritten": item["is_handwritten"],
                    "use_llm_correction": item["use_llm_correction"],
                    "language": item["lang"],         # ★ OCR 言語を LangGraph に渡す
                    "extracted_json": {},
                    "audit_mode": audit_mode,
                    "validate_mode": validate_mode,
                    "max_retries": max_r,
                    "retry_count": 0,
                    "audit_logs": [],
                    "critique": "",
                    "status": "starting"
                }

                with st.spinner(f"Analyzing {file.name}..."):
                    final_state = bill_agent.invoke(initial_state)

                res_data = final_state.get("extracted_json", {}).copy()
                res_data["_lang"] = final_state.get("language", "EN")
                res_data["Source File"] = file.name

                display_results.append({
                    "json": res_data,
                    "meta": {
                        "language": final_state.get("language"),
                        "is_handwritten": final_state.get("is_handwritten"),
                        "retry_count": final_state.get("retry_count"),
                        "audit_logs": final_state.get("audit_logs", []),
                        "audit_summary": final_state.get("audit_summary", "No summary generated.")
                    }
                })

                with st.expander(f"Analysis: {file.name}"):
                    meta = display_results[-1]["meta"]

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Language:** {meta['language']}")
                        st.write(f"**Handwritten:** {meta['is_handwritten']}")
                    with col_b:
                        st.write(f"**Total Attempts:** {meta['retry_count']}")

                    st.info(f"🤖 **Process Summary:** {meta['audit_summary']}")

                    if audit_mode:
                        st.write("### Technical Audit Logs")
                        for log in meta["audit_logs"]:
                            st.write(log)

                    st.json(display_results[-1]["json"])

            # ================================
            # Step 4: 集計 + CSV 出力
            # ================================
            if display_results:
                st.divider()
                common_cols = ["Invoice ID", "Issue Date", "DESCRIPTION", "UNIT PRICE", "AMOUNT", "Bill For", "From", "Source File"]

                all_json_data = [item["json"] for item in display_results]

                # English (USD)
                en_data = [r for r in all_json_data if r["_lang"] == "EN"]
                if en_data:
                    st.subheader("📋 Extracted Invoices (USD)")
                    df_en = pd.DataFrame(en_data).reindex(columns=common_cols)

                    df_en["_num_amount"] = df_en["AMOUNT"].apply(clean_currency)
                    df_en[f"JPY (at {exchange_rate})"] = df_en["_num_amount"].apply(lambda x: f"¥{int(x * exchange_rate):,}")

                    usd_total = df_en["_num_amount"].sum()
                    jpy_equivalent = usd_total * exchange_rate

                    col1, col2 = st.columns(2)
                    col1.metric("Total Amount (USD)", f"${usd_total:,.2f}")
                    col2.metric("Equivalent (JPY)", f"¥{int(jpy_equivalent):,}")

                    st.dataframe(df_en.drop(columns=["_num_amount"]), use_container_width=True)

                    csv_en = df_en.to_csv(index=False).encode("utf-8")
                    st.download_button("Download CSV (USD)", csv_en, "invoices_usd.csv")

                # Japanese (JPY)
                jp_data = [r for r in all_json_data if r["_lang"] == "JP"]
                if jp_data:
                    st.subheader("📋 抽出済み請求書一覧 (JPY)")
                    df_jp = pd.DataFrame(jp_data).reindex(columns=common_cols)

                    df_jp["_num_amount"] = df_jp["AMOUNT"].apply(clean_currency)
                    jpy_total = df_jp["_num_amount"].sum()

                    st.metric("合計金額 (JPY)", f"¥{int(jpy_total):,}")
                    st.dataframe(df_jp.drop(columns=["_num_amount"]), use_container_width=True)

                    csv_jp = df_jp.to_csv(index=False).encode("utf-8")
                    st.download_button("Download CSV (JPY)", csv_jp, "invoices_jp.csv")


if __name__ == "__main__":
    main()
