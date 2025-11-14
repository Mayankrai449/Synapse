"""
Synapse MCP Server - Fast & Minimalistic
Allows LLM platforms to save content to Synapse via MCP
"""

from fastmcp import FastMCP
import httpx
import json
from typing import Optional

# Initialize MCP server
mcp = FastMCP("Synapse Knowledge Base")

# Configuration
SYNAPSE_API = "http://localhost:8000"

@mcp.tool()
async def save_to_synapse(
    text: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> str:
    """
    Save content to Synapse knowledge base.

    Args:
        text: The main content to save (required)
        title: Title or heading for the content
        url: Source URL if content is from web
        tags: List of tags/keywords for categorization

    Returns:
        Success message with document ID
    """

    # Prepare metadata
    from datetime import datetime
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "timestamp_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "mcp",
    }

    if title:
        metadata["title"] = title
    if url:
        metadata["url"] = url
        # Extract domain from URL
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            metadata["domain"] = domain
        except:
            pass
    if tags:
        metadata["tags"] = tags

    # Prepare form data
    form_data = {
        "text": text,
        "metadata": json.dumps(metadata),
        "enable_chunking": "true",
        "image_urls": "[]"
    }

    # Send to Synapse /save endpoint
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SYNAPSE_API}/save",
                data=form_data
            )
            response.raise_for_status()

            result = response.json()
            doc_id = result.get("document_id", "unknown")
            status = result.get("message", "Success")

            return f"✓ Saved to Synapse!\nDocument ID: {doc_id}\nStatus: {status}"

        except httpx.HTTPError as e:
            return f"✗ Error saving to Synapse: {str(e)}"
        except Exception as e:
            return f"✗ Unexpected error: {str(e)}"


@mcp.tool()
async def save_conversation_to_synapse(
    conversation: str,
    topic: Optional[str] = None,
    participants: Optional[list[str]] = None
) -> str:
    """
    Save a conversation or chat history to Synapse.

    Args:
        conversation: The full conversation text
        topic: Topic or subject of the conversation
        participants: List of participants in the conversation

    Returns:
        Success message with document ID
    """

    from datetime import datetime
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "timestamp_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "mcp",
        "type": "conversation",
    }

    if topic:
        metadata["title"] = topic
    if participants:
        metadata["participants"] = participants

    # Format conversation with header
    formatted_text = ""
    if topic:
        formatted_text += f"# {topic}\n\n"
    if participants:
        formatted_text += f"Participants: {', '.join(participants)}\n\n"
    formatted_text += conversation

    # Prepare form data
    form_data = {
        "text": formatted_text,
        "metadata": json.dumps(metadata),
        "enable_chunking": "true",
        "image_urls": "[]"
    }

    # Send to Synapse
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SYNAPSE_API}/save",
                data=form_data
            )
            response.raise_for_status()

            result = response.json()
            doc_id = result.get("document_id", "unknown")

            return f"✓ Conversation saved to Synapse!\nDocument ID: {doc_id}\nTopic: {topic or 'None'}"

        except httpx.HTTPError as e:
            return f"✗ Error: {str(e)}"
        except Exception as e:
            return f"✗ Error: {str(e)}"


@mcp.tool()
async def save_notes_to_synapse(
    notes: str,
    category: Optional[str] = None,
    project: Optional[str] = None
) -> str:
    """
    Save notes, ideas, or thoughts to Synapse.

    Args:
        notes: The notes content
        category: Category (e.g., "work", "personal", "research")
        project: Associated project name

    Returns:
        Success message with document ID
    """

    from datetime import datetime
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "timestamp_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "mcp",
        "type": "notes",
    }

    if category:
        metadata["category"] = category
    if project:
        metadata["project"] = project
        metadata["title"] = f"{project} - Notes"

    form_data = {
        "text": notes,
        "metadata": json.dumps(metadata),
        "enable_chunking": "true",
        "image_urls": "[]"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SYNAPSE_API}/save",
                data=form_data
            )
            response.raise_for_status()

            result = response.json()
            doc_id = result.get("document_id", "unknown")

            return f"✓ Notes saved to Synapse!\nDocument ID: {doc_id}\nCategory: {category or 'None'}"

        except Exception as e:
            return f"✗ Error: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
