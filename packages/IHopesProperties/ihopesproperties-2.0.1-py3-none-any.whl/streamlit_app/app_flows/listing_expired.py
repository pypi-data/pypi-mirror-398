import streamlit as st
import pandas as pd

from flows.listing_expired_flow.flow import run_listing_expired_flow


def run_expired_listings_extractor():
    st.header("🏡⏰ Expired Listings Extractor 🏡⏰")
    st.write("Upload a CSV file from your local machine and run the listing expired flow.")

    st.info(
        """
        **📋 How to export your CSV correctly**

        Before uploading your CSV:
        1. Go to the **OneHome map view**.  
        2. In the **“Sort by”** menu, select **“Newest”**.  
        3. Then switch to **List View** and export your CSV.  

        This ensures that the newest properties appear **first**, so the system knows when to stop 
        upon encountering the first already-analyzed property.
        """
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df: pd.DataFrame = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded CSV file with {len(df)} rows and {len(df.columns)} columns.")
            with st.expander("Preview Data"):
                st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"❌ Failed to read CSV file: {e}")
            return

    # --- New Feature: Skip previously-seen properties ---
    st.markdown("### ⚙️ Processing Options")

    with st.expander("Advanced Options", expanded=False):
        st.markdown(
            """
            **ℹ️ Skip Previously Seen Properties**

            By default, the system will **stop** as soon as it encounters the **first property**
            that has already been analyzed before.  

            This is intentional — because the CSV is sorted by *newest first*, encountering the
            first already-seen property means **all following ones were also analyzed earlier**.

            If you enable this option, the system will **not stop** at that point.  
            It means that we will **run over all properties** in the file.
            """
        )

        skip_seen = st.checkbox(
            "Skip already-analyzed properties (advanced users only)",
            value=False,
            help="If checked, the flow will continue to process all properties, even those already analyzed before."
        )

        if skip_seen:
            st.warning(
                "⚠️ You have chosen to skip already-analyzed properties. "
                "The system will run over all properties in the CSV instead of stopping at the first known one."
            )
            confirm_skip = st.checkbox("✅ I understand and want to proceed with this behavior.")
        else:
            confirm_skip = False

    # --- Run button ---
    if st.button("Run"):
        if uploaded_file is None:
            st.warning("Please upload a CSV file before running.")
            return

        if skip_seen and not confirm_skip:
            st.warning("Please confirm you understand the implications of skipping previously seen properties.")
            return

        st.info("Running listing expired flow on uploaded CSV...")
        try:
            run_listing_expired_flow(expired_listings_df=df, stop_on_the_first_already_existing_property=not skip_seen)
            st.success("✅ Process completed successfully!")
        except Exception as e:
            st.error(f"❌ Failed to complete process: {e}")
