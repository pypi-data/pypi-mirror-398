"""Tests for synapse_sdk.clients.utils module."""

from __future__ import annotations

from synapse_sdk.clients.utils import build_url, extract_error_detail, parse_json_response

# -----------------------------------------------------------------------------
# build_url Tests
# -----------------------------------------------------------------------------


class TestBuildUrl:
    """Tests for build_url function."""

    def test_simple_join(self):
        """Base URL and path are joined correctly."""
        result = build_url('https://api.example.com', 'users/123')
        assert result == 'https://api.example.com/users/123'

    def test_base_with_trailing_slash(self):
        """Base URL trailing slash is stripped."""
        result = build_url('https://api.example.com/', 'users/123')
        assert result == 'https://api.example.com/users/123'

    def test_path_with_leading_slash(self):
        """Path leading slash is stripped."""
        result = build_url('https://api.example.com', '/users/123')
        assert result == 'https://api.example.com/users/123'

    def test_both_with_slashes(self):
        """Both trailing and leading slashes are handled."""
        result = build_url('https://api.example.com/', '/users/123/')
        assert result == 'https://api.example.com/users/123/'

    def test_no_slashes(self):
        """Works without any slashes."""
        result = build_url('https://api.example.com', 'users')
        assert result == 'https://api.example.com/users'

    def test_trailing_slash_true(self):
        """trailing_slash=True adds trailing slash."""
        result = build_url('https://api.example.com', 'users', trailing_slash=True)
        assert result == 'https://api.example.com/users/'

    def test_trailing_slash_false(self):
        """trailing_slash=False does not add trailing slash."""
        result = build_url('https://api.example.com', 'users', trailing_slash=False)
        assert result == 'https://api.example.com/users'

    def test_trailing_slash_preserved_when_present(self):
        """trailing_slash=True does not double slash if already present."""
        result = build_url('https://api.example.com', 'users/', trailing_slash=True)
        assert result == 'https://api.example.com/users/'

    def test_full_url_path_http(self):
        """Full http:// URL in path is used directly."""
        result = build_url('https://api.example.com', 'http://other.com/resource')
        assert result == 'http://other.com/resource'

    def test_full_url_path_https(self):
        """Full https:// URL in path is used directly."""
        result = build_url('https://api.example.com', 'https://cdn.example.com/files/123')
        assert result == 'https://cdn.example.com/files/123'

    def test_empty_path(self):
        """Empty path returns base URL with slash."""
        result = build_url('https://api.example.com', '')
        assert result == 'https://api.example.com/'

    def test_nested_path(self):
        """Nested paths work correctly."""
        result = build_url('https://api.example.com', 'api/v1/users/123/posts')
        assert result == 'https://api.example.com/api/v1/users/123/posts'

    def test_path_with_query_params(self):
        """Paths with query params are preserved."""
        result = build_url('https://api.example.com', 'users?page=1&limit=10')
        assert result == 'https://api.example.com/users?page=1&limit=10'


# -----------------------------------------------------------------------------
# extract_error_detail Tests
# -----------------------------------------------------------------------------


class TestExtractErrorDetail:
    """Tests for extract_error_detail function."""

    def test_json_response(self, mock_response):
        """Extracts JSON from response."""
        response = mock_response(
            status_code=400,
            json_data={'error': 'Bad request', 'code': 'INVALID'},
        )
        result = extract_error_detail(response)
        assert result == {'error': 'Bad request', 'code': 'INVALID'}

    def test_text_fallback_invalid_json(self, mock_response):
        """Falls back to text when JSON is invalid."""
        response = mock_response(
            status_code=500,
            json_data=None,
            text='Internal Server Error',
        )
        result = extract_error_detail(response)
        assert result == 'Internal Server Error'

    def test_reason_fallback(self, mock_response):
        """Falls back to reason when no text."""
        response = mock_response(
            status_code=404,
            json_data=None,
            text='',
            reason='Not Found',
        )
        result = extract_error_detail(response)
        assert result == 'Not Found'

    def test_reason_phrase_fallback(self):
        """Falls back to reason_phrase (httpx style) when no reason."""

        class HttpxStyleResponse:
            def __init__(self):
                self.reason_phrase = 'Bad Gateway'

            def json(self):
                raise ValueError('No JSON')

        response = HttpxStyleResponse()
        result = extract_error_detail(response)
        assert result == 'Bad Gateway'

    def test_minimal_response(self):
        """Handles response with minimal attributes."""

        class MinimalResponse:
            def json(self):
                raise ValueError('No JSON')

        response = MinimalResponse()
        result = extract_error_detail(response)
        assert result == ''

    def test_json_list_response(self, mock_response):
        """Extracts JSON list from response."""
        response = mock_response(
            status_code=400,
            json_data=['error1', 'error2'],
        )
        result = extract_error_detail(response)
        assert result == ['error1', 'error2']

    def test_empty_json_object(self, mock_response):
        """Handles empty JSON object."""
        response = mock_response(status_code=400, json_data={})
        result = extract_error_detail(response)
        assert result == {}


# -----------------------------------------------------------------------------
# parse_json_response Tests
# -----------------------------------------------------------------------------


class TestParseJsonResponse:
    """Tests for parse_json_response function."""

    def test_valid_json_dict(self, mock_response):
        """Parses valid JSON dict response."""
        response = mock_response(
            status_code=200,
            json_data={'id': 1, 'name': 'Test'},
        )
        result = parse_json_response(response)
        assert result == {'id': 1, 'name': 'Test'}

    def test_valid_json_list(self, mock_response):
        """Parses valid JSON list response."""
        response = mock_response(
            status_code=200,
            json_data=[{'id': 1}, {'id': 2}],
        )
        result = parse_json_response(response)
        assert result == [{'id': 1}, {'id': 2}]

    def test_204_no_content(self, mock_response):
        """Returns None for 204 No Content."""
        response = mock_response(status_code=204, json_data=None, text='')
        result = parse_json_response(response)
        assert result is None

    def test_text_fallback(self, mock_response):
        """Returns text when JSON parsing fails."""
        response = mock_response(
            status_code=200,
            json_data=None,
            text='Plain text response',
        )
        result = parse_json_response(response)
        assert result == 'Plain text response'

    def test_empty_response(self, mock_response):
        """Handles empty text response."""
        response = mock_response(status_code=200, json_data=None, text='')
        result = parse_json_response(response)
        assert result == ''

    def test_html_response(self, mock_response):
        """Returns HTML as text when not JSON."""
        html_content = '<html><body>Error</body></html>'
        response = mock_response(
            status_code=200,
            json_data=None,
            text=html_content,
        )
        result = parse_json_response(response)
        assert result == html_content

    def test_nested_json(self, mock_response):
        """Parses nested JSON structures."""
        nested_data = {
            'user': {
                'id': 1,
                'profile': {'name': 'Test', 'settings': {'theme': 'dark'}},
            },
            'items': [1, 2, 3],
        }
        response = mock_response(status_code=200, json_data=nested_data)
        result = parse_json_response(response)
        assert result == nested_data

    def test_json_with_null_values(self, mock_response):
        """Parses JSON with null values."""
        data = {'id': 1, 'name': None, 'description': None}
        response = mock_response(status_code=200, json_data=data)
        result = parse_json_response(response)
        assert result == data
        assert result['name'] is None
