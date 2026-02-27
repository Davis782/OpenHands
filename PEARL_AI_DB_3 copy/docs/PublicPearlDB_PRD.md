# Product Requirements Document: Public PEARL DB for AI & Blockchain

## 1. Introduction

This document outlines the requirements for evolving the PEARL AI system's data management from a local, embedded `PEARLqlite` instance to a public, networked, and URL-accessible database service. This service, hereafter referred to as "Public PEARL DB," will be designed to support multi-user access, integrate with AI and Machine Learning workflows, and provide verifiable data integrity through blockchain principles.

The primary goal is to enable users to securely create, manage, and access their PEARL-identified data via a public API, fostering a decentralized and verifiable data ecosystem for AI and blockchain applications.

## 2. Goals and Vision

*   **Enable Public Access:** Provide a secure, URL-accessible endpoint for users to interact with their PEARL-identified data.
*   **Multi-User Support:** Facilitate concurrent access and data management for numerous independent users, each operating under their own PEARL Identities.
*   **AI Integration:** Offer features and data structures optimized for AI/ML model training, inference, and data analysis, including semantic search and vector embeddings.
*   **Blockchain Verifiability:** Incorporate mechanisms to leverage blockchain for data integrity, provenance, and potentially decentralized identity management.
*   **Scalability & Reliability:** Design for high availability and the ability to scale with increasing user demand and data volume.
*   **Developer-Friendly:** Provide clear APIs, documentation, and client libraries to facilitate integration by third-party applications.

## 3. Key Features

### 3.1. PEARL ID Management & Isolation
*   **Secure PEARL ID Generation:** Users can securely generate and manage their PEARL IDs.
*   **Row-Level Security (RLS):** Data belonging to one PEARL ID is strictly isolated from others at the database level.
*   **Multi-Tenancy:** Support for multiple independent users, each managing their own set of PEARL-identified data.

### 3.2. Public API Access
*   **RESTful API:** A well-documented, versioned RESTful API for all CRUD operations on PEARL-identified entities.
*   **Realtime Subscriptions:** Ability to subscribe to data changes for real-time application development.
*   **Querying & Filtering:** Advanced querying capabilities, including filtering by PEARL ID, entity type, and metadata.

### 3.3. AI & ML Data Support
*   **Structured Metadata Storage:** Support for storing rich, structured metadata (e.g., JSONB in PostgreSQL) alongside PEARL-identified entities.
*   **Semantic Search & Vector Embeddings:** Integration with vector databases or PostgreSQL extensions (e.g., `pgvector`) to enable semantic search and similarity queries on data.
*   **Data Export/Import:** Tools for efficient bulk export and import of data for AI/ML workflows.

### 3.4. Blockchain Integration
*   **Data Immutability & Provenance:** Mechanisms to hash data or metadata and anchor these hashes on a public blockchain for verifiable immutability and provenance.
*   **Decentralized Identity (DID) Integration (Future):** Potential to integrate with DID systems for enhanced user authentication and data ownership verification.
*   **Smart Contract Interaction (Future):** Explore interaction with smart contracts for automated data governance or conditional access.

### 3.5. Security & Compliance
*   **Robust Authentication:** Industry-standard authentication mechanisms (e.g., OAuth2, API Keys, JWTs).
*   **Authorization (RBAC):** Role-Based Access Control to manage user permissions.
*   **Data Encryption:** Encryption of data at rest and in transit.
*   **Auditing & Logging:** Comprehensive logging of all API access and data modifications.

## 4. Architectural Considerations

### 4.1. Core Database Technology
*   **Recommendation:** PostgreSQL (e.g., via Supabase, AWS RDS, Google Cloud SQL).
    *   **Rationale:** Provides robust RLS, JSONB support, extensibility (e.g., `pgvector`), high concurrency, and strong data integrity. SQLite is unsuitable for direct public, networked access.

### 4.2. Backend-as-a-Service (BaaS) Platform
*   **Recommendation:** Supabase (or similar platforms like Firebase, AWS Amplify).
    *   **Rationale:** Accelerates development by providing managed PostgreSQL, auto-generated APIs (PostgREST), authentication, and real-time capabilities out-of-the-box. Reduces operational overhead significantly.

### 4.3. API Layer
*   **Approach:** Leverage BaaS auto-generated APIs (e.g., Supabase's PostgREST) for standard CRUD operations.
*   **Custom Logic:** Implement custom serverless functions (e.g., Supabase Edge Functions, AWS Lambda) for complex business logic, AI model inference, or blockchain interactions that cannot be handled directly by the auto-generated API or RLS.

### 4.4. Authentication & Authorization
*   **Authentication:** Utilize BaaS authentication services (e.g., Supabase Auth) for user management and token issuance.
*   **Authorization:** Implement PostgreSQL Row-Level Security (RLS) policies based on authenticated user IDs and their associated PEARL IDs. Supplement with API-level authorization in custom functions where needed.

### 4.5. AI/ML Infrastructure
*   **Vector Database/Embeddings:** Integrate `pgvector` extension within PostgreSQL for storing and querying vector embeddings.
*   **ML Model Hosting:** Utilize cloud ML platforms (e.g., AWS SageMaker, Google AI Platform) for hosting and serving AI models that interact with the Public PEARL DB.

### 4.6. Blockchain Integration Layer
*   **Blockchain Client/SDK:** Develop or integrate a service that interacts with chosen blockchain networks (e.g., Ethereum, Polygon, Solana) to submit transactions for data hashing/anchoring.
*   **Off-Chain Data Storage:** The Public PEARL DB remains the primary storage for detailed data; only cryptographic proofs or minimal metadata are stored on-chain.

## 5. Data Model Enhancements

*   **`pearls` Table:** Continue to store `pearl_id`, `seed_string`, `created_at`, etc.
*   **Entity Tables:** All entity tables (e.g., `jobs`, `contacts`, `tasks`) will include a `pearl_id` foreign key and potentially a `metadata` column (JSONB type in PostgreSQL) for flexible, structured data.
*   **`blockchain_proofs` Table (New):** To store references to on-chain transactions (e.g., `transaction_hash`, `block_number`, `data_hash`, `pearl_id`).

## 6. User Experience (UX) Considerations

*   **Developer Portal:** Provide a comprehensive developer portal with API documentation, tutorials, and client SDKs.
*   **Dashboard:** A web-based dashboard for users to manage their PEARL IDs, view data, and monitor usage.
*   **Client Libraries:** Offer client libraries for popular programming languages (Python, JavaScript, etc.) to simplify interaction with the Public PEARL DB API.

## 7. Acceptance Criteria

*   Users can register, log in, and securely manage their PEARL Identities.
*   Authenticated users can perform CRUD operations on their PEARL-identified data via a public API.
*   Data for different PEARL IDs is strictly isolated and cannot be accessed by unauthorized users.
*   The system can store and retrieve structured metadata for AI/ML applications.
*   Data integrity can be cryptographically verified via blockchain proofs.
*   The service demonstrates high availability and responsiveness under load.

## 8. Future Considerations

*   Decentralized Identity (DID) integration.
*   Support for multiple blockchain networks.
*   Advanced AI/ML features (e.g., built-in model serving).
*   Federated queries across multiple PEARL DB instances.
