import streamlit as st

from flows.leads_cleaner_flow.flow import run_leads_cleaner


def run_leads_cleaner_flow():
    st.title("🧹 Leads Cleaner 🧹")
    st.write("This flow will help clean and remove already sold/under contract properties from the leads section.")

    if st.button("Clean Leads"):
        with st.spinner("Running..."):
            try:
                st.info(f"Leads cleaner flow has been triggered.")
                run_leads_cleaner()
                st.success(f"Leads cleaner flow has been completed.")
            except Exception as e:
                st.error(f"Error: {e}")
