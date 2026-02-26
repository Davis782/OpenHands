# Database Protocol Product Requirements Document (PRD)

## 1. Introduction

This document outlines the requirements for implementing a standardized database protocol within the PEARL AI system. The primary goal is to establish a clear and secure method for interacting with the underlying database, ensuring data integrity, isolation, and efficient management, particularly in the context of multiple PEARL Identities.

## 2. Goal and Scope

The goal of this protocol is to:
*   Define a consistent approach for all database operations (CRUD - Create, Read, Update, Delete).
*   Ensure data isolation and security by leveraging the `PEARL_ID` for all data access.
*   Improve maintainability and reusability of SQL statements.
*   Provide a clear separation of concerns between application logic and database interactions.

The scope of this PRD covers:
*   The integration of `PEARL_ID` into the database schema and all relevant queries.
*   The organization and management of SQL statements in dedicated files.
*   The introduction of a Data Access Layer (DAL) to abstract database interactions.
*   Guidelines for parameterized queries to prevent SQL injection.

## 3. Key Concepts

### 3.1. PEARL_ID as a Data Partitioning Key
The `PEARL_ID` will serve as a fundamental identifier for data ownership and isolation within the database. Every record in relevant tables will be associated with a specific `PEARL_ID`, ensuring that data belonging to one PEARL Identity is logically separated from others.

### 3.2. SQL Statement File Organization
All SQL `SELECT`, `INSERT`, `UPDATE`, and `DELETE` statements will be stored in external `.sql` files, separate from the application's Python code. These files will be organized logically (e.g., by module or entity).

### 3.3. Parameterized Queries
All database interactions will utilize parameterized queries (prepared statements) to prevent SQL injection vulnerabilities and ensure proper handling of data types.

### 3.4. Foreign Keys
Foreign key constraints will be used to maintain referential integrity between related tables, ensuring consistency across the database schema.

## 4. Architectural Changes

### 4.1. Introduction of a Data Access Layer (DAL)
A new `DataAccess` layer will be introduced to encapsulate all database interaction logic. This layer will be responsible for:
*   Loading SQL statements from `.sql` files.
*   Managing database connections.
*   Executing parameterized queries.
*   Handling `PEARL_ID` context for all operations.

### 4.2. Application Context for PEARL_ID
Upon successful vault unlocking, the active `PEARL_ID` will be set in the application's context (e.g., within the `DataAccess` instance). All subsequent database operations will implicitly use this `PEARL_ID` for filtering and insertion.

## 5. Database Schema Impact

### 5.1. PEARL_ID Column
All primary data tables (e.g., `Jobs`, `Employees`, `Invoices`, `Contacts`, `InventoryItems`) will include a `PEARL_ID` column.
*   **Type:** TEXT (or appropriate UUID/string type for PEARL_ID).
*   **Constraint:** NOT NULL.
*   **Index:** An index should be created on the `PEARL_ID` column for efficient lookups.

### 5.2. Foreign Key Relationships
Where applicable, `PEARL_ID` will also be used as part of composite primary keys or foreign keys to enforce relationships between tables while maintaining `PEARL_ID` isolation.

## 6. SQL Statement Management

### 6.1. Directory Structure
A dedicated directory (e.g., `App/sql/`) will house all `.sql` files. Subdirectories can be used for further organization (e.g., `App/sql/jobs/`, `App/sql/accounting/`) and menu driven UI is able to eloquently utilize the proper directory for queries.

### 6.2. Naming Conventions
SQL files and individual queries within them should follow a clear, descriptive naming convention (e.g., `jobs_get_all.sql`, `jobs_insert.sql`).

### 6.3. Query Design
*   All `SELECT` queries for user-specific data must include `WHERE PEARL_ID = ?`.
*   All `INSERT` statements for user-specific data must include `PEARL_ID` as a column.
*   All `UPDATE` and `DELETE` statements for user-specific data must include `WHERE PEARL_ID = ?` to prevent cross-identity modifications.

if user has not assigned a PEARL_ID, either it is not needed or they need to update one for further usage and made available a way to do so in the protocal.

### 6.4. SQL Statement Evolution and Maintenance

This section outlines the process for managing the lifecycle of SQL statements within the `.sql` files:

*   **Development and Testing:** When developing new features or reports, SQL queries and joins should first be drafted and thoroughly tested using a database client or a dedicated testing environment.
*   **Validation:** Once a query or join is confirmed to be working correctly and efficiently, it can be integrated into the appropriate `.sql` file.
*   **Integration:** New or modified SQL statements should be added to their respective `.sql` files following the established naming conventions and directory structure.
*   **Version Control:** All changes to `.sql` files must be committed to version control (e.g., Git) alongside the corresponding application code changes. This ensures traceability and allows for easy rollback if issues arise.
*   **Documentation:** For complex queries or joins, consider adding comments within the `.sql` file to explain their purpose, parameters, and any specific assumptions.

## 7. Security and Data Isolation

*   **Enforced Isolation:** The `PEARL_ID` in every query ensures that a user can only access data associated with their unlocked PEARL Identity.
*   **SQL Injection Prevention:** Strict adherence to parameterized queries will mitigate SQL injection risks.
*   **Data Integrity:** Foreign key constraints will help maintain the consistency and validity of relationships within the database.

## 8. Reporting Considerations

Reports will be generated by executing `SELECT` queries that incorporate the active `PEARL_ID`. The DAL will facilitate passing the `PEARL_ID` to reporting queries, ensuring that reports only reflect data relevant to the current PEARL Identity.

