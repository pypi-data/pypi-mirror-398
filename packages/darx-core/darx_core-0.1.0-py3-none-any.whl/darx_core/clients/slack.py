"""
Slack API client utilities with proper error handling

This module provides Slack posting and file upload functionality that can be
used across all DARX services.
"""
import os
import logging
from typing import Dict, List, Optional, Callable
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Module-level logger
logger = logging.getLogger(__name__)

# Slack client (singleton pattern)
_slack_client: Optional[WebClient] = None


def get_slack_client() -> Optional[WebClient]:
    """
    Get or create Slack client (singleton).

    Returns:
        WebClient: Slack client instance, or None if token missing

    Raises:
        Exception: If client initialization fails
    """
    global _slack_client

    if _slack_client is None:
        token = os.environ.get('SLACK_BOT_TOKEN')

        if not token:
            logger.warning("SLACK_BOT_TOKEN not found in environment")
            return None

        try:
            _slack_client = WebClient(token=token)
            logger.info("Slack client initialized successfully")
        except Exception as e:
            logger.error(
                "Failed to initialize Slack client",
                exc_info=True,
                extra={'error': str(e)}
            )
            raise

    return _slack_client


def post_to_slack(
    channel: str,
    thread_ts: str,
    response_text: str,
    blocks: Optional[List[Dict]] = None,
    on_success: Optional[Callable[[str], None]] = None
) -> bool:
    """
    Post a message to Slack with comprehensive error handling.

    Args:
        channel: Slack channel ID
        thread_ts: Thread timestamp (for threading)
        response_text: Text content of the message
        blocks: Optional Block Kit blocks for rich formatting
        on_success: Optional callback function called with message timestamp on success

    Returns:
        True if message posted successfully, False otherwise
    """
    slack_client = get_slack_client()
    if not slack_client:
        logger.warning("Slack client not initialized - cannot post response")
        return False

    # Validate inputs
    if not channel or not thread_ts:
        logger.error(
            "Invalid channel or thread_ts",
            extra={'channel': channel, 'thread_ts': thread_ts}
        )
        return False

    if not response_text or len(response_text.strip()) == 0:
        logger.warning("Empty response text, skipping post")
        return False

    try:
        logger.info(
            "Posting message to Slack",
            extra={
                'channel': channel,
                'thread_ts': thread_ts,
                'size': len(response_text)
            }
        )

        result = slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=response_text,
            blocks=blocks if blocks else None,
            unfurl_links=False,
            unfurl_media=False
        )

        # Validate response from Slack API
        if result.get('ok'):
            response_ts = result.get('ts')
            logger.info(
                "Message posted successfully",
                extra={
                    'ts': response_ts,
                    'size': len(response_text),
                    'channel': channel
                }
            )

            # Call success callback if provided
            if on_success and response_ts:
                on_success(response_ts)

            return True
        else:
            # Slack API returned ok=False
            error_msg = result.get('error', 'Unknown error')
            logger.error(
                "Slack API returned error",
                extra={
                    'error': error_msg,
                    'response': result,
                    'channel': channel
                }
            )
            return False

    except SlackApiError as e:
        error_code = e.response.get('error') if e.response else 'unknown'
        logger.error(
            "SlackApiError posting message",
            exc_info=True,
            extra={
                'error_code': error_code,
                'channel': channel,
                'thread_ts': thread_ts,
                'message_size': len(response_text)
            }
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error posting to Slack",
            exc_info=True,
            extra={
                'channel': channel,
                'thread_ts': thread_ts,
                'message_size': len(response_text)
            }
        )
        return False


def upload_file_to_slack(
    channel: str,
    thread_ts: str,
    file_content: str,
    filename: str,
    summary_text: str,
    on_success: Optional[Callable[[str, str], None]] = None
) -> bool:
    """
    Upload a file to Slack when response exceeds message limits.

    Args:
        channel: Slack channel ID
        thread_ts: Thread timestamp (for threading)
        file_content: Content of the file
        filename: Name of the file
        summary_text: Summary text to post with the file
        on_success: Optional callback function called with (message_ts, file_url) on success

    Returns:
        True if file uploaded successfully, False otherwise
    """
    slack_client = get_slack_client()
    if not slack_client:
        logger.warning("Slack client not initialized - cannot upload file")
        return False

    try:
        logger.info(
            "Uploading file to Slack",
            extra={
                'filename': filename,
                'size': len(file_content),
                'channel': channel
            }
        )

        # Upload using Slack SDK files_upload_v2
        upload_response = slack_client.files_upload_v2(
            channel=channel,
            content=file_content,
            filename=filename,
            title="DARX Response",
            initial_comment=summary_text,
            thread_ts=thread_ts
        )

        # Check upload success
        if upload_response and upload_response.get('ok'):
            file_data = upload_response.get('file', {})
            file_url = file_data.get('permalink') or file_data.get('url_private')
            message_ts = upload_response.get('ts', thread_ts)

            logger.info(
                "File uploaded successfully",
                extra={
                    'filename': filename,
                    'file_url': file_url,
                    'message_ts': message_ts
                }
            )

            # Call success callback if provided
            if on_success and file_url:
                on_success(message_ts, file_url)

            return True
        else:
            logger.warning(
                "File upload failed",
                extra={'response': upload_response}
            )
            return False

    except SlackApiError as e:
        logger.error(
            "Failed to upload file to Slack",
            exc_info=True,
            extra={'filename': filename}
        )
        return False

    except Exception as e:
        logger.error(
            "File upload exception",
            exc_info=True,
            extra={'filename': filename}
        )
        return False


def reset_slack_client():
    """
    Reset the Slack client singleton.

    Useful for testing or when token changes.
    """
    global _slack_client
    _slack_client = None
    logger.info("Slack client reset")
