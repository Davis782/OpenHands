# Product Requirements Document: Master Key and Hierarchical PEARL_ID Access

## 1. Introduction

This document outlines the requirements for implementing a "Master PEARL ID Seed" and "Sub-Master Key" system within PEARL AI. This feature aims to enhance both user convenience for vault access and provide robust hierarchical access control for `PEARL_ID` groupings, addressing the needs of individual users and organizational data management.

## 2. Goals

*   **Improve Vault Access Convenience:** Allow users to unlock their vault with a single "Master PEARL ID Seed" instead of multiple passwords.
*   **Enable Hierarchical `PEARL_ID` Grouping:** Provide a mechanism to logically group related `PEARL_ID`s.
*   **Implement Granular Access Control:** Allow for the creation of "Sub-Master Keys" that grant access only to specific `PEARL_ID` groupings.
*   **Ensure Security and Non-Reversibility:** Maintain high security standards, ensuring that "Sub-Master Keys" cannot expose higher-level access or other groups.
*   **Provide Administrative Control:** Grant the global "Master Key" holder comprehensive management capabilities over groupings and "Sub-Master Keys."

## 3. User Stories

### 3.1. Vault Unlocking Master Key

*   As a PEARL AI user, I want to define a "Master PEARL ID Seed" that, when entered, automatically provides my Vault Door, Identity, and Metadata passwords, so I don't have to type them repeatedly.
*   As a PEARL AI user, I want to manage my "Master PEARL ID Seed" (which contains my vault passwords) externally, so the system does not store my sensitive credentials.
*   As a PEARL AI user, if I change my vault passwords, I want to be able to update my external "Master PEARL ID Seed" accordingly.

### 3.2. Hierarchical `PEARL_ID` Grouping and Access Control

*   As an administrator (global "Master Key" holder), I want to create logical groupings of `PEARL_ID`s (e.g., "Project Alpha," "Sales Department") to organize data.
*   As an administrator, I want to generate "Sub-Master Keys" for specific `PEARL_ID` groupings, so I can delegate access to subsets of data.
*   As an administrator, I want to manage (create, read, update, delete) all `PEARL_ID` groupings and "Sub-Master Keys," including the ability to deprecate them.
*   As a team member, I want to use a "Sub-Master Key" to access only the `PEARL_ID`s relevant to my assigned group (e.g., "Project Alpha"), so I only see data pertinent to my work.
*   As a team member, I want to be prevented from accessing `PEARL_ID`s or data outside my assigned group when using a "Sub-Master Key," ensuring data segregation.
*   As a team member, I want to be unable to reverse-engineer a "Sub-Master Key" to gain access to the global "Master Key" or other groupings.

## 4. High-Level Requirements

### 4.1. Vault Unlocking Master Key

*   **REQ-VK-1:** The system SHALL provide a mechanism for users to input a "Master PEARL ID Seed" for vault unlocking.
*   **REQ-VK-2:** The system SHALL interpret the "Master PEARL ID Seed" to derive the Vault Door, Identity, and Metadata passwords.
*   **REQ-VK-3:** The system SHALL use the derived passwords to attempt to unlock the vault.
*   **REQ-VK-4:** The system SHALL NOT store the "Master PEARL ID Seed" or its derived passwords internally. The "Master PEARL ID Seed" is expected to be managed externally by the user.
*   **REQ-VK-5:** The interpretation logic for deriving passwords from the "Master PEARL ID Seed" seed string SHALL be robust and clearly documented for users.

### 4.2. `PEARL_ID` Grouping and Access Control

*   **REQ-GC-1:** The system SHALL allow the global "Master Key" holder to define and manage (CRUD) `PEARL_ID` groupings.
*   **REQ-GC-2:** Each `PEARL_ID` grouping SHALL be associated with a unique "Sub-Master Key."
*   **REQ-GC-3:** The system SHALL allow the global "Master Key" holder to generate and manage (CRUD) "Sub-Master Keys."
*   **REQ-GC-4:** When a "Sub-Master Key" is active, the system SHALL restrict all data access operations (e.g., queries, reports, UI display) to *only* the `PEARL_ID`s belonging to that key's associated group.
*   **REQ-GC-5:** The global "Master Key" SHALL bypass all `PEARL_ID` grouping restrictions, granting access to all `PEARL_ID`s and their data.
*   **REQ-GC-6:** The global "Master Key" holder SHALL have CRUD privileges over all groupings and "Sub-Master Keys." This includes the ability to deprecate/revoke "Sub-Master Keys."
*   **REQ-GC-7:** "Sub-Master Keys" SHALL NOT provide any mechanism to derive the global "Master Key" or access `PEARL_ID`s outside their assigned group.

## 5. Technical Considerations

### 5.1. Vault Unlocking Master Key

*   **Seed String Format:** Define a secure and parsable format for embedding multiple passwords within a `PEARL_ID`'s seed string (e.g., JSON, delimited string, or a custom encryption scheme).
*   **Encryption/Obfuscation:** Consider if the passwords within the seed string should be further encrypted or obfuscated to prevent casual inspection.
*   **`seedtools` Integration:** Extend `seedtools` to include functions for parsing and potentially decrypting the seed string into individual vault passwords.
*   **UI Integration:** Add a dedicated input field for the "Master PEARL ID Seed" in the vault loading section.

### 5.2. `PEARL_ID` Grouping and Access Control

*   **Database Schema:** Introduce a new table (e.g., `pearl_id_groups`) to store:
    *   `group_id` (Primary Key)
    *   `group_name` (e.g., "Project Alpha")
    *   `sub_master_key` (Unique identifier for the group's access)
    *   A many-to-many relationship table linking `group_id` to `PEARL_ID`s.
*   **Access Context:** Implement a session-level context variable (similar to `st.session_state.pearl_id`) that stores the currently active `group_id` or a flag indicating global "Master Key" access.
*   **Query Modification Layer:** All data access functions (`DataAccess` methods) will need to be modified to dynamically include `WHERE pearl_id IN (...)` clauses based on the active access context.
*   **UI for Group Management:** Develop a UI for administrators to:
    *   Create new groups and assign `PEARL_ID`s to them.
    *   Generate and display "Sub-Master Keys."
    *   Modify existing groups (add/remove `PEARL_ID`s).
    *   Delete groups and deprecate their associated "Sub-Master Keys."
*   **Security of Sub-Master Keys:** Ensure "Sub-Master Keys" are securely generated (e.g., UUIDs or cryptographically strong random strings) and not easily guessable or reversible.

## 6. Future Considerations

*   **Time-Limited Access:** Implement an option for "Sub-Master Keys" to have an expiration date.
*   **Audit Logging:** Log all actions related to `PEARL_ID` grouping and "Sub-Master Key" management for compliance and security auditing.
*   **Role-Based Access Control (RBAC):** Extend the grouping concept to a more formal RBAC system, where roles are assigned permissions to specific groups.
*   **Integration with External Identity Providers:** Consider how these keys might integrate with external authentication systems.
