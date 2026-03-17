"""
Public Voting 2026 - Election Management UI Page
"""

import streamlit as st
from datetime import datetime, timedelta
from Public_Voting_2026.src.core import VotingDataAccess


def render_election_management_page(voting_dal: VotingDataAccess):
    """Render the election management page"""
    st.title("Election Management")
    
    # Check if user has PEARL ID (for verification)
    current_pearl_id = st.session_state.get('pearl_id', None)
    
    # Tabs for different management functions
    tab1, tab2, tab3 = st.tabs(["Create Election", "Active Elections", "Manage Election"])
    
    with tab1:
        st.header("Create New Election")
        
        with st.form("create_election_form"):
            title = st.text_input("Election Title", placeholder="e.g., 2026 Board Election")
            description = st.text_area("Description", placeholder="Describe the election purpose...")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now().date())
                start_time = st.time_input("Start Time", value=datetime.now().time())
            with col2:
                end_date = st.date_input("End Date", value=(datetime.now() + timedelta(days=7)).date())
                end_time = st.time_input("End Time", value=datetime.now().time())
            
            st.subheader("Election Options")
            col3, col4 = st.columns(2)
            with col3:
                is_anonymous = st.checkbox("Anonymous Voting", value=True, 
                    help="Voter identities will be kept confidential")
                require_pearl_id = st.checkbox("Require PEARL ID Verification", value=True,
                    help="Voters must verify their PEARL ID to vote")
            with col4:
                max_votes = st.number_input("Max Votes per Voter", min_value=1, value=1)
                allow_write_in = st.checkbox("Allow Write-in Candidates", value=False)
            
            submitted = st.form_submit_button("Create Election")
            
            if submitted and title:
                try:
                    start_datetime = f"{start_date} {start_time}"
                    end_datetime = f"{end_date} {end_time}"
                    
                    election_id = voting_dal.create_election(
                        title=title,
                        description=description,
                        start_time=start_datetime,
                        end_time=end_datetime,
                        is_anonymous=1 if is_anonymous else 0,
                        require_pearl_id_verification=1 if require_pearl_id else 0,
                        max_votes_per_voter=max_votes,
                        allow_write_in_candidates=1 if allow_write_in else 0
                    )
                    
                    voting_dal.log_audit(
                        election_id=election_id,
                        action_type="ELECTION_CREATED",
                        actor_id=current_pearl_id,
                        actor_type="admin",
                        details=f"Election '{title}' created"
                    )
                    
                    st.success(f"Election created successfully! ID: {election_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating election: {e}")
            elif submitted:
                st.warning("Please enter an election title")
    
    with tab2:
        st.header("Active Elections")
        
        # Get all active elections
        elections = voting_dal.get_all_elections()
        
        if not elections:
            st.info("No elections found. Create one to get started!")
        else:
            for election in elections:
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(election['title'])
                        if election['description']:
                            st.write(election['description'])
                        st.caption(f"Status: **{election['status'].upper()}**")
                        st.caption(f"Period: {election['start_time']} to {election['end_time']}")
                    
                    with col2:
                        if st.button(f"Manage", key=f"manage_{election['election_id']}"):
                            st.session_state['selected_election_id'] = election['election_id']
                            st.rerun()
    
    with tab3:
        st.header("Manage Election")
        
        # Get selected election
        selected_id = st.session_state.get('selected_election_id', None)
        
        if not selected_id:
            st.info("Select an election from the 'Active Elections' tab to manage it")
            return
        
        election = voting_dal.get_election(selected_id)
        if not election:
            st.error("Election not found")
            return
        
        st.subheader(f"Managing: {election['title']}")
        
        # Status management
        col1, col2, col3 = st.columns(3)
        with col1:
            if election['status'] == 'pending':
                if st.button("Start Election"):
                    voting_dal.update_election_status(selected_id, 'active')
                    voting_dal.log_audit(selected_id, "ELECTION_STARTED", current_pearl_id, "admin")
                    st.rerun()
        with col2:
            if election['status'] == 'active':
                if st.button("Close Election"):
                    voting_dal.update_election_status(selected_id, 'closed')
                    voting_dal.log_audit(selected_id, "ELECTION_CLOSED", current_pearl_id, "admin")
                    st.rerun()
        with col3:
            if election['status'] != 'cancelled':
                if st.button("Cancel Election"):
                    voting_dal.update_election_status(selected_id, 'cancelled')
                    voting_dal.log_audit(selected_id, "ELECTION_CANCELLED", current_pearl_id, "admin")
                    st.rerun()
        
        st.markdown("---")
        
        # Candidate Management
        st.subheader("Candidates")
        
        with st.expander("Add Candidate"):
            with st.form("add_candidate_form"):
                candidate_name = st.text_input("Candidate Name")
                candidate_desc = st.text_area("Candidate Description")
                order_index = st.number_input("Display Order", min_value=0, value=0)
                
                if st.form_submit_button("Add Candidate"):
                    if candidate_name:
                        voting_dal.add_candidate(selected_id, candidate_name, candidate_desc, order_index)
                        voting_dal.log_audit(selected_id, "CANDIDATE_ADDED", current_pearl_id, "admin",
                                           f"Added candidate: {candidate_name}")
                        st.success("Candidate added!")
                        st.rerun()
        
        # Display candidates
        candidates = voting_dal.get_candidates(selected_id)
        if candidates:
            for candidate in candidates:
                st.write(f"• {candidate['candidate_name']} (Order: {candidate['order_index']})")
                if candidate['candidate_description']:
                    st.caption(f"  {candidate['candidate_description']}")
        else:
            st.info("No candidates added yet")
        
        # View Results
        st.markdown("---")
        st.subheader("Results")
        
        if st.button("Calculate Results"):
            results = voting_dal.calculate_results(selected_id)
            st.success("Results calculated!")
            
            for result in results:
                st.write(f"**{result['candidate_name']}**: {result['vote_count']} votes ({result['percentage']:.1f}%)")
        
        # View Audit Log
        st.markdown("---")
        st.subheader("Audit Log")
        
        audit_log = voting_dal.get_audit_log(selected_id)
        if audit_log:
            for log in audit_log[:10]:
                st.caption(f"{log['timestamp']} - {log['action_type']} by {log['actor_type']}")
        else:
            st.info("No audit entries")


