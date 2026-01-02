import json
import finter
from finter.settings import get_api_client, logger
from finter.utils.timer import timer


def _parse_api_error(exception):
    """
    Parse API error and extract user-friendly message.

    :param exception: Exception from API call
    :return: Formatted error message
    """
    try:
        # Try to extract error body from ApiException
        if hasattr(exception, 'body'):
            error_data = json.loads(exception.body)

            # Extract nested message if it exists
            message = error_data.get('message', '')

            # Check if message is a stringified dict (common server error)
            if message.startswith('{') or message.startswith("{'"):
                try:
                    # Try to parse nested JSON/dict
                    nested = eval(message) if message.startswith("{'") else json.loads(message)
                    if isinstance(nested, dict) and 'message' in nested:
                        message = nested['message']
                except Exception:
                    pass  # Keep original message if parsing fails

            # Format clean error message
            title = error_data.get('title', 'Error')
            return f"{title}: {message}"

        # Fallback to original exception message
        return str(exception)

    except Exception:
        # If parsing fails, return original error
        return str(exception)


@timer
def submit_model(model_info, output_directory, docker_submit, staging, model_nickname=None):
    """
    Submits the model to the Finter platform.

    :param model_info: Information about the model to submit.
    :param output_directory: Directory containing the model output files.
    :param docker_submit: Whether to submit the model using Docker.
    :return: The result of the submission if successful, None otherwise.
    """
    try:
        res = finter.SubmissionApi(get_api_client()).submission_create(
            model_info, output_directory, docker_submit, staging, model_nickname
        )
        return res
    except Exception as e:
        # Parse and log user-friendly error message
        error_message = _parse_api_error(e)
        logger.error(f"Error submitting the model: {error_message}")
        return None
