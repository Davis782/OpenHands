# Product Requirements Document: PEARL AI Folder Structure Report

## 1. Introduction

This document outlines the requirements for implementing a "Folder Structure Report" feature within the PEARL AI Streamlit application. This report aims to provide users with a clear, hierarchical overview of their PEARL-identified data, enhancing navigability and understanding of the database's contents. The report will dynamically display PEARL IDs, the tables associated with each ID, and potentially high-level metadata, all while respecting the active PEARL ID's data access permissions.

## 2. Goals

*   **Improve Data Discoverability:** Enable users to easily see and understand the structure of their PEARL-identified data within the `pearl.db`.
*   **Enhance User Experience:** Provide an intuitive, hierarchical view that simplifies navigation and comprehension of stored entities.
*   **Reinforce Security Model:** Ensure the report only displays data accessible by the currently active PEARL ID, upholding the system's row-level security.
*   **Aid Development & Debugging:** Offer a valuable tool for developers and advanced users to inspect data organization and verify data integrity.

## 3. Key Features

### 3.1. Hierarchical View
*   **Top Level:** List all PEARL IDs that the currently active user (via their unlocked vault) has access to.
*   **Second Level:** For each accessible PEARL ID, list all database tables that contain records associated with that specific PEARL ID.
*   **Third Level (Optional/Future):** Display high-level summaries or counts of records within each table for a given PEARL ID.

### 3.2. Permission-Based Display
*   The report will strictly adhere to the `PEARL_ID`'s data access permissions. If a `PEARL_ID` is not active or the user does not have permission to view its data, that `PEARL_ID` and its associated tables will not appear in the report.
*   The report will leverage the existing `DataAccess` layer to ensure all data retrieval respects the active `PEARL_ID` context.

### 3.3. Interactive UI Component
*   The report will be presented within the Streamlit UI, potentially using expandable/collapsible elements (e.g., `st.expander`) for a clean, navigable interface.
*   Display PEARL IDs and table names clearly.

### 3.4. Dynamic Updates
*   The report should reflect the current state of the database and the active PEARL ID upon generation or refresh.

## 4. Technical Considerations

### 4.1. Backend Data Retrieval Logic
*   **Identify All PEARL IDs:** Query the `Pearls` table to retrieve all known `pearl_id`s.
*   **Identify Tables with `PEARL_ID` Column:** Dynamically inspect the database schema (e.g., `PRAGMA table_info(table_name)`) to find all tables that contain a `pearl_id` column.
*   **Check for Data Existence:** For each identified table and each accessible `PEARL_ID`, perform a `SELECT COUNT(*)` query with `WHERE pearl_id = ?` to determine if the `PEARL_ID` has data in that table. This ensures we only show relevant tables.
*   **Leverage `DataAccess`:** All database interactions for the report must go through the `DataAccess` layer to ensure `PEARL_ID` context and security are maintained.
*   **Performance:** Optimize queries to avoid performance bottlenecks, especially for databases with many PEARL IDs or tables. Caching mechanisms (e.g., `st.cache_data`) might be considered for the report's output.

### 4.2. Streamlit UI Implementation
*   Use `st.expander` or similar Streamlit components to create the hierarchical "folder" view.
*   Display PEARL IDs as top-level items.
*   Display table names as sub-items under each PEARL ID.
*   Consider displaying a count of records next to each table name.

### 4.3. Integration with Existing System
*   The report will be accessible from the `main_app.py` UI, likely as a dedicated section or button.
*   It will utilize the `AgentPearl` instance to access the `DataAccess` layer and the active `PEARL_ID` context.

## 5. Acceptance Criteria

*   The report successfully displays a list of all PEARL IDs accessible by the currently active user.
*   For each accessible PEARL ID, the report accurately lists all tables that contain data associated with that specific PEARL ID.
*   The report does not display any PEARL IDs or associated data that the active user does not have permission to view.
*   The UI presents the information in a clear, hierarchical, and navigable format.
*   The report generates within a reasonable time frame, even with a moderate amount of data.
*   All database interactions for the report are routed through the `DataAccess` layer, respecting `PEARL_ID` isolation.
