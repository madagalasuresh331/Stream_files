import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import StringIO

st.set_page_config(page_title="MaTtErS...AnAlYzE", layout="wide")

# ---------------- SESSION ----------------

if "page" not in st.session_state:
    st.session_state.page = "data_show"

if "theme" not in st.session_state:
    st.session_state.theme = "light"

if "analysis_log" not in st.session_state:
    st.session_state.analysis_log = []


# ---------------- THEME ----------------

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp {background-color:#0e1117; color:white;}
        section[data-testid="stSidebar"] {background-color:#111827;}
        h1,h2,h3,h4,p,div,span,label {color:white;}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {background-color:white; color:black;}
        section[data-testid="stSidebar"] {background-color:#f3f4f6;}
        </style>
        """, unsafe_allow_html=True)

apply_theme()


# ---------------- TOP BAR ----------------

col1, col2 = st.columns([8, 1])

with col1:
    st.title("MaTtErS...AnAlYzE")
    st.caption(" Ai Agent Data Analyst...")

with col2:
    if st.button("🌙 / ☀️"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()


# ---------------- FUNCTIONS ----------------

@st.cache_data
def read_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def get_info(df):
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def download_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def download_text(text):
    return text.encode("utf-8")


def clean_data(df, method):
    report = {}

    report["Original Rows"] = df.shape[0]
    report["Original Columns"] = df.shape[1]
    report["Duplicate Rows Removed"] = int(df.duplicated().sum())
    report["Missing Values Before"] = int(df.isnull().sum().sum())

    df = df.drop_duplicates()

    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                if method == "Mean":
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna("Unknown")

    report["Rows After Cleaning"] = df.shape[0]
    report["Columns After Cleaning"] = df.shape[1]
    report["Missing Values After"] = int(df.isnull().sum().sum())

    return df, report


def detect_columns(df):
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    return numeric_cols, categorical_cols


def add_log(action, detail):
    st.session_state.analysis_log.append({
        "Action": action,
        "Details": detail
    })


def final_report(cleaning_report):
    text = "MaTtErS...AnAlYzE FINAL ANALYSIS SUMMARY\n\n"

    text += "1. CLEANING SUMMARY\n"
    for k, v in cleaning_report.items():
        text += f"{k}: {v}\n"

    text += "\n2. ANALYSIS DONE\n"
    if len(st.session_state.analysis_log) == 0:
        text += "No analysis performed yet.\n"
    else:
        for i, item in enumerate(st.session_state.analysis_log, start=1):
            text += f"{i}. {item['Action']} - {item['Details']}\n"

    text += "\n3. FINAL NOTE\n"
    text += "Dataset is cleaned, processed, and ready for dashboard/reporting.\n"

    return text


# ---------------- SIDEBAR ----------------

st.sidebar.title("Control Panel")

file = st.sidebar.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

st.sidebar.markdown("---")

clean_method = st.sidebar.radio("Null value filling method", ["Mean", "Median"])

st.sidebar.markdown("---")
st.sidebar.subheader("Actions")

if st.sidebar.button("1️⃣ Data Show"):
    st.session_state.page = "data_show"

if st.sidebar.button("2️⃣ Data Cleaning"):
    st.session_state.page = "cleaning"

if st.sidebar.button("3️⃣ Pivot Analyzer"):
    st.session_state.page = "pivot"

if st.sidebar.button("4️⃣ Graph Analyzer"):
    st.session_state.page = "graphs"

if st.sidebar.button("5️⃣ Report Analysis"):
    st.session_state.page = "report"

if st.sidebar.button("6️⃣ Analyze Summary"):
    st.session_state.page = "analyze"


# ---------------- MAIN ----------------

if file is not None:
    df = read_file(file)
    cleaned_df, cleaning_report = clean_data(df.copy(), clean_method)
    numeric_cols, categorical_cols = detect_columns(cleaned_df)

    # ---------------- DATA SHOW ----------------
    if st.session_state.page == "data_show":
        st.header("Data Show")

        st.subheader("Dataset Preview")
        st.dataframe(df, use_container_width=True)

        st.download_button("Download Original Data", download_csv(df), "original_data.csv", "text/csv")

        st.subheader("Info")
        info_text = get_info(df)
        st.text(info_text)

        st.download_button("Download Info", download_text(info_text), "data_info.txt", "text/plain")

        st.subheader("Describe")
        describe_df = df.describe(include="all")
        st.dataframe(describe_df, use_container_width=True)

        st.download_button("Download Describe", download_csv(describe_df.reset_index()), "describe.csv", "text/csv")

        st.subheader("Correlation")
        num_df = df.select_dtypes(include=["int64", "float64"])

        if len(num_df.columns) >= 2:
            corr_df = num_df.corr()
            st.dataframe(corr_df, use_container_width=True)
            st.download_button("Download Correlation", download_csv(corr_df.reset_index()), "correlation.csv", "text/csv")
        else:
            st.warning("Correlation needs minimum 2 numeric columns.")

    # ---------------- CLEANING ----------------
    elif st.session_state.page == "cleaning":
        st.header("Data Cleaning")

        report_df = pd.DataFrame(list(cleaning_report.items()), columns=["Step", "Value"])

        st.subheader("Cleaning Report")
        st.dataframe(report_df, use_container_width=True)

        st.success("Null values filled and duplicates removed.")

        st.subheader("Cleaned Data")
        st.dataframe(cleaned_df, use_container_width=True)

        st.download_button("Download Cleaned Dataset", download_csv(cleaned_df), "cleaned_dataset.csv", "text/csv")
        st.download_button("Download Cleaning Report", download_csv(report_df), "cleaning_report.csv", "text/csv")

    # ---------------- PIVOT ANALYZER ----------------
    elif st.session_state.page == "pivot":
        st.header("Pivot Analyzer")

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            row_col = st.selectbox("Select Row Column", categorical_cols)
            value_col = st.selectbox("Select Value Column", numeric_cols)
            agg_type = st.selectbox("Select Aggregation", ["sum", "mean", "count", "max", "min"])

            if st.button("Generate Pivot"):
                pivot_df = pd.pivot_table(
                    cleaned_df,
                    index=row_col,
                    values=value_col,
                    aggfunc=agg_type
                ).reset_index()

                st.subheader("Pivot Result")
                st.dataframe(pivot_df, use_container_width=True)

                add_log("Pivot Analysis", f"{agg_type} of {value_col} by {row_col}")

                st.download_button("Download Pivot Table", download_csv(pivot_df), "pivot_analysis.csv", "text/csv")
        else:
            st.warning("Need categorical and numeric columns.")

    # ---------------- GRAPH ANALYZER ----------------
    elif st.session_state.page == "graphs":
        st.header("Graph Analyzer")

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            chart_type = st.selectbox(
                "Select Chart Type",
                ["Bar Chart", "Line Chart", "Pie Chart", "Combo Bar + Line"]
            )

            x_col = st.selectbox("Select Category Column", categorical_cols)
            y_col = st.selectbox("Select First Numeric Column", numeric_cols)
            agg_type = st.selectbox("Aggregation", ["sum", "mean", "count", "max", "min"])

            if chart_type == "Combo Bar + Line":
                if len(numeric_cols) >= 2:
                    y2_col = st.selectbox("Select Second Numeric Column", numeric_cols)
                else:
                    y2_col = None
                    st.warning("Combo chart needs 2 numeric columns.")
            else:
                y2_col = None

            if st.button("Generate Graph"):
                if chart_type == "Combo Bar + Line" and y2_col is not None:
                    graph_df = cleaned_df.groupby(x_col).agg({
                        y_col: agg_type,
                        y2_col: agg_type
                    }).reset_index()

                    fig = make_subplots(specs=[[{"secondary_y": True}]])

                    fig.add_trace(
                        go.Bar(x=graph_df[x_col], y=graph_df[y_col], name=y_col),
                        secondary_y=False
                    )

                    fig.add_trace(
                        go.Scatter(x=graph_df[x_col], y=graph_df[y2_col], name=y2_col, mode="lines+markers"),
                        secondary_y=True
                    )

                    fig.update_layout(title=f"Combo Chart: {y_col} and {y2_col} by {x_col}")
                    fig.update_xaxes(title_text=x_col)
                    fig.update_yaxes(title_text=y_col, secondary_y=False)
                    fig.update_yaxes(title_text=y2_col, secondary_y=True)

                    st.plotly_chart(fig, use_container_width=True)

                    add_log("Combo Chart", f"{y_col} as bar and {y2_col} as line by {x_col}")

                else:
                    graph_df = cleaned_df.groupby(x_col)[y_col].agg(agg_type).reset_index()

                    if chart_type == "Bar Chart":
                        fig = px.bar(graph_df, x=x_col, y=y_col, title=f"{agg_type} of {y_col} by {x_col}")
                    elif chart_type == "Line Chart":
                        fig = px.line(graph_df, x=x_col, y=y_col, title=f"{agg_type} of {y_col} by {x_col}")
                    else:
                        fig = px.pie(graph_df, names=x_col, values=y_col, title=f"{y_col} share by {x_col}")

                    st.plotly_chart(fig, use_container_width=True)

                    add_log(chart_type, f"{agg_type} of {y_col} by {x_col}")

                st.subheader("Chart Data")
                st.dataframe(graph_df, use_container_width=True)

                st.download_button("Download Chart Data", download_csv(graph_df), "chart_data.csv", "text/csv")
        else:
            st.warning("Need categorical and numeric columns.")

    # ---------------- REPORT ----------------
    elif st.session_state.page == "report":
        st.header("Report Analysis")

        report = final_report(cleaning_report)

        st.text_area("Report", report, height=450)

        st.download_button("Download Report", download_text(report), "matters_report.txt", "text/plain")

    # ---------------- ANALYZE SUMMARY ----------------
    elif st.session_state.page == "analyze":
        st.header("Analyze Summary")

        st.subheader("All Analysis Done")

        if len(st.session_state.analysis_log) > 0:
            log_df = pd.DataFrame(st.session_state.analysis_log)
            st.dataframe(log_df, use_container_width=True)

            st.download_button("Download Analysis Summary", download_csv(log_df), "analysis_summary.csv", "text/csv")
        else:
            st.info("No pivot or chart analysis done yet.")

        st.subheader("Final Cleaned and Processed Dataset")
        st.dataframe(cleaned_df, use_container_width=True)

        st.download_button(
            "Final Download: Cleaned Processed Dataset",
            download_csv(cleaned_df),
            "final_cleaned_processed_dataset.csv",
            "text/csv"
        )

        final_text = final_report(cleaning_report)

        st.download_button(
            "Final Download: Full Report",
            download_text(final_text),
            "final_matters_report.txt",
            "text/plain"
        )

else:
    st.info("Upload your data file from the left panel.")
