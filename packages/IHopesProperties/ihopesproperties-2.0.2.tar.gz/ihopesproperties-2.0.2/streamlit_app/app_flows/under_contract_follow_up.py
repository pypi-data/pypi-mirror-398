import streamlit as st

from flows.under_contract_follow_up_flow.flow import run_under_contract_leads_flow


def run_under_contract_follow_up_flow():
    st.title("📞 Under Contract Follow-Up")
    st.write("Track, manage and organize our current under contract leads.")

    if st.button("Organize Under Contract Properties"):
        with st.spinner("Running..."):
            try:
                st.info(f"Under contract flow has been triggered.")
                run_under_contract_leads_flow()
                st.success(f"Under contract flow has been completed.")

            except Exception as e:
                st.error(f"Error: {e}")
