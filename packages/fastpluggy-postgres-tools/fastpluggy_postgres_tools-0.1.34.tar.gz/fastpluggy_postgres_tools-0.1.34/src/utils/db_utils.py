"""
Database utility functions for postgres_tools.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def execute_query(db: Session, query_text, params=None):
    """
    Execute a query and return the result as a list of dictionaries.
    This function handles the connection properly to avoid "Connection is closed" errors.
    
    Args:
        db (Session): The SQLAlchemy session
        query_text: The SQL query text (can be a string or sqlalchemy.text)
        params (dict, optional): Parameters for the query
        
    Returns:
        list: List of dictionaries containing the query results
    """
    # Convert string query to text object if needed
    if isinstance(query_text, str):
        query_text = text(query_text)
        
    # Use params dict if provided, otherwise empty dict
    params = params or {}
    
    # Execute the query without using 'with' context manager
    # This prevents the connection from being closed prematurely
    conn = db.connection()
    try:
        result = conn.execute(query_text, params).mappings()
        return [dict(row) for row in result]
    except Exception as e:
        # Log the error but don't close the connection
        print(f"Error executing query: {e}")
        raise
    # Don't close the connection here - let SQLAlchemy manage it


def execute_query_first(db: Session, query_text, params=None):
    """
    Execute a query and return the first result as a dictionary.
    This function handles the connection properly to avoid "Connection is closed" errors.
    
    Args:
        db (Session): The SQLAlchemy session
        query_text: The SQL query text (can be a string or sqlalchemy.text)
        params (dict, optional): Parameters for the query
        
    Returns:
        dict: Dictionary containing the first row of the query result, or None if no results
    """
    # Convert string query to text object if needed
    if isinstance(query_text, str):
        query_text = text(query_text)
        
    # Use params dict if provided, otherwise empty dict
    params = params or {}
    
    # Execute the query without using 'with' context manager
    conn = db.connection()
    try:
        result = conn.execute(query_text, params).mappings().first()
        return dict(result) if result else None
    except Exception as e:
        # Log the error but don't close the connection
        print(f"Error executing query: {e}")
        raise
    # Don't close the connection here - let SQLAlchemy manage it


def execute_command(db: Session, command_text, params=None):
    """
    Execute a command (INSERT, UPDATE, DELETE, etc.) and commit the transaction.
    This function handles the connection properly to avoid "Connection is closed" errors.
    
    Args:
        db (Session): The SQLAlchemy session
        command_text: The SQL command text (can be a string or sqlalchemy.text)
        params (dict, optional): Parameters for the command
        
    Returns:
        None
    """
    # Convert string command to text object if needed
    if isinstance(command_text, str):
        command_text = text(command_text)
        
    # Use params dict if provided, otherwise empty dict
    params = params or {}
    
    # Execute the command without using 'with' context manager
    conn = db.connection()
    try:
        db.execute(command_text, params)
        db.commit()
    except Exception as e:
        # Log the error but don't close the connection
        print(f"Error executing command: {e}")
        db.rollback()
        raise
    # Don't close the connection here - let SQLAlchemy manage it