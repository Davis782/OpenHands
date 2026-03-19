"""
PEARL AI Notary - UI Pages
"""

import streamlit as st
from datetime import datetime
from PEARL_AI_Notary.src.core import NotaryDataAccess
import pandas as pd


def render_notary_dashboard_page(notary_dal: NotaryDataAccess):
    st.title("Notary Dashboard")
    current_pearl_id = st.session_state.get('pearl_id', None)
    
    try:
        all_sessions = notary_dal.get_all_sessions()
        all_notaries = notary_dal.get_all_notaries()
        all_signers = notary_dal.get_all_signers()
        all_documents = notary_dal.get_all_documents()
        
        pending_sessions = len([s for s in all_sessions if s.get('status') == 'pending'])
        completed_sessions = len([s for s in all_sessions if s.get('status') == 'completed'])
        in_progress_sessions = len([s for s in all_sessions if s.get('status') == 'in_progress'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sessions", len(all_sessions))
        with col2:
            st.metric("Pending", pending_sessions)
        with col3:
            st.metric("In Progress", in_progress_sessions)
        with col4:
            st.metric("Completed", completed_sessions)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Registered Notaries", len(all_notaries))
        with col2:
            st.metric("Registered Signers", len(all_signers))
        with col3:
            st.metric("Documents", len(all_documents))
        
        st.markdown("---")
        
        st.subheader("Recent Notarization Sessions")
        if all_sessions:
            session_data = []
            for s in all_sessions[:10]:
                session_data.append({
                    'Session Hash': s.get('session_hash', '')[:16] + '...',
                    'Status': s.get('status', 'unknown'),
                    'State': s.get('state', 'N/A'),
                    'Payment': s.get('payment_status', 'pending'),
                    'Started': s.get('started_at', 'N/A')
                })
            
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No notarization sessions yet. Create one to get started!")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")


def render_create_session_page(notary_dal: NotaryDataAccess):
    st.title("Create Notarization Session")
    current_pearl_id = st.session_state.get('pearl_id', None)
    
    try:
        notaries = notary_dal.get_all_notaries()
        signers = notary_dal.get_all_signers()
        documents = notary_dal.get_all_documents()
        
        tab1, tab2, tab3 = st.tabs(["Create Session", "Register Notary", "Register Signer"])
        
        with tab1:
            st.header("New Notarization Session")
            
            with st.form("create_session_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    notary_options = ["Create New Notary"] + [n.get('name', 'Unknown') for n in notaries]
                    selected_notary = st.selectbox("Select Notary", notary_options)
                    
                    signer_options = ["Create New Signer"] + [s.get('name', 'Unknown') for s in signers]
                    selected_signer = st.selectbox("Select Signer", signer_options)
                
                with col2:
                    doc_options = ["Upload New Document"] + [d.get('filename', 'Unknown') for d in documents]
                    selected_document = st.selectbox("Select Document", doc_options)
                
                state_code = st.selectbox("Jurisdiction (State)", 
                    ["VA", "TX", "FL", "NY", "CA", "Other"],
                    help="Select the state where the notarization will take place")
                
                submitted = st.form_submit_button("Create Session")
                
                if submitted:
                    try:
                        notary_hash = notaries[notary_options.index(selected_notary) - 1].get('notary_hash') if selected_notary != "Create New Notary" else None
                        signer_hash = signers[signer_options.index(selected_signer) - 1].get('signer_hash') if selected_signer != "Create New Signer" else None
                        document_hash = documents[doc_options.index(selected_document) - 1].get('document_hash') if selected_document != "Upload New Document" else None
                        
                        if notary_hash and signer_hash and document_hash:
                            session_hash = notary_dal.create_session(
                                notary_hash=notary_hash,
                                signer_hash=signer_hash,
                                document_hash=document_hash,
                                state=state_code
                            )
                            
                            notary_dal.log_audit(
                                session_hash=session_hash,
                                action_type="SESSION_CREATED",
                                actor_hash=current_pearl_id,
                                actor_type="user",
                                details=f"Session created in state {state_code}"
                            )
                            
                            st.success(f"Session created successfully! Hash: {session_hash[:16]}...")
                            st.rerun()
                        else:
                            st.warning("Please select or create all required entities")
                    except Exception as e:
                        st.error(f"Error creating session: {e}")
        
        with tab2:
            st.header("Register New Notary")
            
            with st.form("register_notary_form"):
                name = st.text_input("Notary Name")
                commission_number = st.text_input("Commission Number")
                jurisdiction = st.selectbox("Jurisdiction", ["VA", "TX", "FL", "NY", "CA", "Other"])
                commission_expiry = st.date_input("Commission Expiry Date")
                
                submitted = st.form_submit_button("Register Notary")
                
                if submitted and name and commission_number:
                    try:
                        notary_hash = notary_dal.create_notary(
                            name=name,
                            commission_number=commission_number,
                            jurisdiction=jurisdiction,
                            commission_expiry=str(commission_expiry)
                        )
                        
                        notary_dal.log_audit(
                            session_hash=None,
                            action_type="NOTARY_REGISTERED",
                            actor_hash=notary_hash,
                            actor_type="notary",
                            details=f"Notary {name} registered"
                        )
                        
                        st.success(f"Notary registered successfully! Hash: {notary_hash[:16]}...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error registering notary: {e}")
        
        with tab3:
            st.header("Register New Signer")
            
            with st.form("register_signer_form"):
                name = st.text_input("Signer Name")
                email = st.text_input("Email (Optional)")
                phone = st.text_input("Phone (Optional)")
                address = st.text_area("Address (Optional)")
                
                col1, col2 = st.columns(2)
                with col1:
                    id_type = st.selectbox("ID Type", ["Driver's License", "Passport", "State ID", "Other"])
                with col2:
                    id_number = st.text_input("ID Number")
                
                submitted = st.form_submit_button("Register Signer")
                
                if submitted and name:
                    try:
                        signer_hash = notary_dal.create_signer(
                            name=name,
                            email=email,
                            phone=phone,
                            address=address,
                            id_type=id_type,
                            id_number=id_number
                        )
                        
                        notary_dal.log_audit(
                            session_hash=None,
                            action_type="SIGNER_REGISTERED",
                            actor_hash=signer_hash,
                            actor_type="signer",
                            details=f"Signer {name} registered"
                        )
                        
                        st.success(f"Signer registered successfully! Hash: {signer_hash[:16]}...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error registering signer: {e}")
                        
    except Exception as e:
        st.error(f"Error loading form: {e}")


def render_manage_sessions_page(notary_dal: NotaryDataAccess):
    st.title("Manage Notarization Sessions")
    current_pearl_id = st.session_state.get('pearl_id', None)
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", 
            ["All", "pending", "in_progress", "completed", "cancelled"])
    with col2:
        state_filter = st.selectbox("Filter by State",
            ["All", "VA", "TX", "FL", "NY", "CA", "Other"])
    
    try:
        all_sessions = notary_dal.get_all_sessions()
        
        filtered_sessions = all_sessions
        if status_filter != "All":
            filtered_sessions = [s for s in filtered_sessions if s.get('status') == status_filter]
        if state_filter != "All":
            filtered_sessions = [s for s in filtered_sessions if s.get('state') == state_filter]
        
        if filtered_sessions:
            for session in filtered_sessions:
                with st.expander(f"Session: {session.get('session_hash', '')[:16]}... - {session.get('status', 'unknown')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Status:** {session.get('status', 'N/A')}")
                        st.write(f"**State:** {session.get('state', 'N/A')}")
                        st.write(f"**Payment:** {session.get('payment_status', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Started:** {session.get('started_at', 'N/A')}")
                        st.write(f"**Completed:** {session.get('completed_at', 'N/A')}")
                    
                    st.markdown("---")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if session.get('status') == 'pending':
                            if st.button(f"Start Session", key=f"start_{session.get('session_hash')}"):
                                notary_dal.update_session_status(session.get('session_hash'), 'in_progress')
                                notary_dal.log_audit(
                                    session_hash=session.get('session_hash'),
                                    action_type="SESSION_STARTED",
                                    actor_hash=current_pearl_id,
                                    actor_type="user",
                                    details="Session started"
                                )
                                st.rerun()
                    
                    with action_col2:
                        if session.get('status') == 'in_progress':
                            if st.button(f"Complete", key=f"complete_{session.get('session_hash')}"):
                                notary_dal.update_session_status(session.get('session_hash'), 'completed')
                                notary_dal.log_audit(
                                    session_hash=session.get('session_hash'),
                                    action_type="SESSION_COMPLETED",
                                    actor_hash=current_pearl_id,
                                    actor_type="user",
                                    details="Session completed"
                                )
                                st.rerun()
                    
                    with action_col3:
                        if session.get('status') in ['pending', 'in_progress']:
                            if st.button(f"Cancel", key=f"cancel_{session.get('session_hash')}"):
                                notary_dal.update_session_status(session.get('session_hash'), 'cancelled')
                                notary_dal.log_audit(
                                    session_hash=session.get('session_hash'),
                                    action_type="SESSION_CANCELLED",
                                    actor_hash=current_pearl_id,
                                    actor_type="user",
                                    details="Session cancelled"
                                )
                                st.rerun()
                    
                    st.markdown("### Audit Logs")
                    audit_logs = notary_dal.get_session_audit_logs(session.get('session_hash'))
                    if audit_logs:
                        for log in audit_logs:
                            st.write(f"- **{log.get('action_type')}**: {log.get('details', '')} ({log.get('created_at', '')})")
                    else:
                        st.info("No audit logs yet")
        else:
            st.info("No sessions match your filters")
            
    except Exception as e:
        st.error(f"Error loading sessions: {e}")


def render_audit_logs_page(notary_dal: NotaryDataAccess):
    st.title("Notary Audit Logs")
    
    try:
        all_sessions = notary_dal.get_all_sessions()
        
        session_options = ["All Sessions"] + [s.get('session_hash', '')[:16] + '...' for s in all_sessions]
        selected_session = st.selectbox("Select Session", session_options)
        
        if selected_session == "All Sessions":
            st.subheader("All Audit Logs")
            all_logs = []
            for session in all_sessions:
                logs = notary_dal.get_session_audit_logs(session.get('session_hash'))
                for log in logs:
                    log['session_short'] = session.get('session_hash', '')[:16] + '...'
                    all_logs.append(log)
            
            if all_logs:
                all_logs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                for log in all_logs[:50]:
                    with st.container():
                        st.write(f"**{log.get('action_type', 'UNKNOWN')}** - {log.get('session_short', 'N/A')}")
                        st.write(f"Actor: {log.get('actor_type', 'N/A')} | {log.get('created_at', 'N/A')}")
                        if log.get('details'):
                            st.write(f"Details: {log.get('details')}")
                        st.markdown("---")
            else:
                st.info("No audit logs found")
        else:
            session_hash = all_sessions[session_options.index(selected_session) - 1].get('session_hash')
            st.subheader(f"Audit Logs for Session {selected_session}")
            
            logs = notary_dal.get_session_audit_logs(session_hash)
            
            if logs:
                for log in logs:
                    with st.container():
                        st.write(f"**{log.get('action_type', 'UNKNOWN')}")
                        st.write(f"Actor: {log.get('actor_type', 'N/A')} | {log.get('created_at', 'N/A')}")
                        if log.get('details'):
                            st.write(f"Details: {log.get('details')}")
                        st.markdown("---")
            else:
                st.info("No audit logs for this session")
                
    except Exception as e:
        st.error(f"Error loading audit logs: {e}")


def render_state_rules_page(notary_dal: NotaryDataAccess):
    st.title("Multi-State Rules Configuration")
    
    tab1, tab2 = st.tabs(["View Rules", "Add/Update Rule"])
    
    with tab1:
        st.header("Current State Rules")
        try:
            rules = notary_dal.get_all_state_rules()
            
            if rules:
                for rule in rules:
                    with st.expander(f"{rule.get('state_name', 'Unknown')} ({rule.get('state_code', 'N/A')})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**RON Allowed:** {'Yes' if rule.get('ron_allowed') else 'No'}")
                            st.write(f"**Notary Location Required:** {'Yes' if rule.get('notary_location_required') else 'No'}")
                            st.write(f"**ID Verification:** {rule.get('id_verification', 'N/A')}")
                        with col2:
                            st.write(f"**Retention (Years):** {rule.get('retention_years', 'N/A')}")
                            st.write(f"**Certificate Template:** {rule.get('certificate_template', 'N/A')}")
                        st.write(f"**Signer Location Allowed:** {rule.get('signer_location_allowed', 'N/A')}")
            else:
                st.info("No state rules configured. Add rules in the 'Add/Update Rule' tab.")
        except Exception as e:
            st.error(f"Error loading rules: {e}")
    
    with tab2:
        st.header("Add or Update State Rule")
        
        with st.form("add_rule_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                state_code = st.text_input("State Code (e.g., VA)", max_chars=2)
                state_name = st.text_input("State Name (e.g., Virginia)")
                ron_allowed = st.checkbox("RON Allowed", value=True)
                notary_location_required = st.checkbox("Notary Location Required", value=True)
            
            with col2:
                id_verification = st.selectbox("ID Verification Standard", 
                    ["NIST-IAL1", "NIST-IAL2", "NIST-IAL3"])
                retention_years = st.number_input("Retention Years", min_value=1, max_value=10, value=5)
                certificate_template = st.text_input("Certificate Template", value="STATE_RON_2026")
            
            signer_location_allowed = st.multiselect("Signer Location Allowed", 
                ["US", "International"], default=["US"])
            
            allowed_documents = st.multiselect("Allowed Documents",
                ["affidavit", "power_of_attorney", "real_estate", "vehicle_title", "contract", "other"],
                default=["affidavit", "power_of_attorney", "real_estate"])
            
            submitted = st.form_submit_button("Save Rule")
            
            if submitted and state_code and state_name:
                try:
                    notary_dal.create_state_rule(
                        state_code=state_code.upper(),
                        state_name=state_name,
                        ron_allowed=1 if ron_allowed else 0,
                        notary_location_required=1 if notary_location_required else 0,
                        id_verification=id_verification,
                        retention_years=retention_years,
                        certificate_template=certificate_template,
                        signer_location_allowed=str(signer_location_allowed),
                        allowed_documents=allowed_documents
                    )
                    st.success(f"Rule for {state_name} saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving rule: {e}")


__all__ = [
    'render_notary_dashboard_page',
    'render_create_session_page',
    'render_manage_sessions_page',
    'render_audit_logs_page',
    'render_state_rules_page'
]
