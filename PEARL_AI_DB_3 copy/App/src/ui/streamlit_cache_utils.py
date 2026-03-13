import streamlit as st
import logging
from App.src.core.database import data_access
from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient
from App.src.agent_pearl import agent_pearl
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

@st.cache_resource(ttl=3600)
def get_pearl_client_cached(db_path: str) -> PearlClient:
    """
    Caches and returns a PearlClient instance.
    This ensures the PearlClient is a singleton across Streamlit reruns.
    """
    logger.debug(f"get_pearl_client_cached received db_path: {db_path}")
    return PearlClient(default_db=db_path)

@st.cache_resource(ttl=3600)
def get_data_access_cached(db_path: str, sql_dir: str) -> data_access.DataAccess:
    """
    Caches and returns a DataAccess instance.
    This ensures the DataAccess object is a singleton across Streamlit reruns,
    and uses the cached PearlClient.
    """
    pearl_client = get_pearl_client_cached(db_path)
    return data_access.DataAccess(db_path=db_path, sql_dir=sql_dir, pearl_client=pearl_client)

@st.cache_data(ttl=300)
def get_all_distinct_pearl_ids_from_all_tables_cached(db_path: str, sql_dir: str) -> list[str]:
    """
    Retrieves all distinct PEARL IDs from all tables, cached for performance.
    Uses a cached DataAccess instance.
    """
    dal = get_data_access_cached(db_path, sql_dir)
    return dal.get_all_distinct_pearl_ids_from_all_tables()

@st.cache_data(ttl=300)
def get_all_table_names_cached(db_path: str, sql_dir: str) -> list[str]:
    """
    Retrieves all table names in the database, cached for performance.
    Uses a cached DataAccess instance.
    """
    dal = get_data_access_cached(db_path, sql_dir)
    return dal.get_all_table_names()

@st.cache_data(ttl=300)
def get_all_pearl_id_groups_cached(db_path: str, sql_dir: str) -> list[dict]:
    """
    Retrieves all PEARL ID groups, cached for performance.
    Uses a cached DataAccess instance.
    """
    dal = get_data_access_cached(db_path, sql_dir)
    return dal.get_all_pearl_id_groups()

@st.cache_data(ttl=300)
def get_pearl_ids_in_group_cached(db_path: str, sql_dir: str, group_id: str) -> list[dict]:
    """
    Retrieves PEARL IDs belonging to a specific group, cached for performance.
    Uses a cached DataAccess instance.
    """
    dal = get_data_access_cached(db_path, sql_dir)
    return dal.get_pearl_ids_in_group(group_id)

@st.cache_data(ttl=300)
def get_all_pearl_ids_in_active_group_cached(db_path: str, sql_dir: str) -> list[str]:
    """
    Retrieves all PEARL IDs in the currently active group, cached for performance.
    Uses a cached DataAccess instance.
    """
    dal = get_data_access_cached(db_path, sql_dir)
    return dal.get_all_pearl_ids_in_active_group()

@st.cache_resource(ttl=3600)
def get_agent_pearl_cached(db_name: str, vault_path: str) -> agent_pearl.AgentPearl:
    """
    Caches and returns an AgentPearl instance.
    """
    # Inside this cached function, get the PearlClient
    pearl_client = get_pearl_client_cached(db_name) # Use the cached PearlClient
    return agent_pearl.AgentPearl(db_name=db_name, vault_path=vault_path, pearl_client=pearl_client)
