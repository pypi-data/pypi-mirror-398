def log(msg: str, regular_log: bool = True, app_log: bool = False):
    """
    Log messages to console and optionally to Streamlit app.
    :param msg: Message to log
    :param regular_log: If True, log to console
    :param app_log: If True, log to Streamlit app
    """
    if regular_log:
        print(msg)
    if app_log:
        import streamlit as st
        st.write(msg)
