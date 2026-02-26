# User Interface Product Requirements Document (PRD)

## 1. Introduction

This document outlines the requirements for developing a user-friendly graphical interface for the PEARL AI system. The primary goal is to provide an intuitive and efficient way for users to interact with the various modules (job cost tracking, accounting, payroll, etc.) and to visualize data, moving beyond the current command-line interface.

## 2. Goal and Scope

The goal of this UI is to:
*   Provide an intuitive and accessible interface for managing project-related data.
*   Enable efficient data entry, retrieval, and modification across all core modules.
*   Offer clear and interactive data visualization and reporting capabilities.
*   Enhance the overall user experience and reduce the learning curve for new users.

The initial scope of this PRD covers:
*   The development of a web-based user interface.
*   Integration with the existing `DataAccess` layer and `PEARLqlite_DB`.
*   Support for core functionalities across selected modules (to be prioritized).
*   Leveraging `PEARL_ID` for user-specific data isolation within the UI.

## 3. Target Users

*   **Project Managers:** To track job costs, progress, and overall project health.
*   **Accountants/Bookkeepers:** To manage financial transactions, payroll, and generate financial reports.
*   **Administrators:** To manage system configurations, user access (if applicable), and master data.
*   **Field Personnel (limited access):** For time entry, material requests, or work order updates.

## 4. Key Features (Modules - Initial Prioritization)

The UI will initially focus on providing robust functionality for the following modules:

### 4.1. Job Cost Tracking
*   Create, view, edit jobs.
*   Assign cost categories and track expenses against jobs.
*   View real-time job profitability and budget vs. actuals.

### 4.2. Contact Management
*   Add, view, edit, and search for contacts (clients, subcontractors, suppliers).
*   Associate contacts with jobs and financial transactions.

### 4.3. Reporting Dashboard
*   Interactive dashboards for key performance indicators (KPIs).
*   Ability to generate customizable reports (e.g., job cost summaries, financial statements).
*   Export reports to common formats (CSV, PDF).

### 4.4. PEARL ID Management
*   A dedicated sidebar dropdown for selecting the active PEARL ID, which scopes all subsequent data operations.
*   Integration with the Master PEARL ID Seed for vault unlocking and limited access entry creation.

*(Further modules like Accounting, Payroll, Estimating, etc., will be integrated in subsequent phases based on user feedback and business priority.)*

## 5. Technology Stack

### 5.1. Frontend: Streamlit (Primary Candidate)
*   **Rationale:** Streamlit offers rapid development of interactive web applications purely in Python, significantly reducing development time for data-centric UIs. Its component model is well-suited for dashboards and data entry forms.
*   **Key Capabilities:** Interactive widgets, data display (tables, charts), multi-page applications.

### 5.2. Backend: Python with Existing `DataAccess` Layer
*   **Rationale:** Leverage the existing `PEARLqlite_DB` and the newly defined `DataAccess` layer for all database interactions. This ensures consistency, security, and data isolation via `PEARL_ID`.
*   **Integration:** Streamlit application will directly call functions within the `DataAccess` layer.

## 6. Architectural Considerations

### 6.1. Separation of Concerns
The UI (Streamlit) will be responsible solely for presentation and user interaction. All business logic and data persistence will reside in the existing backend modules and the `DataAccess` layer.

### 6.2. PEARL_ID Context Management
Upon user authentication (e.g., unlocking a vault via the CLI or a future UI-based authentication flow, potentially using a Master PEARL ID Seed), the active `PEARL_ID` will be passed to the `DataAccess` layer. All data displayed or modified through the UI will be strictly scoped to this `PEARL_ID`. The UI will also interact with the `LimitedAccessKeyStore` for managing granular access.

### 6.3. Scalability (Streamlit Specific)
While Streamlit is excellent for internal tools and dashboards, for very high concurrent user loads, a more traditional client-server architecture with a dedicated web framework (e.g., Flask/Django API + React/Vue frontend) might be considered in the future. For initial deployment, Streamlit's capabilities are sufficient.

## 7. User Experience (UX) Design Principles

*   **Simplicity:** Clean, uncluttered interface with clear navigation.
*   **Intuitiveness:** Easy to understand and use without extensive training.
*   **Responsiveness:** UI should adapt well to different screen sizes (though Streamlit's native responsiveness might have limitations).
*   **Feedback:** Provide clear visual feedback for user actions (e.g., data saved, errors).
*   **Consistency:** Consistent layout, terminology, and interaction patterns across all modules.

## 8. Reporting and Visualization

Streamlit's built-in capabilities and integration with Python data science libraries (e.g., Pandas, Matplotlib, Plotly) will be utilized to:
*   Display tabular data from database queries.
*   Create interactive charts and graphs (e.g., bar charts for cost breakdown, line charts for trend analysis).
*   Allow users to filter and sort report data dynamically.

## 9. Acceptance Criteria

*   Users can successfully navigate between implemented modules via the UI.
*   Data entry forms are functional and correctly persist data to `PEARLqlite_DB` via the `DataAccess` layer.
*   All data displayed in the UI is correctly filtered by the active `PEARL_ID`.
*   Key reports and visualizations are accessible and display accurate data.
*   The UI is responsive and provides clear feedback to user actions.
*   The Streamlit application can be launched and accessed successfully.

## 10. Post-Change Verification

After any changes to the codebase, ensure the following steps are performed:
*   Run `ruff check App/src` to ensure that all the changes made haven't introduced any new linting or type errors.
*   Restart `streamlit run yourscript.py` to apply changes and verify functionality.