def render_voting_page(voting_dal: VotingDataAccess):
    """Render the voting page where users cast votes"""
    st.title("🗳️ Cast Your Vote")
    
    current_pearl_id = st.session_state.get('pearl_id', None)
    
    if not current_pearl_id:
        st.warning("Please set your PEARL ID in the sidebar to vote")
        return
    
    # Get voter
    voter = voting_dal.get_voter_by_pearl_id(current_pearl_id)
    if not voter:
        st.info("You need to register before voting")
        if st.button("Register as Voter"):
            voter_id = voting_dal.register_voter(current_pearl_id, current_pearl_id)
            st.success(f"Registered successfully! Voter ID: {voter_id}")
            st.rerun()
        return
    
    # Get active elections
    elections = voting_dal.get_all_elections('active')
    
    if not elections:
        st.info("No active elections at this time")
        return
    
    for election in elections:
        with st.container():
            st.markdown("---")
            st.subheader(election['title'])
            
            if election['description']:
                st.write(election['description'])
            
            # Check if already voted
            if voting_dal.has_voted(voter['voter_id'], election['election_id']):
                st.success("✓ You have already voted in this election")
                continue
            
            # Check eligibility
            if election.get('require_pearl_id_verification'):
                is_eligible = voting_dal.check_voter_eligibility(voter['voter_id'], election['election_id'])
                if not is_eligible:
                    st.warning("You are not eligible to vote in this election")
                    continue
            
            # Get candidates
            candidates = voting_dal.get_candidates(election['election_id'])
            
            if not candidates:
                st.info("No candidates available yet")
                continue
            
            # Vote selection
            selected_candidate = st.radio(
                "Select your candidate:",
                candidates,
                format_func=lambda c: c['candidate_name'],
                key=f"vote_{election['election_id']}"
            )
            
            if selected_candidate:
                st.caption(f"Vote for: {selected_candidate['candidate_name']}")
                
                if st.button("Cast Vote", key=f"cast_{election['election_id']}"):
                    try:
                        vote_id, receipt = voting_dal.cast_vote(
                            election['election_id'],
                            voter['voter_id'],
                            selected_candidate['candidate_id']
                        )
                        
                        voting_dal.log_audit(
                            election['election_id'],
                            "VOTE_CAST",
                            voter['voter_id'],
                            "voter",
                            f"Voted for {selected_candidate['candidate_name']}"
                        )
                        
                        st.success("Vote cast successfully!")
                        st.info(f"**Your Receipt Code: {receipt}**")
                        st.caption("Save this receipt code to verify your vote later")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error casting vote: {e}")


def render_results_page(voting_dal: VotingDataAccess):
    """Render the results page"""
    st.title("📊 Election Results")
    
    elections = voting_dal.get_all_elections()
    
    if not elections:
        st.info("No elections found")
        return
    
    # Select election to view
    election_options = {e['election_id']: f"{e['title']} ({e['status']})" for e in elections}
    selected_id = st.selectbox("Select Election", options=list(election_options.keys()),
                             format_func=lambda x: election_options[x])
    
    if selected_id:
        election = voting_dal.get_election(selected_id)
        st.subheader(f"Results: {election['title']}")
        
        st.caption(f"Status: {election['status'].upper()}")
        
        # Get results
        results = voting_dal.get_results(selected_id)
        
        if not results:
            st.info("No results available yet")
            return
        
        # Display results
        total_votes = sum(r['vote_count'] for r in results)
        st.metric("Total Votes", total_votes)
        
        for result in results:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(result['percentage'] / 100)
            with col2:
                st.write(f"**{result['vote_count']}** ({result['percentage']:.1f}%)")
            
            st.write(f"  {result['candidate_name']}")
            st.markdown("")


def render_verify_page(voting_dal: VotingDataAccess):
    """Render the vote verification page"""
    st.title("✅ Verify Your Vote")
    
    st.write("Enter your receipt code to verify your vote was recorded correctly")
    
    receipt_code = st.text_input("Receipt Code", placeholder="Enter your receipt code")
    
    if receipt_code:
        vote = voting_dal.get_vote_by_receipt(receipt_code.upper())
        
        if vote:
            st.success("Vote verified!")
            
            st.write(f"**Election**: {vote['election_title']}")
            st.write(f"**Candidate**: {vote['candidate_name']}")
            st.write(f"**Timestamp**: {vote['vote_timestamp']}")
            st.write(f"**Vote ID**: {vote['vote_id']}")
            
            if vote['is_valid']:
                st.info("✓ Your vote is valid and has been counted")
            else:
                st.warning(f"⚠ Vote status: {vote['validation_message']}")
        else:
            st.error("Receipt code not found. Please check and try again.")
