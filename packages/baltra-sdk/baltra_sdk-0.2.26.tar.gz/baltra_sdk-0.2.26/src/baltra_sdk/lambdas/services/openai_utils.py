from openai import OpenAI, APITimeoutError, AssistantEventHandler
from datetime import datetime
import openai
import time
import tempfile
from typing_extensions import override
from baltra_sdk.lambdas.db.sql_utils import log_response_time


def get_openai_client(settings):
    """Get an OpenAI client instance.
    
    Args:
        settings: Settings object with OPENAI_KEY_SCREENING attribute
    
    Returns:
        OpenAI: OpenAI client instance
    """
    client = OpenAI(api_key=settings.OPENAI_KEY_SCREENING)
    return client


def wait_for_free_run(client, thread_id, max_attempts=5, base_wait=2, timeout=30):
    """Wait until there are no active runs on a given thread."""

    for attempt in range(max_attempts):
        try:
            active_runs = client.beta.threads.runs.list(thread_id=thread_id, timeout=timeout)
            is_active = any(run.status in ['active', 'queued', 'in_progress', 'cancelling'] for run in active_runs.data)
            if is_active:
                wait_time = base_wait ** attempt
                time.sleep(wait_time)
            else:
                return True
        except openai.APITimeoutError:
            if attempt < max_attempts - 1:
                 time.sleep(base_wait ** attempt)
            else:
                 return False
    return False


def add_msg_to_thread(thread_id, message_body, role, client):
    """Add a message to a thread with retries and timeout handling."""
    if not wait_for_free_run(client, thread_id):
        return "error", role

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=message_body,
                timeout=45
            )
            messages = client.beta.threads.messages.list(thread_id=thread_id, timeout=30)
            return messages.data[0].id, messages.data[0].role

        except openai.APITimeoutError:
            if attempt < max_attempts - 1:
                if not wait_for_free_run(client, thread_id):
                    return "error", role
                time.sleep(2 ** attempt)
            else:
                break
        except Exception as e:
            if attempt < max_attempts - 1:
                if not wait_for_free_run(client, thread_id):
                    return "error", role
                time.sleep(2 ** attempt)
            else:
                break
        except BaseException as critical_error:
            break
    return "error", role


class EventHandler(AssistantEventHandler):
    """Event handler to accumulate text chunks from streaming responses."""

    def __init__(self):
        super().__init__()
        self.full_text = ""

    @override
    def on_text_delta(self, delta, snapshot):
        self.full_text += delta.value


def run_assistant_stream(client, candidate_data, assistant_id, settings, additional_instructions = ""):
    """Run an assistant in streaming mode with retries and timeout handling.
    
    Args:
        client: OpenAI client instance
        candidate_data: Dictionary with candidate data including thread_id
        assistant_id: OpenAI assistant ID
        settings: Settings object with RESPONSE_TO_WHATSAPP_ISSUE attribute
        additional_instructions: Optional additional instructions for the assistant
    
    Returns:
        tuple: (response_text, message_id, role) or (error_response, "error", "assistant")
    """
    thread_id = candidate_data["thread_id"]

    if not wait_for_free_run(client, thread_id):
        return settings.RESPONSE_TO_WHATSAPP_ISSUE, "error", "assistant"

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            start_time = datetime.now()
            handler = EventHandler()
            with client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                additional_instructions=additional_instructions,
                event_handler=handler,
            ) as stream:
                stream.until_done()
            end_time = datetime.now()
            time_delta = (end_time - start_time).total_seconds()
            usage = stream.current_run.usage
            model = stream.current_run.model or "unknown"
            prompt_tokens = usage.prompt_tokens if usage and hasattr(usage, "prompt_tokens") else 0
            completion_tokens = usage.completion_tokens if usage and hasattr(usage, "completion_tokens") else 0
            total_tokens = usage.total_tokens if usage and hasattr(usage, "total_tokens") else 0

            log_response_time(candidate_data, start_time, end_time, time_delta, assistant_id, model, prompt_tokens, completion_tokens, total_tokens)

            messages = client.beta.threads.messages.list(thread_id=thread_id, timeout=30)
            assistant_messages = [m for m in messages.data if m.role == "assistant"]
            if not assistant_messages:
                raise Exception("No assistant messages found after streaming.")
            last_message = assistant_messages[0]
            return last_message.content[0].text.value, last_message.id, last_message.role

        except APITimeoutError:
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                break
        except BaseException as critical_error:
            break
    return settings.RESPONSE_TO_WHATSAPP_ISSUE, "error", "assistant"


def transcribe_audio(audio_bytes: bytes, settings, suffix=".mp3") -> str:
    """Transcribe audio bytes to text using OpenAI Whisper.
    
    Args:
        audio_bytes: Audio file bytes
        settings: Settings object with OPENAI_KEY_SCREENING attribute
        suffix: File suffix (default: ".mp3")
    
    Returns:
        str: Transcribed text
    """
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        with open(tmp.name, "rb") as audio_file:
            openai_client = get_openai_client(settings)
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
    return transcription.text


def copy_last_messages_to_new_thread(client, original_thread_id, max_messages=5):
    """Copies the last N messages from an existing thread to a new thread."""
    try:
        messages = client.beta.threads.messages.list(thread_id=original_thread_id, limit=100)
        sorted_messages = sorted(messages.data, key=lambda m: m.created_at)

        last_messages = sorted_messages[-max_messages:]

        new_thread = client.beta.threads.create()
        new_thread_id = new_thread.id

        for msg in last_messages:
            for block in msg.content:
                if block.type == "text":
                    client.beta.threads.messages.create(
                        thread_id=new_thread_id,
                        role=msg.role,
                        content=block.text.value
                    )

        return new_thread_id

    except Exception as e:
        return None

