import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os
import uuid

st.set_page_config(
    page_title="TEST VERSION 999",
    page_icon="📦",
    layout="wide"
)

st.title("TEST VERSION 999")
st.stop()

RECORDS_FILE = "filter_records.csv"

# ==========================
# CREATE FILE IF NOT EXISTS
# ==========================

if not os.path.exists(RECORDS_FILE):
    pd.DataFrame(columns=[
        "ID",
        "Team",
        "Area",
        "Tag",
        "Filter Type",
        "Interval Days",
        "Date Changed",
        "Changed By",
        "Remarks"
    ]).to_csv(RECORDS_FILE, index=False)

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(RECORDS_FILE)
st.write("Columns:")
st.write(df.columns.tolist())

st.write(df.head())

st.stop()
# ==========================
# CALCULATE STATUS
# ==========================

if len(df) > 0:

    df["Date Changed"] = pd.to_datetime(
        df["Date Changed"],
        errors="coerce"
    )

    df["Next Due"] = (
        df["Date Changed"] +
        pd.to_timedelta(df["Interval Days"], unit="D")
    )

    df["Days Remaining"] = (
        df["Next Due"].dt.date -
        datetime.today().date()
    )

    df["Days Remaining"] = df["Days Remaining"].apply(
        lambda x: x.days if pd.notna(x) else None
    )

    def get_status(days):

        if pd.isna(days):
            return "Unknown"

        if days < 0:
            return "Overdue"

        elif days <= 30:
            return "Due Soon"

        else:
            return "Healthy"

    df["Status"] = df["Days Remaining"].apply(
        get_status
    )

else:

    df["Next Due"] = ""
    df["Days Remaining"] = ""
    df["Status"] = ""

# ==========================
# TABS
# ==========================

tab1, tab2, tab3 = st.tabs([
    "📊 Dashboard",
    "📋 Records",
    "➕ Add Record"
])

# ==========================
# DASHBOARD
# ==========================

with tab1:

    st.title("📦 Filter Replacement Dashboard")

    total = len(df)

    overdue = len(df[df["Status"] == "Overdue"])
    due_soon = len(df[df["Status"] == "Due Soon"])
    healthy = len(df[df["Status"] == "Healthy"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Filters", total)
    c2.metric("Healthy", healthy)
    c3.metric("Due Soon", due_soon)
    c4.metric("Overdue", overdue)

    st.divider()

    left, right = st.columns(2)

    if total > 0:

        status_df = (
            df["Status"]
            .value_counts()
            .reset_index()
        )

        status_df.columns = [
            "Status",
            "Count"
        ]

        fig1 = px.pie(
            status_df,
            names="Status",
            values="Count",
            hole=0.5,
            title="Filter Health"
        )

        left.plotly_chart(
            fig1,
            use_container_width=True
        )

        team_df = (
            df.groupby("Team")
            .size()
            .reset_index(name="Count")
        )

        fig2 = px.bar(
            team_df,
            x="Team",
            y="Count",
            title="Filters by Team"
        )

        right.plotly_chart(
            fig2,
            use_container_width=True
        )

# ==========================
# RECORDS
# ==========================

with tab2:

    st.subheader("Filter Records")

    c1, c2, c3 = st.columns(3)

    teams = ["All"] + sorted(
        df["Team"].dropna().unique().tolist()
    )

    selected_team = c1.selectbox(
        "Team",
        teams
    )

    filtered = df.copy()

    if selected_team != "All":
        filtered = filtered[
            filtered["Team"] == selected_team
        ]

    areas = ["All"] + sorted(
        filtered["Area"].dropna().unique().tolist()
    )

    selected_area = c2.selectbox(
        "Area",
        areas
    )

    selected_status = c3.selectbox(
        "Status",
        [
            "All",
            "Healthy",
            "Due Soon",
            "Overdue"
        ]
    )

    if selected_area != "All":
        filtered = filtered[
            filtered["Area"] == selected_area
        ]

    if selected_status != "All":
        filtered = filtered[
            filtered["Status"] == selected_status
        ]

    gb = GridOptionsBuilder.from_dataframe(
        filtered
    )

    gb.configure_selection(
        "multiple",
        use_checkbox=True
    )

    gb.configure_default_column(
        editable=True,
        sortable=True,
        filter=True
    )

    grid = AgGrid(
        filtered,
        gridOptions=gb.build(),
        height=500,
        update_mode=GridUpdateMode.MODEL_CHANGED
    )

    col1, col2 = st.columns(2)

    if col1.button("💾 Save Changes"):

        pd.DataFrame(
            grid["data"]
        ).to_csv(
            RECORDS_FILE,
            index=False
        )

        st.success("Saved")
        st.rerun()

    selected_rows = pd.DataFrame(
        grid["selected_rows"]
    )

    if col2.button("❌ Delete Selected"):

        if len(selected_rows) > 0:

            ids = selected_rows["ID"].tolist()

            remaining = df[
                ~df["ID"].isin(ids)
            ]

            remaining.to_csv(
                RECORDS_FILE,
                index=False
            )

            st.success("Deleted")
            st.rerun()

# ==========================
# ADD RECORD
# ==========================

with tab3:

    st.subheader("Add Filter Record")

    if "last_team" not in st.session_state:
        st.session_state.last_team = ""

    if "last_area" not in st.session_state:
        st.session_state.last_area = ""

    if "last_changed_by" not in st.session_state:
        st.session_state.last_changed_by = ""

    c1, c2, c3 = st.columns(3)

    team = c1.text_input(
        "Team",
        st.session_state.last_team
    )

    area = c2.text_input(
        "Area",
        st.session_state.last_area
    )

    changed_by = c3.text_input(
        "Changed By",
        st.session_state.last_changed_by
    )

    c4, c5, c6 = st.columns(3)

    tag = c4.text_input("Tag")

    filter_type = c5.text_input(
        "Filter Type"
    )

    interval = c6.number_input(
        "Interval Days",
        min_value=1,
        value=90
    )

    date_changed = st.date_input(
        "Date Changed"
    )

    remarks = st.text_area(
        "Remarks"
    )

    if st.button("➕ Add Record"):

        new_row = pd.DataFrame([{
            "ID": str(uuid.uuid4())[:8],
            "Team": team,
            "Area": area,
            "Tag": tag,
            "Filter Type": filter_type,
            "Interval Days": interval,
            "Date Changed": date_changed,
            "Changed By": changed_by,
            "Remarks": remarks
        }])

        save_df = pd.concat(
            [df.drop(
                columns=[
                    "Next Due",
                    "Days Remaining",
                    "Status"
                ],
                errors="ignore"
            ),
            new_row],
            ignore_index=True
        )

        save_df.to_csv(
            RECORDS_FILE,
            index=False
        )

        st.session_state.last_team = team
        st.session_state.last_area = area
        st.session_state.last_changed_by = changed_by

        st.success("Record Added")
        st.rerun()