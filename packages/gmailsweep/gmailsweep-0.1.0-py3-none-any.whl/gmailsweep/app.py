import os
import time
import datetime
import pandas as pd
import streamlit as st
import pandas as pd
import time
import datetime
import os
from pathlib import Path

# Global Config Path
CONFIG_DIR = Path.home() / '.gmailsweep'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


st.set_page_config(page_title="GmailSweep", page_icon="🧹", layout="wide")

CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

def show_setup_screen():
    st.title("👋 Welcome to GmailSweep")
    st.markdown(f"""
    ### Setup Required
    To use this tool, you need to provide your **Google Cloud Credentials**.
    
    **How to get them:**
    1. Go to [Google Cloud Console](https://console.cloud.google.com/).
    2. Create a Project and enable the **Gmail API**.
    3. Go to **APIs & Services > Credentials**.
    4. Create **OAuth Client ID** (Desktop App).
    5. Download the JSON file and rename it to `credentials.json`.
    
    *Credentials will be saved securely to: `{CONFIG_DIR}`*
    """)
    
    tab1, tab2 = st.tabs(["📂 Upload File", "📝 Paste JSON"])
    
    with tab1:
        uploaded_file = st.file_uploader("Upload your credentials.json", type=['json'])
        if uploaded_file is not None:
            if st.button("Save File & Continue", type="primary"):
                with open(CREDENTIALS_FILE, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Credentials saved! Reloading...")
                time.sleep(1)
                st.rerun()

    with tab2:
        json_content = st.text_area("Paste the content of credentials.json here", height=300)
        # Always show button
        if st.button("Save JSON & Continue", type="primary"):
            if not json_content.strip():
                st.error("Please paste valid JSON content.")
            else:
                try:
                    with open(CREDENTIALS_FILE, "w") as f:
                        f.write(json_content)
                    st.success("Credentials saved! Reloading...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving file: {e}")

def main_app():
    from gmailsweep.logic import fetch_messages, get_message_details, batch_delete_messages, fetch_total_count
    
    st.title("🧹 GmailSweep")
    st.markdown("### Clean up your inbox safely and efficiently.")

    with st.sidebar:
        st.header("🔍 Filters")
        
        keyword = st.text_input("Search (Subject, Body, etc.)", "")
        sender_query = st.text_input("Sender Email (From)", "")
        date_mode = st.selectbox("Date Filter", ["Any Time", "Specific Year", "Date Range"])
        
        date_query = ""
        if date_mode == "Specific Year":
            year = st.number_input("Year", min_value=2000, max_value=datetime.date.today().year, value=datetime.date.today().year - 1, step=1)
            date_query = f"after:{year}/01/01 before:{year + 1}/01/01"
        elif date_mode == "Date Range":
            col_d1, col_d2 = st.columns(2)
            d_start = col_d1.date_input("From", value=datetime.date.today() - datetime.timedelta(days=30))
            d_end = col_d2.date_input("To", value=datetime.date.today())
            if d_start and d_end:
                d_end_exclusive = d_end + datetime.timedelta(days=1)
                date_query = f"after:{d_start.strftime('%Y/%m/%d')} before:{d_end_exclusive.strftime('%Y/%m/%d')}"

        # Safety Flags
        st.divider()
        st.caption("Safety Filters (Applied automatically)")
        exclude_starred = st.checkbox("Exclude Starred", value=True)
        exclude_important = st.checkbox("Exclude Important (Recommended if deleting)", value=True)
        
        if not exclude_starred:
            st.warning("⚠️ Started emails will be INCLUDED in deletion!")
        if not exclude_important:
            st.warning("⚠️ Important emails (bills, updates) will be INCLUDED in the deletion!")
        
        query_parts = []
        if keyword: 
            query_parts.append(keyword)
        if sender_query: 
            query_parts.append(f"from:{sender_query}")
        if date_query: 
            query_parts.append(date_query)
        
        # Only apply safety filters if user checked them OR if we are doing a deletion run?
        # Actually user expects to see everything in overview.
        if exclude_starred: 
            query_parts.append("-is:starred")
        if exclude_important: 
            query_parts.append("-is:important")
        
        final_query = " ".join(query_parts).strip()
        st.code(final_query or " (All Emails) ", language="text")
        
        has_user_filter = bool(keyword or sender_query or date_query)
        
        # Remove Advanced Settings - Unlimited Scan
        # max_results_limit removed
        
        search_btn = st.button("🔎 Scan Emails", type="primary")

    if 'messages' not in st.session_state: st.session_state.messages = []
    if 'scanned' not in st.session_state: st.session_state.scanned = False
    if 'df' not in st.session_state: st.session_state.df = pd.DataFrame()
    if 'yearly_df' not in st.session_state: st.session_state.yearly_df = pd.DataFrame()

    if search_btn:
        if not has_user_filter:
            st.warning("⚠️ Scanning the entire inbox without filters typically hits Google API rate limits. Please use filters (Year, Sender) for better performance.")
            # Give UI a moment to show the warning before blocking? Streamlit reruns might handle this differently, 
            # but since we are inside the button block, it will render above the spinner if placed before.
            
        with st.spinner(f"Scanning..."):
            try:
                # 1. Base Count (User Intent - No Safety Filters)
                # Reconstruct query without safety flags
                base_query_parts = []
                if keyword: base_query_parts.append(keyword)
                if sender_query: base_query_parts.append(f"from:{sender_query}")
                if date_query: base_query_parts.append(date_query)
                base_query = " ".join(base_query_parts).strip()
                
                total_est_base = fetch_total_count(base_query)
                
                # 2. Final Count (With Safety Filters)
                total_est_final = fetch_total_count(final_query)
                
                # 3. Message Scan (Unlimited - Fetches ALL matching emails)
                msgs = fetch_messages(final_query, max_results=None)

                # CORRECTION: If we fetched more messages than the estimate, the estimate is wrong.
                # Trust the actual fetched count.
                if len(msgs) > total_est_final:
                    total_est_final = len(msgs)

                st.session_state.total_est_base = total_est_base
                st.session_state.total_est = total_est_final
                st.session_state.base_query = base_query 
                st.session_state.is_overview = not has_user_filter
                st.session_state.messages = msgs
                st.session_state.scanned = True
                

                # 4. Yearly Breakdown 
                # User requested NOT to show yearly count in overview mode to simplify.
                if st.session_state.is_overview:
                    st.session_state.yearly_df = pd.DataFrame() # Empty
                else:
                    st.session_state.yearly_df = pd.DataFrame()

                # Clear previous detail DF
                st.session_state.df = pd.DataFrame() 
                    
            except Exception as e:
                st.error(f"Error scanning emails: {e}")

    # --- RESULTS DISPLAY ---
    if st.session_state.scanned:
        count = len(st.session_state.messages)
        total_est_base = st.session_state.get('total_est_base', 0)
        base_query = st.session_state.get('base_query', '') 
        is_overview = st.session_state.get('is_overview', False)
        
        # Retrieve pre-calculated stats
        
        col1, col2 = st.columns([3, 1])
        with col1:
             st.info(f"**Total Matching Emails: {count:,}**")
                 
        with col2:
             if st.button("🔄 Clear Results"):
                st.session_state.scanned = False
                st.session_state.messages = []
                st.session_state.df = pd.DataFrame()
                st.session_state.yearly_df = pd.DataFrame()
                st.rerun()

        # Overview Mode Specifics
        if is_overview:
            st.markdown(f"""
            ### 🦅 Overview Mode
            Analyzing your inbox health. 
            - **Top Senders**: Based on the latest **{count}** emails (Sample).
            """)
        else:
             st.markdown(f"### 🔎 Search Results")

        # Fetch details for charts if not done or if messages changed
        # We check if we have a DF matching the current messages
        if st.session_state.df.empty and count > 0:
            with st.spinner("Analyzing headers for charts..."):
                 prog = st.progress(0, "Fetching details...")
                 st.session_state.df = get_message_details(st.session_state.messages, lambda p: prog.progress(p))
                 prog.empty()

        # --- CHARTS ---
        tab1, tab2 = st.tabs(["📧 Top Senders", "📋 Message List"])
        
        df = st.session_state.df

        with tab1:
            if not df.empty:
                st.caption(f"Top senders from the analyzed emails.")
                sender_counts = df['From'].value_counts().reset_index()
                sender_counts.columns = ['Sender', 'Count']
                
                # Show Top 30 as requested
                limit = 30
                
                st.bar_chart(sender_counts.head(limit).set_index('Sender'))
                st.dataframe(sender_counts.head(limit), width=800, hide_index=True)
            else:
                st.write("No data to analyze.")

        with tab2:
            if is_overview:
                st.info("Message list hidden in Overview Mode.")
            elif not df.empty:
                st.dataframe(df[['From', 'Subject', 'Date']], hide_index=True)

        # --- DELETION ---
        st.divider()
        if is_overview:
            st.info("ℹ️ **Safety Lock**: You cannot delete from Overview Mode. Please apply a filter (e.g. Sender or Date) to delete emails.")
        elif count > 0:
            st.warning("⚠️ Danger Zone")
            st.markdown(f"You are about to delete **{count}** emails. (Exact count of messages found)")
            
            st.warning("⚠️ Validate any important messages before click on delete")
            
            if st.checkbox(f"I confirm I want to PERMANENTLY delete these {count} emails."):
                if st.button("🗑️ DELETE ALL MATCHING EMAILS", type="primary"):
                    with st.status("Deleting...") as s:
                        ids = [m['id'] for m in st.session_state.messages]
                        n = batch_delete_messages(ids)
                        s.update(label=f"Deleted {n} emails!", state="complete")
                        time.sleep(2)
                        st.session_state.scanned = False
                        st.session_state.messages = []
                        st.session_state.df = pd.DataFrame()
                        st.rerun()

if __name__ == "__main__":
    if CREDENTIALS_FILE.exists():
        main_app()
    else:
        show_setup_screen()
