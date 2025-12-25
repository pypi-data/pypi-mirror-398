import os
import sys
from datetime import datetime
import streamlit as st

from flows.flows_meta import Flow
from flows.update_comps.flow import address_based_comps_update_flow
from my_asana.generate_tasks.tasks_generator import GeneratedTask

sys.path.append(os.path.abspath("src"))

from flows.leads_generator_flow.flow.lead_flow import address_based_lead_flow
from google_drive.authenticator import get_google_services, GoogleServices

LEADS = []

def create_lead(address):
    return {
        "id": len(LEADS) + 1,
        "address": address,
        "status": "processing",
        "processedDate": datetime.now().isoformat()
    }

def update_lead(lead, **kwargs):
    lead.update(kwargs)

def run_single_lead_analyzer_flow():
    st.title("🏡 Property Lead Analyzer 🏡")
    st.write("Enter a property address to retrieve its comps and create Asana task.")

    if "current_lead" not in st.session_state:
        st.session_state.current_lead = None
    if "error" not in st.session_state:
        st.session_state.error = None
    if 'current_address' not in st.session_state:
        st.session_state.current_address = None

    address = st.text_input("Property Address")
    processing_mode = st.radio(
        "Choose a processing mode:",
        ("Generate new lead & comps", "Update comps for existing lead")
    )
    if st.button("Process"):
        if address:
            st.session_state.error = None
            st.session_state.current_address = address
            lead = create_lead(address)
            LEADS.insert(0, lead)
            st.session_state.current_lead = lead

            google_services: GoogleServices = get_google_services()
            if google_services is None:
                st.warning("Authentication failed or not completed.")
                st.stop()

            with st.spinner("Processing property..."):
                try:
                    if processing_mode == "Generate new lead & comps":
                        generated_task: GeneratedTask = address_based_lead_flow(
                            address=address,
                            flow=Flow.GENERATE_LEADS
                        )
                        update_lead(lead, status="completed", property_link=generated_task.task_link)
                    elif processing_mode == "Update comps for existing lead":
                        new_comps_number: int = address_based_comps_update_flow(address=address)
                        print(f"New comps added: {new_comps_number}")
                        update_lead(lead, status="completed", new_comps_number=new_comps_number)
                    else:
                        st.warning("Please select a processing mode.")
                        return
                except Exception as e:
                    update_lead(lead, status="failed")
                    st.session_state.error = str(e)
        else:
            st.warning("Please enter an address.")

    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")

    if st.session_state.current_lead and st.session_state.current_lead["status"] == "completed":
        lead = st.session_state.current_lead
        if 'property_link' in lead:
            st.success("Processing complete! See link to Asana task below.")
        elif 'new_comps_number' in lead:
            st.success(f"Processing complete! Added {lead['new_comps_number']} new comps to the existing lead.")
        else:
            st.warning(f"Couldn't create a new task")
        st.json(lead)

    st.subheader("📜 Recent Leads")
    if LEADS:
        st.table([{
            "Address": l["address"],
            "Status": l["status"],
            "Date": l["processedDate"][:10],
            "Asana task": l['property_link'] if 'property_link' in l else "N/A",
        } for l in LEADS])
    else:
        st.info("No leads yet.")
