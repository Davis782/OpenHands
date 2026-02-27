import streamlit as st
import pandas as pd
from App.src.core.seedtools.seedtools import seed_to_pearl_id

def render_csv_import_page():
    """
    Renders the CSV import page in the Streamlit application.
    """
    st.title("CSV Import for PEARL IDs")
    st.write("Upload a CSV file to generate and manage PEARL IDs for your data.")

    # File uploader widget
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        try:
            df = pd.read_csv(uploaded_file)
            st.write("### Preview of Uploaded Data:")
            st.dataframe(df.head())
            st.session_state.uploaded_csv_df = df # Store DataFrame in session state

            # Column selection for PEARL ID seed
            st.write("### Configure PEARL ID Generation")
            st.info("Select the columns from your CSV file that will be used to generate the PEARL ID seed. The order of selection matters.")

            available_columns = df.columns.tolist()
            selected_columns = st.multiselect(
                "Select columns for PEARL ID seed",
                options=available_columns,
                help="Combine values from these columns to create a unique seed for each PEARL ID."
            )

            if selected_columns:
                st.write(f"Selected columns for seed: {', '.join(selected_columns)}")
                if st.button("Generate and Store PEARL IDs"):
                    if 'pearl_client' not in st.session_state:
                        st.error("PearlClient not initialized. Please unlock a vault first.")
                        return

                    pearl_client = st.session_state.pearl_client
                    imported_count = 0
                    progress_bar = st.progress(0)
                    total_rows = len(df)

                    for index, row in df.iterrows():
                        # Concatenate selected column values to form the seed
                        seed_parts = [str(row[col]) for col in selected_columns]
                        seed = "_".join(seed_parts)

                        # Generate PEARL ID
                        generated_pearl_id = seed_to_pearl_id(seed)

                        # Store PEARL ID in the database
                        try:
                            pearl_client.create_pearl_id(
                                entity_type="csv_imported_item", # Or a more specific type if available
                                attributes={"original_csv_row": row.to_dict(), "seed_used": seed},
                                pearl_id=generated_pearl_id,
                                seed=seed
                            )
                            imported_count += 1
                        except Exception as e:
                            st.error(f"Error storing PEARL ID for row {index}: {e}")

                        progress_bar.progress((index + 1) / total_rows)

                    st.success(f"Successfully generated and stored {imported_count} PEARL IDs.")
                    if imported_count > 0:
                        # Clear the cache for PEARL IDs to ensure the main app UI refreshes
                        from App.src.ui.streamlit_cache_utils import get_all_distinct_pearl_ids_from_all_tables_cached
                        get_all_distinct_pearl_ids_from_all_tables_cached.clear()
                        st.rerun()
            else:
                st.warning("Please select at least one column to generate PEARL IDs.")

            
            available_columns = df.columns.tolist()
            selected_seed_columns = st.multiselect(
                "Select columns for PEARL ID seed (order matters for determinism):",
                options=available_columns,
                default=available_columns[0] if available_columns else [] # Pre-select first column if available
            )

            if selected_seed_columns:
                st.session_state.selected_seed_columns = selected_seed_columns
                st.success(f"Selected columns for PEARL ID seed: {', '.join(selected_seed_columns)}")

                if st.button("Import Data and Generate PEARL IDs"):
                    if not st.session_state.get("vault_unlocked", False):
                        st.error("Please unlock the vault before importing data and generating PEARL IDs.")
                    elif not hasattr(st.session_state, "pearl_client") or st.session_state.pearl_client is None:
                        st.error("PearlClient is not initialized. Please ensure the database is selected and vault is unlocked.")
                    else:
                        progress_bar = st.progress(0)
                        total_rows = len(df)
                        imported_count = 0
                        failed_count = 0
                        generated_pearl_ids = []
                        failed_rows_details = []

                        for index, row in df.iterrows():
                            try:
                                # Construct the seed string
                                seed_parts = [str(row[col]) for col in selected_seed_columns]
                                seed = ":".join(seed_parts)

                                # Generate PEARL ID
                                pearl_id = seed_to_pearl_id(seed)

                                # Store PEARL ID using PearlClient
                                # For now, entity_type is generic, and attributes are the whole row
                                st.session_state.pearl_client.create_pearl_id(
                                    entity_type="csv_imported_item",
                                    attributes=row.to_dict(),
                                    pearl_id=pearl_id,
                                    seed=seed
                                )
                                generated_pearl_ids.append(pearl_id)
                                imported_count += 1
                            except Exception as e:
                                failed_count += 1
                                failed_rows_details.append(f"Row {index} (ID: {row.get(selected_seed_columns[0], 'N/A')}): {e}")
                            progress_bar.progress((index + 1) / total_rows)
                        
                        progress_bar.empty()
                        
                        if imported_count > 0:
                            st.success(f"Import complete! Successfully imported {imported_count} out of {total_rows} rows.")
                            if generated_pearl_ids:
                                st.write("### Generated PEARL IDs (first 10):")
                                for pid in generated_pearl_ids[:10]:
                                    st.write(f"- {pid}")
                        else:
                            st.warning(f"No rows were successfully imported. Total rows processed: {total_rows}.")

                        if failed_count > 0:
                            st.error(f"Failed to import {failed_count} out of {total_rows} rows.")
                            with st.expander("View Failed Rows Details"):
                                for detail in failed_rows_details:
                                    st.write(detail)

            else:
                st.warning("Please select at least one column to generate PEARL IDs.")
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
