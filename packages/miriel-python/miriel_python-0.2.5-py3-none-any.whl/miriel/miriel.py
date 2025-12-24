import base64
import json
import logging
import os
import re
import string
import time
from contextlib import ExitStack
from enum import Enum
from typing import Any, Dict, Iterator, Optional
from urllib.parse import urlparse
from uuid import UUID

import requests
from requests.exceptions import HTTPError, RequestException

COMMON_FILE_EXTENSIONS = [
    # Documents
    '.doc',
    '.docx',
    '.markdown',
    '.md',
    '.odt',
    '.pdf',
    '.rtf',
    '.tex',
    '.txt',
    # Spreadsheets / Data
    '.csv',
    '.json',
    '.ods',
    '.parquet',
    '.tsv',
    '.xls',
    '.xlsx',
    '.xml',
    '.yaml',
    '.yml',
    # Presentations
    '.odp',
    '.ppt',
    '.pptx',
    # Code / Config
    '.bat',
    '.c',
    '.cfg',
    '.cpp',
    '.cs',
    '.css',
    '.env',
    '.go',
    '.html',
    '.ini',
    '.ipynb',
    '.java',
    '.js',
    '.py',
    '.rb',
    '.sh',
    '.toml',
    '.ts',
    # Images
    '.bmp',
    '.gif',
    '.ico',
    '.jpeg',
    '.jpg',
    '.png',
    '.svg',
    '.tiff',
    '.webp',
    # Archives / Compressed
    '.7z',
    '.gz',
    '.rar',
    '.tar',
    '.xz',
    '.zip',
    # Audio / Video
    '.aac',
    '.avi',
    '.flac',
    '.mkv',
    '.mov',
    '.mp3',
    '.mp4',
    '.ogg',
    '.wav',
    '.webm',
    # Misc
    '.bin',
    '.db',
    '.exe',
    '.log',
    '.sqlite',
]


class ExhaustiveOptions(Enum):
    """
    For setting query's exhaustive query mode.
    """

    # with auto, miriel will decide the best type of query to answer the question
    AUTO = 'auto'
    FORCE_OFF = False
    FORCE_ON = True


MAX_POLLING_INTERVAL = 60

_logger = logging.getLogger(__name__)

_WHITESPACE = set(string.whitespace)


def _is_single_token(s: str) -> bool:
    """True if the string is one token (no whitespace/newlines)."""
    return bool(s) and not any(ch in _WHITESPACE for ch in s)


def _is_pure_uri(s: str) -> bool:
    """
    Treat as URI only if the whole string is a single token URI
    with a known scheme. Do NOT trigger on text that merely contains a URI.
    """
    s = s.strip()
    if not _is_single_token(s):
        return False
    p = urlparse(s)
    if p.scheme not in {
        'http',
        'https',
        'file',
        'folder',
        'directory',
        'dir',
        's3',
        'rtsp',
        'discord',
        'gcalendar',
        'string',
    }:
        return False
    return bool(p.netloc or p.path)


def _looks_like_path_pure(s: str) -> bool:
    """
    Treat as local path only if the whole string is a single token that looks
    like a real path. Do NOT trigger on multiline or text with spaces.
    """
    s = s.strip()
    if not _is_single_token(s):
        return False

    # absolute or home-relative or typical relative prefixes
    if s.startswith(('~', './', '../', os.sep)):
        return True

    # Windows drive root (C:\ or C:/)
    if os.name == 'nt' and re.match(r'^[A-Za-z]:[\\/]', s):
        return True

    # filename-like (single token with a common extension)
    if any(s.lower().endswith(ext) for ext in COMMON_FILE_EXTENSIONS):
        return True

    # last resort: if it exists on disk and is single token
    try:
        return os.path.exists(os.path.abspath(os.path.expanduser(s)))
    except Exception:
        return False


class UnauthorizedError(Exception):
    pass