## 9. UI Considerations for Structured Data Input

To ensure data integrity and efficient utilization of structured data (e.g., `user:JohnDoe,tenant:acme,company:hardware`), the User Interface (UI) must be designed to guide users in providing input that adheres to predefined formats. This "idiot-proof" approach is critical for the accuracy of database operations, clustering, vector embeddings, and search functionalities.

Key considerations for UI design include:
*   **Guided Input:** Implement UI elements (e.g., forms, wizards) that lead users through the process of constructing structured data, rather than allowing free-form text entry where structure is critical.
*   **Validation:** Provide real-time validation and clear feedback to users when input deviates from the expected structure or format.
*   **Templates/Dropdowns:** Where possible, offer predefined templates, dropdowns, or auto-completion features to simplify input and reduce errors for common structured data patterns.
*   **Clear Examples:** Display clear examples of the expected data format within the UI to educate users.
*   **Error Prevention:** Design the UI to prevent common structural errors before submission, ensuring that only correctly formatted data can be saved.

### 9.1. PEARL ID and Semantic Analysis (Clustering, Vector Embedding)

It is crucial to understand the distinction between a PEARL ID and its underlying seed string, especially when considering advanced analytical capabilities like clustering and vector embedding.

**PEARL ID Generation (Hashing):**
The `seedtools.seed_to_pearl_id` function uses a cryptographic hashing algorithm (specifically, Argon2, as implemented in `seedtools.py`). A hash function takes an input (your seed string) and produces a fixed-size, seemingly random output (the PEARL ID).
*   **Key Characteristic:** Hash functions are designed to be extremely sensitive to input changes. Even a single character difference in your seed string will result in a completely different PEARL ID.
*   **Implication for Structure:** This means that the PEARL ID itself (e.g., `pearl_bb9cf3e2ed43`) **does not inherently preserve the internal hierarchical structure or semantic meaning** of your original seed string. The PEARL ID is a unique identifier derived from the *entire* seed string, not a semantic representation of its parts. You cannot "reverse-engineer" the hierarchy from the PEARL ID alone.

**Clustering and Vector Embedding:**
If the goal is to cluster entities based on their `industry`, `discipline`, `task`, or `user`, or to generate vector embeddings that capture these semantic relationships, you would need to work with the **original seed string or its parsed components**, not directly with the PEARL ID.

To achieve this, the following logic is typically applied:
1.  **Store the Original Seed String:** Ensure that the full seed string (e.g., `"industry:health,discipline:heart,task:diagnosis,user:jane_smith"`) is stored in the database alongside the generated `pearl_id`. The current implementation already facilitates this when an entity is created with a seed.
2.  **Parse the Seed String:** When performing clustering or generating embeddings, the seed string needs to be parsed into its constituent parts (e.g., extract "health" for industry, "heart" for discipline, etc.). A utility function, such as `parse_hierarchical_seed` (located in `App/src/utils/seed_parser.py`), can be used to split the string by delimiters (e.g., `,` and `:`) to extract key-value pairs.
3.  **Generate Semantic Embeddings:** A separate process is then applied to these parsed components or the original seed string to generate vector embeddings. This might involve:
    *   **Categorical Embeddings:** Assigning numerical vectors to each category (e.g., "health", "heart", "diagnosis").
    *   **Natural Language Processing (NLP) Embeddings:** Utilizing pre-trained language models (e.g., BERT, Word2Vec) to generate embeddings for the entire seed string or its components, thereby capturing semantic similarity.
    *   **Custom Logic:** Defining specific rules for converting hierarchical components into a vector space that aligns with desired clustering logic.

**Conclusion and Recommendation:**
*   **Utilize your desired hierarchical seed string format.** This format is flexible and fully compatible with PEARL ID generation.
*   **Understand the PEARL ID's role:** It serves as a unique, deterministic identifier, not a semantic representation of the seed's internal structure.
*   **For semantic analysis (clustering, embedding):** Implement additional logic to:
    *   **Parse** structured seed strings into their individual hierarchical components.
    *   **Store** these components as structured metadata (e.g., a JSON column or separate columns) in the database alongside the `pearl_id`.
    *   **Apply appropriate vector embedding techniques** to this structured metadata to enable the clustering and semantic search capabilities.

This comprehensive approach ensures both the strong, unique identification provided by PEARL IDs and the rich, structured metadata necessary for advanced analytical capabilities.

## 10. Acceptance Criteria

*   All database operations (CRUD) for core entities are routed through the `DataAccess` layer.
*   All `SELECT`, `INSERT`, `UPDATE`, and `DELETE` queries for user-specific data correctly utilize the `PEARL_ID` for filtering/scoping.
*   SQL statements are stored in external `.sql` files within the `App/sql/` directory.
*   Parameterized queries are used for all dynamic values in SQL statements.
*   The application successfully retrieves and stores data for multiple distinct `PEARL_ID`s without cross-contamination.
*   Foreign key constraints are implemented where appropriate to maintain referential integrity.
*   The system can generate reports that are correctly filtered by the active `PEARL_ID`.

## 11. Post-Change Verification

After any changes to the codebase, ensure the following steps are performed:
*   Run `ruff check App/src` to ensure that all the changes made haven't introduced any new linting or type errors.
*   Restart `streamlit run yourscript.py` to apply changes and verify functionality.
