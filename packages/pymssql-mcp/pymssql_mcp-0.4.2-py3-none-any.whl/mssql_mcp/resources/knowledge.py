"""Knowledge resource for mssql-mcp.

Exposes saved database knowledge to Claude at the start of conversations.
"""

from ..app import mcp
from ..utils.knowledge import get_knowledge_store


@mcp.resource("mssql://knowledge")
def get_database_knowledge() -> str:
    """Previously learned information about this SQL Server database.

    This resource contains all saved knowledge about the database including:
    - Table descriptions and purposes
    - Column definitions and meanings
    - Working query patterns
    - Data format notes
    - Relationships between tables
    - Stored procedure documentation

    This knowledge was saved from previous conversations to help
    Claude work more efficiently with this database.
    """
    store = get_knowledge_store()
    return store.get_all()
