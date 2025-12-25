from lazyllm.thirdparty import httpx

class HttpExecutorResponse:
    """HTTP executor response class for encapsulating and processing HTTP request response results.

Provides unified access interface for HTTP response content, supporting file type detection and content extraction.

Args:
    response (httpx.Response, optional): httpx library response object, defaults to None

**Returns:**

- HttpExecutorResponse instance, providing multiple response content access methods
"""
    headers: dict[str, str]
    response: 'httpx.Response'

    def __init__(self, response: 'httpx.Response' = None):
        self.response = response
        self.headers = dict(response.headers) if isinstance(self.response, httpx.Response) else {}

    @property
    def is_file(self) -> bool:
        """
        check if response is file
        """
        content_type = self.get_content_type()
        file_content_types = ['image', 'audio', 'video']

        return any(v in content_type for v in file_content_types)

    def get_content_type(self) -> str:
        """Get the content type of the HTTP response.

Extracts the 'content-type' field value from the response headers to determine the type of response content.

**Returns:**

- str: The content type of the response, or empty string if not found.


Examples:
    >>> from lazyllm.tools.http_request.http_executor_response import HttpExecutorResponse
    >>> import httpx
    >>> response = httpx.Response(200, headers={'content-type': 'application/json'})
    >>> http_response = HttpExecutorResponse(response)
    >>> content_type = http_response.get_content_type()
    >>> print(content_type)
    ... 'application/json'
    """
        return self.headers.get('content-type', '')

    def extract_file(self) -> tuple[str, bytes]:
        """
        extract file from response if content type is file related
        """
        if self.is_file:
            return self.get_content_type(), self.body

        return '', b''

    @property
    def content(self) -> str:
        if isinstance(self.response, httpx.Response):
            return self.response.text
        else:
            raise ValueError(f'Invalid response type {type(self.response)}')

    @property
    def body(self) -> bytes:
        if isinstance(self.response, httpx.Response):
            return self.response.content
        else:
            raise ValueError(f'Invalid response type {type(self.response)}')

    @property
    def status_code(self) -> int:
        if isinstance(self.response, httpx.Response):
            return self.response.status_code
        else:
            raise ValueError(f'Invalid response type {type(self.response)}')
