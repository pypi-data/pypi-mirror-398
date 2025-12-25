import streamlit as st
import pandas as pd
import io
import jionlp as jio
from maque.nlp.deduplicate import EditSimilarity

# streamlit run main.py --server.maxUploadSize=1024
simi = EditSimilarity()


def load_data(file):
    return pd.read_excel(file)


def save_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output


st.title('文本预处理工具')

uploaded_file = st.file_uploader("选择一个 Excel 文件", type=['xlsx'])
if 'replay' not in st.session_state:
    st.session_state['replay'] = False

if uploaded_file is not None:
    df = load_data(uploaded_file)

    st.write("数据预览：")
    st.dataframe(df.head(10))
    # 获取 Excel 文件中的列名
    columns = df.columns.tolist()

    # 让用户选择要清理的多个列
    selected_columns = st.multiselect("选择要清理的列", columns)
    # 选择操作
    operation = st.multiselect("选择操作", [ "去重", "清洗文本", ])
    dedup_threshold = 0.7
    if "去重" in operation:
        dedup_threshold = st.slider("选择去重阈值（越小越严格）", 0.0, 1.0, 0.7)

    if st.button('执行'):
        for column in selected_columns:
            if "去重" in operation:
                simi.load_from_df(df, target_col=column)
                df = simi.deduplicate(threshold=dedup_threshold)
            if "删除文本中的冗余字符" in operation:
                df[column] = df[column].apply(lambda x: jio.remove_redundant_char(x))

            if "清洗文本" in operation:
                df[column] = df[column].apply(lambda x: jio.clean_text(x))

        st.write("清理后的数据预览：")
        st.dataframe(df.head(10))

        cleaned_data = save_df_to_excel(df)
        st.download_button(
            label="下载处理后的数据",
            data=cleaned_data,
            file_name="cleaned_data.xlsx",
            mime="application/vnd.ms-excel",
        )
else:
    st.info("请上传一个 Excel 文件。")
