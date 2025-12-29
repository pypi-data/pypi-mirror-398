import streamlit as st
import sys, os

sys.path.append(os.path.abspath("src"))

from app_flows.analyze_lead import run_single_lead_analyzer_flow
from app_flows.leads_cleaner import run_leads_cleaner_flow
from app_flows.under_contract_follow_up import run_under_contract_follow_up_flow
from app_flows.leads_generator import run_leads_generator_flow
from app_flows.listing_expired import run_expired_listings_extractor

#st.sidebar.title("📋 Flow Selector")
st.set_page_config(page_title="IHopes25To40 Tool", layout="centered")
st.title("🛠️ IHopes25To40 Tools Box 🛠️")

flow = st.sidebar.selectbox(
    "Choose a flow:",
    [
        "Single Lead Analyzer",
        "Leads Generator",
        "Leads Cleaner",
        "Under Contract Organizer",
        "Expired Listings Extractor"
    ]
)

if flow == "Single Lead Analyzer":
    run_single_lead_analyzer_flow()
elif flow == "Leads Generator":
    run_leads_generator_flow()
elif flow == "Leads Cleaner":
    run_leads_cleaner_flow()
elif flow == "Under Contract Organizer":
    run_under_contract_follow_up_flow()
elif flow == "Expired Listings Extractor":
    run_expired_listings_extractor()
else:
    raise ValueError("Invalid flow selected.")
