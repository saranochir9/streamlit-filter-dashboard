import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import os
import uuid

st.set_page_config(
    page_title="Filter Replacement Dashboard",
    page_icon="📦",
    layout="wide"
)

RECORDS_FILE = "filter_records.csv"

# ---------- Create File ----------

if not os.path.exists(RECORDS_FILE):
    pd.DataFrame(columns=[
        "ID",
        "Team",
        "Area",
        "Tag",
        "Filter Type",
        "Interval Days",
        "Date Changed",
        "Next Due",
        "Days Remaining",
        "Status",
        "Changed By",
        "Remarks"
    ]).to_csv(RECORDS_FILE, index=False)

# ---------- Load ----------

df = pd.read_csv(RECORDS_FILE)

# ---------- Status Calculation ----------

def calculate_status(row):
    try:
        changed = pd.to_datetime(row["Date Changed"])

        next_due = changed + timedelta(days=int(row["Interval Days"]))
        days_remaining = (next_due.date() - datetime.today().date()).days

        if days_remaining < 0:
            status = "Overdue"
        elif days_remaining <= 30:
            status = "Due Soon"
        else:
            status = "Healthy"

        return pd.Series([
            next_due.date(),
            days_remaining,
            status
        ])

    except:
        return pd.Series([None, None, None])

if len(df) > 0:
    df[["Next Due","Days Remaining","Status"]] = df.apply(
        calculate_status,
        axis=1
    )

# ---------- Theme ----------

st.markdown("""
<style>

.main{
background-color:#0f172a;
}

.card{
padding:20px;
border-radius:15px;
text-align:center;
background:#1e293b;
color:white;
box-shadow:0px 0px 10px rgba(0,255,255,0.2);
}

</style>
""", unsafe_allow_html=True)

# ---------- Tabs ----------

tab1, tab2, tab3 = st.tabs([
    "📊 Dashboard",
    "📝 Records",
    "➕ Add Record"
])

# ==================================
# DASHBOARD
# ==================================

with tab1:

    st.title("📦 Filter Replacement Dashboard")

    total = len(df)

    overdue = len(df[df["Status"] == "Overdue"])
    due = len(df[df["Status"] == "Due Soon"])
    healthy = len(df[df["Status"] == "Healthy"])

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total Filters", total)
    c2.metric("Healthy", healthy)
    c3.metric("Due Soon", due)
    c4.metric("Overdue", overdue)

    st.divider()

    left,right = st.columns(2)

    status_count = (
        df["Status"]
        .value_counts()
        .reset_index()
    )

    status_count.columns=[
        "Status",
        "Count"
    ]

    if len(status_count) > 0:

        fig1 = px.pie(
            status_count,
            names="Status",
            values="Count",
            hole=0.5,
            title="Filter Health"
        )

        left.plotly_chart(fig1, use_container_width=True)

    if len(df) > 0:

        team_count = (
            df.groupby("Team")
            .size()
            .reset_index(name="Count")
        )

        fig2 = px.bar(
            team_count,
            x="Team",
            y="Count",
            title="Filters by Team"
        )

        right.plotly_chart(fig2, use_container_width=True)

# ==================================
# RECORDS
# ==================================

with tab2:

    st.subheader("Filter Records")

    c1,c2,c3 = st.columns(3)

    teams = ["All"] + sorted(df["Team"].dropna().unique().tolist())
    team = c1.selectbox(
        "Team",
        teams
    )

    temp = df.copy()

    if team != "All":
        temp = temp[
            temp["Team"] == team
        ]

    areas = ["All"] + sorted(
        temp["Area"].dropna().unique().tolist()
    )

    area = c2.selectbox(
        "Area",
        areas
    )

    status = c3.selectbox(
        "Status",
        ["All","Healthy","Due Soon","Overdue"]
    )

    if area != "All":
        temp = temp[
            temp["Area"] == area
        ]

    if status != "All":
        temp = temp[
            temp["Status"] == status
        ]

    gb = GridOptionsBuilder.from_dataframe(temp)

    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=True
    )

    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True
    )

    grid = AgGrid(
        temp,
        height=500,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED
    )

    st.divider()

    col1,col2 = st.columns(2)

    if col1.button("💾 Save Changes"):

        save_df = pd.DataFrame(
            grid["data"]
        )

        save_df.to_csv(
            RECORDS_FILE,
            index=False
        )

        st.success("Changes Saved")

    selected = pd.DataFrame(
        grid["selected_rows"]
    )

    if col2.button("❌ Delete Selected"):

        if len(selected) > 0:

            ids = selected["ID"].tolist()

            remaining = df[
                ~df["ID"].isin(ids)
            ]

            remaining.to_csv(
                RECORDS_FILE,
                index=False
            )

            st.success("Deleted")

            st.rerun()

# ==================================
# ADD RECORD
# ==================================

with tab3:

    st.subheader("Add Filter Record")

    if "last_team" not in st.session_state:
        st.session_state.last_team = ""

    if "last_area" not in st.session_state:
        st.session_state.last_area = ""

    if "last_changed_by" not in st.session_state:
        st.session_state.last_changed_by = ""

    c1,c2,c3 = st.columns(3)

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

    c4,c5,c6 = st.columns(3)

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

        new = pd.DataFrame([{

            "ID":str(uuid.uuid4())[:8],

            "Team":team,
            "Area":area,
            "Tag":tag,
            "Filter Type":filter_type,
            "Interval Days":interval,
            "Date Changed":date_changed,
            "Changed By":changed_by,
            "Remarks":remarks

        }])

        df2 = pd.concat(
            [df,new],
            ignore_index=True
        )

        df2.to_csv(
            RECORDS_FILE,
            index=False
        )

        st.session_state.last_team = team
        st.session_state.last_area = area
        st.session_state.last_changed_by = changed_by

        st.success("Record Added")

        st.rerun()
