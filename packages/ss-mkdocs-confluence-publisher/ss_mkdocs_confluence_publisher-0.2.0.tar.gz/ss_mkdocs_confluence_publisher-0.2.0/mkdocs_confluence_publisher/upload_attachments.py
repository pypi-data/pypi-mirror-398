import os
import logging
from typing import List

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.upload_attachments')

def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes."""
    return os.path.getsize(file_path)

def upload_attachments(page_id: int, attachments: List[str], confluence, space_key: str):
    logger.debug(f"Starting attachment upload for page_id: {page_id}")

    # Get existing attachments for the page
    existing_attachments_response = confluence.get_attachments_from_content(page_id)
    existing_attachments = existing_attachments_response.get('results', [])
    logger.debug(f"Found {len(existing_attachments)} existing attachments")

    # Track which attachments we've processed
    processed_attachments = set()

    for attachment in attachments:
        file_name = os.path.basename(attachment)
        local_file_size = get_file_size(attachment)

        logger.debug(f"Processing attachment: {file_name}")

        # Check if the file already exists as an attachment
        existing_attachment = next((att for att in existing_attachments if att['title'] == file_name), None)

        if existing_attachment and existing_attachment['extensions'].get('fileSize') == local_file_size:
            logger.debug(f"Attachment unchanged, skipping: {file_name}")
        else:
            action = "Updating" if existing_attachment else "Uploading"
            logger.debug(f"{action} attachment: {file_name}")
            confluence.attach_file(
                attachment,
                page_id=page_id,
                space=space_key,
                comment=f'{action} by MkDocs Confluence Publisher'
            )

        processed_attachments.add(file_name)

    # Clean up unknown attachments
    for existing_attachment in existing_attachments:
        if existing_attachment['title'] not in processed_attachments:
            logger.debug(f"Removing unknown attachment: {existing_attachment['title']}")
            confluence.delete_attachment(page_id, existing_attachment['id'])

    logger.debug("Finished processing attachments")
