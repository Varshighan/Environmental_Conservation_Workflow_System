import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

# --------------------------
# Firebase Initialization
# --------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# --------------------------
# Helper Functions
# --------------------------
def fetch_approvals():
    """Fetches all approval requests from Firestore."""
    approvals_ref = db.collection("approvals").stream()
    approval_data = [doc.to_dict() for doc in approvals_ref]

    if approval_data:
        df = pd.DataFrame(approval_data)
        st.dataframe(df)
    else:
        st.info("No approval requests found.")




# --------------------------
# Helper Functions
# --------------------------
def delete_old_approvals(days_threshold: int = 30):
    approvals_ref = db.collection("approvals")
    docs = approvals_ref.stream()

    for doc in docs:
        data = doc.to_dict()
        if "submitted_date" in data:
            submitted_date = datetime.strptime(data["submitted_date"], "%Y-%m-%d").date()
            if (datetime.today().date() - submitted_date).days > days_threshold:
                doc.reference.delete()

    st.success(f'✅ Deleted approvals older than {days_threshold} days.')

# --------------------------
# Project Management
# --------------------------
def manage_projects():
    st.header("🌳 Project Management")

    with st.expander("➕ New Project", expanded=True):
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Project Name")
            description = st.text_area("Description")
            assigned_to = col2.text_input("Assigned To")
            priority = col1.selectbox("Priority", ["Low", "Medium", "High"])
            location = col2.text_input("Location")
            latitude = col1.number_input("Latitude", format="%.6f")
            longitude = col2.number_input("Longitude", format="%.6f")
            start_date = col1.date_input("Start Date")
            due_date = col2.date_input("Due Date")

            if st.form_submit_button("Create Project"):
                project_id = str(uuid.uuid4())
                db.collection("projects").document(project_id).set({
                    "id": project_id,
                    "name": name,
                    "description": description,
                    "assigned_to": assigned_to,
                    "priority": priority,
                    "location": location,
                    "lat": latitude,
                    "lng": longitude,
                    "start_date": str(start_date),
                    "due_date": str(due_date),
                    "status": "Planning"
                })
                st.success("Project created!")

# --------------------------
# Incident Management
# --------------------------
def manage_incidents():
    st.header("🚨 Incident Management")

    with st.expander("⚠️ Report New Incident"):
        with st.form("incident_form"):
            col1, col2 = st.columns(2)
            incident_type = col1.selectbox("Type", ["Pollution", "Deforestation", "Poaching", "Disaster"])
            impact = col2.selectbox("Impact Level", ["Low", "Medium", "High", "Critical"])
            description = st.text_area("Incident Description")
            latitude = col1.number_input("Latitude", format="%.6f")
            longitude = col2.number_input("Longitude", format="%.6f")

            if st.form_submit_button("Submit Incident"):
                incident_id = str(uuid.uuid4())
                db.collection("incidents").document(incident_id).set({
                    "id": incident_id,
                    "type": incident_type,
                    "description": description,
                    "impact": impact,
                    "assigned_team": "Field Team",
                    "status": "Reported",
                    "lat": latitude,
                    "lng": longitude,
                    "reported_date": str(datetime.today().date()),
                    "resolved_date": None
                })
                st.success("Incident reported!")

# --------------------------
# Approval Management
# --------------------------
def manage_approvals():
    st.header("📝 Approval Requests")

    with st.expander("➕ New Approval Request"):
        with st.form("approval_form"):
            project_id = st.text_input("Project ID")
            request_type = st.selectbox("Request Type", ["Funding", "Land Access", "Permits"])
            amount = st.number_input("Budget Needed ($)", min_value=0)
            submitted_by = st.text_input("Submitted By")

            if st.form_submit_button("Submit Request"):
                approval_id = str(uuid.uuid4())
                db.collection("approvals").document(approval_id).set({
                    "id": approval_id,
                    "project_id": project_id,
                    "request_type": request_type,
                    "amount": amount,
                    "submitted_by": submitted_by,
                    "submitted_date": str(datetime.today().date()),
                    "status": "Pending"
                })
                st.success("✅ Approval request submitted!")

    st.subheader("📜 Existing Approval Requests")
    approvals = list(db.collection("approvals").stream())
    if approvals:
        approval_data = [doc.to_dict() for doc in approvals]
        df = pd.DataFrame(approval_data)
        st.dataframe(df)

    st.subheader("🗑️ Delete Old Approvals")
    days = st.number_input("Delete approvals older than (days)", min_value=1, value=30)
    if st.button("Delete Old Approvals"):
        delete_old_approvals(days)

# --------------------------
# Admin Page
# --------------------------
def admin_page():
    st.header("🔑 Admin Approval Page")

    pending_approvals = list(db.collection("approvals").where("status", "==", "Pending").stream())

    if pending_approvals:
        st.subheader("Pending Approvals")
        for doc in pending_approvals:
            row = doc.to_dict()
            with st.expander(f"Project ID: {row['project_id']}"):
                st.write(f"Request Type: {row['request_type']}")
                st.write(f"Amount: ${row['amount']}")
                st.write(f"Submitted By: {row['submitted_by']}")

                col1, col2 = st.columns(2)
                approval_id = row['id']

                if col1.button("Approve", key=f"{approval_id}_approve"):
                    db.collection("approvals").document(approval_id).update({"status": "Approved"})
                    st.success(f"Project ID {row['project_id']} approved!")

                if col2.button("Reject", key=f"{approval_id}_reject"):
                    db.collection("approvals").document(approval_id).update({"status": "Rejected"})
                    st.error(f"Project ID {row['project_id']} rejected!")
    else:
        st.write("No pending approvals found.")

    st.subheader("📜 Existing Approval Requests")
    fetch_approvals()
    # approvals = list(db.collection("approvals").stream())
    # if approvals:
    #     approval_data = [doc.to_dict() for doc in approvals]
    #     df = pd.DataFrame(approval_data)
    #     st.dataframe(df)

# --------------------------
# Main Application
# --------------------------
def main():
    st.set_page_config(page_title="EcoGuardian", page_icon="🌿", layout="wide")
    st.title("🌍 EcoGuardian Dashboard")

    st.sidebar.header("Navigation")
    menu = st.sidebar.selectbox("Menu", ["Projects", "Incidents", "Approvals", "Admin Page"])

    if menu == "Projects":
        manage_projects()
    elif menu == "Incidents":
        manage_incidents()
    elif menu == "Approvals":
        manage_approvals()
    elif menu == "Admin Page":
        admin_page()

if __name__ == "__main__":
    main()
