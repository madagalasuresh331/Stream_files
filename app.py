import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="AI Data Analysis Agent", layout="wide")

N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/data-cleaning-agent"

if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.title("AI Data Agent")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Ask AI", "Report"]
)

st.title("AI Data Analysis Agent")

file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])


def read_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def clean_data(df):
    df = df.drop_duplicates()

    for col in df.columns:
        if df[col].dtype == "object":
            cleaned = (
                df[col]
                .astype(str)
                .str.replace("₹", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            converted = pd.to_numeric(cleaned, errors="coerce")

            if converted.notnull().sum() > len(df) * 0.6:
                df[col] = converted

    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            else:
                mode_value = df[col].mode()
                if not mode_value.empty:
                    df[col] = df[col].fillna(mode_value[0])

    return df


def detect_columns(df):
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    date_cols = []

    for col in df.columns:
        if col not in numeric_cols:
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notnull().sum() > len(df) * 0.6:
                date_cols.append(col)

    categorical_cols = [
        col for col in df.columns
        if col not in numeric_cols and col not in date_cols
    ]

    return numeric_cols, categorical_cols, date_cols


def find_best_value_column(df, numeric_cols):
    priority = [
        "sales",
        "revenue",
        "total_amount",
        "amount",
        "profit",
        "cost_price",
        "price",
        "quantity"
    ]

    for word in priority:
        for col in numeric_cols:
            if word in col.lower():
                return col

    if len(numeric_cols) > 0:
        return numeric_cols[0]

    return None


def call_n8n_agent(prompt, dataset_info):
    payload = {
        "prompt": prompt,
        "dataset_info": dataset_info
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        data = response.json()
        return data["output"][0]["content"][0]["text"]

    except Exception as e:
        return "Error: " + str(e)


if file is not None:
    df = read_file(file)
    df = clean_data(df)

    numeric_cols, categorical_cols, date_cols = detect_columns(df)
    value_col = find_best_value_column(df, numeric_cols)

    st.sidebar.success("Dataset uploaded successfully")

    if page == "Dashboard":
        st.subheader("Dashboard")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Rows", df.shape[0])
        col2.metric("Total Columns", df.shape[1])
        col3.metric("Numeric Columns", len(numeric_cols))
        col4.metric("Category Columns", len(categorical_cols))

        st.write("Detected Numeric Columns:", numeric_cols)
        st.write("Main Value Column:", value_col)

        st.divider()

        st.subheader("Filters")

        filtered_df = df.copy()

        if len(categorical_cols) > 0:
            filter_col = st.selectbox("Select filter column", categorical_cols)

            selected_values = st.multiselect(
                f"Filter by {filter_col}",
                df[filter_col].dropna().unique()
            )

            if selected_values:
                filtered_df = filtered_df[
                    filtered_df[filter_col].isin(selected_values)
                ]

        st.divider()

        st.subheader("Auto Dashboard Charts")

        if len(categorical_cols) > 0 and value_col is not None:
            cat = categorical_cols[0]

            chart_data = (
                filtered_df
                .groupby(cat)[value_col]
                .sum()
                .reset_index()
                .sort_values(value_col, ascending=False)
            )

            fig1 = px.bar(
                chart_data,
                x=cat,
                y=value_col,
                title=f"{value_col} by {cat}"
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.pie(
                chart_data,
                names=cat,
                values=value_col,
                title=f"{cat}-wise {value_col} Contribution"
            )
            st.plotly_chart(fig2, use_container_width=True)

        if len(date_cols) > 0 and value_col is not None:
            date_col = date_cols[0]

            filtered_df[date_col] = pd.to_datetime(
                filtered_df[date_col],
                errors="coerce"
            )

            trend = (
                filtered_df
                .dropna(subset=[date_col])
                .groupby(date_col)[value_col]
                .sum()
                .reset_index()
                .sort_values(date_col)
            )

            fig3 = px.line(
                trend,
                x=date_col,
                y=value_col,
                title=f"{value_col} Trend Over Time"
            )
            st.plotly_chart(fig3, use_container_width=True)

        if len(numeric_cols) >= 2:
            fig4 = px.scatter(
                filtered_df,
                x=numeric_cols[0],
                y=numeric_cols[1],
                title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
            )
            st.plotly_chart(fig4, use_container_width=True)

    elif page == "Ask AI":
        st.subheader("Ask Question")

        user_prompt = st.text_input(
            "Example: Show city-wise sales performance"
        )

        if st.button("Ask AI"):
            dataset_info = f"""
Dataset Shape: {df.shape}

Columns:
{df.columns.tolist()}

Data Types:
{df.dtypes.to_string()}

Missing Values:
{df.isnull().sum().to_string()}

Numeric Columns:
{numeric_cols}

Categorical Columns:
{categorical_cols}

Date Columns:
{date_cols}

Main Value Column:
{value_col}

Sample Data:
{df.head(10).to_string()}
"""

            result = call_n8n_agent(user_prompt, dataset_info)

            st.subheader("AI Response")
            st.write(result)

            st.session_state.history.append({
                "prompt": user_prompt,
                "response": result
            })

        st.subheader("Question History")

        for item in st.session_state.history:
            st.write("Question:", item["prompt"])
            st.write("Answer:", item["response"])
            st.divider()

    elif page == "Report":
        st.subheader("Auto Report")

        st.write("Rows:", df.shape[0])
        st.write("Columns:", df.shape[1])
        st.write("Numerical Columns:", numeric_cols)
        st.write("Categorical Columns:", categorical_cols)
        st.write("Date Columns:", date_cols)
        st.write("Main Value Column:", value_col)

        report_text = f"""
AI Data Analysis Report

Rows: {df.shape[0]}
Columns: {df.shape[1]}

Numerical Columns:
{numeric_cols}

Categorical Columns:
{categorical_cols}

Date Columns:
{date_cols}

Main Value Column:
{value_col}

Analysis History:
"""

        for item in st.session_state.history:
            report_text += f"\nQuestion: {item['prompt']}\nAnswer: {item['response']}\n"

        st.text_area("Report", report_text, height=400)

        st.download_button(
            "Download Report",
            report_text,
            file_name="ai_data_analysis_report.txt"
        )

else:
    st.info("Upload a CSV or Excel file from the sidebar to start.")