class MirielRequestError(Exception):
    """Generic API error (non-401)."""

    def __init__(self, status_code: int, message: str, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class MirielStreamError(Exception):
    """Raised when the SSE stream emits an error event or terminates unexpectedly."""


def _normalize_stream_timeout(timeout: Optional[Any]) -> Any:
    """
    requests timeout:
      - None => no timeout (not recommended for connect)
      - float/int => both connect+read timeout
      - (connect, read) tuple
    For SSE, we usually want a finite connect timeout and an infinite read timeout.
    """
    if timeout is None:
        return (30, None)  # connect=30s, read=∞
    if isinstance(timeout, (int, float)):
        return (float(timeout), None)
    return timeout


def _iter_sse_data_messages(resp: requests.Response) -> Iterator[str]:
    """
    Yield SSE 'data' payloads as complete messages (joined across multi-line data fields).

    Backend emits messages like:
      data: {"type": "chunk", "content": "Hello"}
      <blank line>

    We support:
      - comments (": keepalive")
      - multiple data: lines per message
    """
    data_lines: list[str] = []
    for raw in resp.iter_lines(decode_unicode=True):
        if raw is None:
            continue
        line = raw.rstrip('\r')

        # blank line => end of one SSE event
        if line == '':
            if data_lines:
                yield '\n'.join(data_lines)
                data_lines = []
            continue

        # comment/keepalive
        if line.startswith(':'):
            continue

        # only handle data lines
        if line.startswith('data:'):
            data_lines.append(line[len('data:') :].lstrip())
            continue

        # ignore other SSE fields: event:, id:, retry:, etc.

    # flush if stream closes without trailing blank line
    if data_lines:
        yield '\n'.join(data_lines)


class Miriel:
    def __init__(
        self,
        api_key=None,
        base_url='https://api.prod.miriel.ai',
        verify=True,
        api_version='v2',
    ):
        """
        api_key: Your Miriel API key. Get one at https://miriel.ai
        base_url: Base URL for the Miriel API
        verify: Whether to verify SSL certificates
        api_version: API version to use
        """
        if not api_key:
            raise UnauthorizedError('API key is required. Please visit https://miriel.ai to sign up.')
        self.api_key = api_key
        self.api_version = api_version
        self.base_url = base_url
        self.verify = verify

    # ----------------------------
    # Core request helpers
    # ----------------------------

    def _build_url(self, route: str) -> str:
        return f'{self.base_url}/api/{self.api_version}/{route}'

    def _apply_auth(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers = dict(headers or {})
        headers['x-access-token'] = self.api_key
        return headers

    def _raise_for_status(self, resp: requests.Response) -> None:
        """
        Raise nice exceptions for non-2xx responses.
        """
        try:
            resp.raise_for_status()
        except HTTPError as err:
            status = err.response.status_code if err.response is not None else -1
            body = None
            try:
                body = err.response.text if err.response is not None else None
            except Exception:
                body = None

            if status == 401:
                raise UnauthorizedError('Invalid API key. Please visit https://miriel.ai to sign up.') from err

            # Special-case 501 for voice_mode unsupported
            if status == 501:
                # try to surface message from JSON
                msg = 'Not implemented'
                try:
                    j = err.response.json() if err.response is not None else None
                    if isinstance(j, dict):
                        msg = j.get('error') or j.get('message') or msg
                except Exception:
                    pass
                raise MirielRequestError(status, msg, body=body) from err

            raise MirielRequestError(status, f'Miriel request error ({status})', body=body) from err

    def _request_raw(self, method, route: str, **kwargs) -> requests.Response:
        """
        Perform an HTTP request and return the Response (no JSON parsing).
        """
        url = self._build_url(route)

        headers = kwargs.pop('headers', None)
        kwargs['headers'] = self._apply_auth(headers)

        # Always apply verify unless explicitly overridden
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify

        resp = method(url, **kwargs)
        self._raise_for_status(resp)
        return resp

    def _request_json(self, method, route: str, **kwargs) -> Dict[str, Any]:
        """
        Perform an HTTP request and parse JSON.
        """
        resp = self._request_raw(method, route, **kwargs)
        try:
            return resp.json()
        except ValueError as e:
            # Include response body for easier debugging
            _logger.error(f'Error parsing JSON response: status={resp.status_code} body={resp.text[:1000]!r}')
            raise e

    def serialize_payload_for_form(self, payload):
        """Convert all nested dicts/lists in the payload to JSON strings."""
        serialized = {}
        for key, value in (payload or {}).items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value
        return serialized

    def make_post_request(self, route, payload=None, files=None):
        """
        Makes a POST request to the given URL.

        - If 'files' is provided, sends a multipart/form-data request:
          - The 'payload' is included as regular form fields via the 'data=' parameter.
        - Otherwise, sends a JSON body using the 'json=' parameter.
        """
        if files:
            headers = {'Accept': 'application/json'}
            payload = self.serialize_payload_for_form(payload or {})
            return self._request_json(
                requests.post,
                route,
                headers=headers,
                data=payload,
                files=files,
            )
        else:
            headers = {'Content-Type': 'application/json'}
            return self._request_json(
                requests.post,
                route,
                headers=headers,
                json=payload,
            )

    def _get_request(self, route: str):
        headers = {'Content-Type': 'application/json'}
        return self._request_json(
            requests.get,
            route,
            headers=headers,
        )

    # ----------------------------
    # Query: non-streaming + streaming + voice
    # ----------------------------

    def query(
        self,
        query: str,
        *,
        streaming: bool = False,
        voice_mode: bool = False,
        voice: Optional[str] = None,
        yield_events: bool = False,
        timeout: Optional[Any] = None,
        force_exhaustive: Optional[ExhaustiveOptions] = ExhaustiveOptions.FORCE_OFF,
        response_format: Optional[dict] = None,
        email_results: Optional[list] = None,
        **params,
    ):
        """
        Perform a Miriel query.

        New features:
          - streaming=True: returns an iterator (SSE). By default yields text chunks (strings).
            Set yield_events=True to yield full event dicts (metadata/start/chunk/audio/done/error).
          - voice_mode=True: enables audio output (provider-dependent). For non-streaming queries,
            audio comes back in JSON as results.audio_content (base64-encoded).
            For streaming+voice, an SSE event {"type":"audio","audio_content":"..."} is emitted near the end.
          - voice="alloy"|"echo"|"fable"|"onyx"|"nova"|"shimmer": voice name for TTS (OpenAI).

        Backwards compatible:
          - If streaming=False, returns the same JSON structure as before.

        Args:
          timeout:
            - for non-streaming: passed to requests (float or tuple)
            - for streaming: connect timeout is used; read timeout defaults to None (infinite) unless you pass a tuple
          force_exhaustive: force exhaustive query on, off, or use auto mode
          response_format: see readme for details, allows custom response schema
          email_results: list of email addresses to email results to

        Returns:
          - dict (non-streaming)
          - iterator[str] (streaming, yield_events=False)
          - iterator[dict] (streaming, yield_events=True)
        """
        route = 'query'
        publish_options = ''
        if email_results:
            publish_options = json.dumps(
                [
                    {
                        'type': 'email',
                        'to_addresses': email_results,
                    }
                ]
            )
        payload = {
            'query': query,
            'streaming': bool(streaming),
            'voice_mode': bool(voice_mode),
            'voice': voice,
            'force_exhaustive': force_exhaustive.value,
            'response_format': response_format,
            'publish_options': publish_options,
            **{k: v for k, v in params.items() if v is not None},
        }

        if not streaming:
            # Normal JSON response
            return self.make_post_request(route, payload=payload)

        # Streaming SSE response
        if yield_events:
            return self.query_stream_events(payload, timeout=timeout)
        return self.query_stream_text(payload, timeout=timeout)

    def query_stream_events(
        self, payload: Dict[str, Any], *, timeout: Optional[Any] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Low-level streaming API. Yields parsed SSE event dicts.

        Each event is usually one of:
          - {"type":"metadata", ...}
          - {"type":"start", ...}
          - {"type":"chunk", "content":"..."}
          - {"type":"audio", "audio_content":"..."}   (streaming+voice_mode)
          - {"type":"done"}
          - {"type":"error", "error":"..."}
        """
        headers = {
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }
        timeout = _normalize_stream_timeout(timeout)

        resp: Optional[requests.Response] = None
        try:
            resp = self._request_raw(
                requests.post,
                'query',
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout,
            )

            for data in _iter_sse_data_messages(resp):
                if not data:
                    continue
                try:
                    event = json.loads(data)
                    if isinstance(event, dict):
                        yield event
                    else:
                        # Unexpected shape; still surface it
                        yield {'type': 'message', 'data': event}
                except json.JSONDecodeError:
                    # Non-JSON message; surface raw
                    yield {'type': 'message', 'data': data}
        except RequestException as e:
            raise MirielStreamError(f'Stream connection error: {e}') from e
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass

    def query_stream_text(self, payload: Dict[str, Any], *, timeout: Optional[Any] = None) -> Iterator[str]:
        """
        Convenience streaming API. Yields ONLY the text chunks (strings).

        If the stream emits an error event, raises MirielStreamError.

        Note:
          - If you need vector_db_results metadata or audio_content (voice streaming),
            use query(..., streaming=True, yield_events=True) or query_stream_events(...).
        """
        for event in self.query_stream_events(payload, timeout=timeout):
            etype = event.get('type')
            if etype == 'chunk':
                yield event.get('content', '')
            elif etype == 'error':
                msg = event.get('error') or event.get('message') or 'Unknown streaming error'
                raise MirielStreamError(msg)
            elif etype == 'done':
                break

    def query_voice(
        self,
        query: str,
        *,
        voice: str = 'alloy',
        timeout: Optional[Any] = None,
        **params,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for non-streaming voice mode queries.
        Returns JSON with results.audio_content (base64 mp3) when supported.
        """
        return self.query(query, streaming=False, voice_mode=True, voice=voice, timeout=timeout, **params)

    # ----------------------------
    # Audio helpers
    # ----------------------------

    @staticmethod
    def decode_audio_content(audio_content_base64: str) -> bytes:
        """Decode base64 audio (MP3 bytes for OpenAI) to raw bytes."""
        return base64.b64decode(audio_content_base64)

    @staticmethod
    def save_audio_content(audio_content_base64: str, path: str) -> str:
        """Decode base64 audio and save to a file; returns the file path."""
        audio_bytes = base64.b64decode(audio_content_base64)
        with open(path, 'wb') as f:
            f.write(audio_bytes)
        return path

    # ----------------------------
    # Jobs / learn / document mgmt (unchanged except minor robustness)
    # ----------------------------

    def wait_for_jobs(self, job_ids, polling_interval=None, user_id=None):
        """
        Poll the API for specific job_ids until all are 'completed'.
        """
        if not job_ids:
            return

        route = 'get_job_status'

        exponential_backoff = False
        if not polling_interval:
            exponential_backoff = True
            polling_interval = 1

        while True:
            payload = {'job_ids': job_ids}
            if user_id is not None:
                payload['user_id'] = user_id

            try:
                response = self._request_json(
                    requests.post,
                    route,
                    headers={'Content-Type': 'application/json'},
                    json=payload,
                )
            except (ValueError, HTTPError, MirielRequestError, RequestException):
                time.sleep(polling_interval or 1)
                if exponential_backoff:
                    polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)
                continue

            statuses = response.get('jobs', {})
            pending_left = [jid for jid, st in statuses.items() if st != 'completed']

            if not pending_left:
                return  # all done

            _logger.info(f'Waiting on {len(pending_left)} job(s): {", ".join(pending_left)}')
            time.sleep(polling_interval or 1)
            if exponential_backoff:
                polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)

    def learn(
        self,
        input: str | list,
        user_id=None,
        metadata=None,
        force_string=False,
        discoverable=True,
        grant_ids=['*'],
        domain_restrictions=None,
        recursion_depth=0,
        priority=100,
        project=None,
        wait_for_complete=False,
        chunk_size=None,
        polling_interval=None,
        command=None,
        upsert_ids: Optional[list] = None,
        expiration_seconds: Optional[int] = None,
    ):
        """
        Add a string, URL, or file to the Miriel AI system for learning.

        Notes:
          - Supports new-format learn inputs (value/upsert_id/command) and now also supports expiration_seconds.
          - Behavior unchanged from your previous client unless you provide expiration_seconds.

        input: str|list - file path, directory path, URL, or literal string to learn, OR a list of such values
        force_string: True will always treat input as a string.
        upsert_ids: optional list of resource ids to upsert documents. order and length must match input list.
        command: add, upsert, or append. upsert and append require upsert_id.
        polling_interval: seconds between polling for job status when wait_for_complete=True.
        """
        parsed_inputs = []
        files_list = []

        inputs = input if isinstance(input, list) else [input]

        if upsert_ids is not None:
            if not isinstance(upsert_ids, list):
                raise ValueError('upsert_ids must be a list if provided.')
            if len(upsert_ids) != len(inputs):
                raise ValueError('Length of upsert_ids must match length of input list.')
        else:
            upsert_ids = [None] * len(inputs)

        with ExitStack() as stack:
            for raw_input, upsert_id in zip(inputs, upsert_ids):
                raw_input = raw_input.strip()

                resolved_path = None
                if force_string:
                    is_file = False
                    is_directory = False
                else:
                    if _is_pure_uri(raw_input):
                        is_file = False
                        is_directory = False
                    elif _looks_like_path_pure(raw_input):
                        expanded_path = os.path.expanduser(raw_input)
                        resolved_path = os.path.abspath(expanded_path)
                        if os.path.exists(resolved_path):
                            raw_input = resolved_path
                            is_file = True
                            is_directory = os.path.isdir(resolved_path)
                        else:
                            raise FileNotFoundError(
                                f"Input '{raw_input}' looks like a file or path, but no file was found at: {resolved_path}.\n"
                                'Hint: If this was meant to be a text string, use force_string=True.'
                            )
                    else:
                        is_file = False
                        is_directory = False

                if is_file:
                    if is_directory:
                        for dirpath, _, filenames in os.walk(raw_input):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                handle = stack.enter_context(open(filepath, 'rb'))
                                files_list.append(('files', (filename, handle, 'application/octet-stream')))
                                parsed_inputs.append(
                                    Miriel._format_learn_input(
                                        filename,
                                        upsert_id=upsert_id,
                                        command=command,
                                        expiration_seconds=expiration_seconds,
                                    )
                                )
                    else:
                        filename = os.path.basename(raw_input)
                        handle = stack.enter_context(open(raw_input, 'rb'))
                        files_list.append(('files', (filename, handle, 'application/octet-stream')))
                        parsed_inputs.append(
                            Miriel._format_learn_input(
                                filename,
                                upsert_id=upsert_id,
                                command=command,
                                expiration_seconds=expiration_seconds,
                            )
                        )
                else:
                    parsed_inputs.append(
                        Miriel._format_learn_input(
                            raw_input,
                            upsert_id=upsert_id,
                            command=command,
                            expiration_seconds=expiration_seconds,
                        )
                    )

            if isinstance(priority, str):
                if priority == 'norank':
                    priority = -1
                elif priority == 'pin':
                    priority = -2

            payload = {
                'user_id': user_id,
                'input': parsed_inputs,
                'metadata': metadata,
                'force_string': force_string,
                'discoverable': discoverable,
                'grant_ids': grant_ids,
                'domain_restrictions': domain_restrictions,
                'recursion_depth': recursion_depth,
                'priority': priority,
                'chunk_size': chunk_size,
                'polling_interval': polling_interval,
            }
            if project is not None:
                payload['project'] = project

            _logger.info(f'Uploading {len(payload["input"])} items, {len(files_list)} files...')
            route = 'learn'
            response = self.make_post_request(route, payload=payload, files=(files_list or None))

        if wait_for_complete:
            job_ids = (response or {}).get('job_ids', [])
            if job_ids:
                self.wait_for_jobs(job_ids, polling_interval=polling_interval, user_id=user_id)
            else:
                # Legacy fallback
                exponential_backoff = False
                if not polling_interval:
                    polling_interval = 1
                    exponential_backoff = True
                while self.count_non_completed_learning_jobs() > 0:
                    _logger.info('Waiting for all learning jobs to complete...')
                    time.sleep(polling_interval or 1)
                    if exponential_backoff:
                        polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)

        return response

    @classmethod
    def _format_learn_input(cls, input_value, upsert_id=None, command=None, expiration_seconds: Optional[int] = None):
        """
        Helper to ensure proper data structure for learn api.
        Corresponds to the new format introduced in 2025.10.
        """
        return {
            'value': input_value,
            'upsert_id': upsert_id,
            'command': command,
            'expiration_seconds': expiration_seconds,
        }

    def get_learning_jobs(self):
        return self.make_post_request('get_monitor_jobs', payload={'job_status': 'all'})

    def count_non_completed_learning_jobs(self):
        jobs = self.get_learning_jobs()
        if not jobs:
            return 0
        pending_count = sum(len(group.get('job_list', [])) for group in jobs.get('pending_jobs', []))
        queued_count = len(jobs.get('queued_items', []))
        return pending_count + queued_count

    def update_document(
        self,
        document_id,
        user_id=None,
        metadata=None,
        discoverable=True,
        grant_ids=['*'],
        chunk_size=None,
    ):
        return self.make_post_request(
            'update_document',
            payload={
                'user_id': user_id,
                'document_id': document_id,
                'metadata': metadata,
                'discoverable': discoverable,
                'grant_ids': grant_ids,
                'chunk_size': chunk_size,
            },
        )

    def create_user(self):
        return self.make_post_request('create_user', payload={})

    def set_document_access(self, user_id, document_id, grant_ids):
        return self.make_post_request(
            'set_document_access',
            payload={
                'user_id': user_id,
                'document_id': document_id,
                'grant_ids': grant_ids,
            },
        )

    def get_document_by_id(self, document_id, user_id=None):
        return self.make_post_request(
            'get_document_by_id',
            payload={'user_id': user_id, 'document_id': document_id},
        )

    def get_monitor_sources(self, user_id=None):
        return self.make_post_request('get_monitor_sources', payload={'user_id': user_id})

    def remove_all_documents(self, user_id=None, project=None):
        return self.make_post_request('remove_all_documents', payload={'user_id': user_id, 'project': project})

    def get_users(self):
        return self.make_post_request('get_users', payload={})

    def delete_user(self, user_id):
        return self.make_post_request('delete_user', payload={'user_id': user_id})

    def get_projects(self):
        return self.make_post_request('get_projects', payload={})

    def create_project(self, name):
        return self.make_post_request('create_project', payload={'name': name})

    def delete_project(self, project_name):
        return self.make_post_request('delete_project', payload={'name': project_name})

    def get_document_count(self):
        return self.make_post_request('get_document_count', payload={})

    def get_user_policies(self):
        return self.make_post_request('get_user_policies', payload={})

    def add_user_policy(self, policy, project_id=None):
        payload = {'policy': policy}
        if project_id is not None:
            payload['project_id'] = project_id
        return self.make_post_request('add_user_policy', payload=payload)

    def delete_user_policy(self, policy_id, project_id=None):
        payload = {'policy_id': policy_id}
        if project_id is not None:
            payload['project_id'] = project_id
        return self.make_post_request('delete_user_policy', payload=payload)

    def remove_document(self, document_id, user_id=None):
        return self.make_post_request('remove_document', payload={'document_id': document_id, 'user_id': user_id})

    def get_all_documents(self, user_id=None, project=None, metadata_query=None):
        payload = {}
        if user_id is not None:
            payload['user_id'] = user_id
        if project is not None:
            payload['project'] = project
        if metadata_query is not None:
            payload['metadata_query'] = metadata_query
        return self.make_post_request('get_all_documents', payload=payload)

    def remove_resource(self, resource_id, user_id=None):
        payload = {'resource_id': resource_id}
        if user_id is not None:
            payload['user_id'] = user_id
        return self.make_post_request('remove_resource', payload=payload)

    def get_query_result(self, query_id: UUID):
        route = f'query/{query_id}'
        return self._get_request(route)
