from typing import Optional

import streamlit as st

from flows.leads_generator_flow.flow.generate_leads import generate_single_source_leads, run_generate_leads_flow
from flows.leads_generator_flow.flow.lead_source import LeadsQuerySourcesHolder, LeadQuerySource


def run_leads_generator_flow():
    st.header("🚀 Leads Generator Flow 🚀")
    st.write("Select a source to generate new leads from:")

    leads_sources_holder: LeadsQuerySourcesHolder = LeadsQuerySourcesHolder()
    options = leads_sources_holder.get_all_cities()
    options.append("All")  # Add a custom option for manual input

    selected_option = st.selectbox("Lead Source", options)

    confirm_all = False
    if selected_option == "All":
        st.warning("⚠️ You selected **All**. This will trigger all lead generation sources and may take time "
                   "and cost some money.")
        confirm_all = st.checkbox("I understand, proceed with All sources")

    if st.button("Generate Leads"):
        if selected_option == "All":
            if not confirm_all:
                st.warning("Please confirm you want to proceed with all sources.")
                return

            st.info("Running leads generation from: **All Sources**...")
            try:
                run_generate_leads_flow()
                st.success("✅ Successfully generated leads from all sources!")
            except Exception as e:
                st.error(f"❌ Failed to generate leads: {e}")
        else:
            st.info(f"Running leads generation from: **{selected_option}**...")
            try:
                lead_source: Optional[LeadQuerySource] = leads_sources_holder.get_source_by_city(city=selected_option)
                if not lead_source:
                    st.warning(f"No lead source found for city: {selected_option}")
                    return
                generate_single_source_leads(lead_source=lead_source)
                st.success(f"✅ Successfully generated leads from {selected_option}!")
            except Exception as e:
                st.error(f"❌ Failed to generate leads: {e}")
