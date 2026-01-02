"""
Request log parser for LiteLLM debug logs

Extracts and formats API requests and responses from LiteLLM debug logs.
"""

import re
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIRequest:
    """Parsed API request"""
    timestamp: str
    method: str
    url: str
    headers: Dict[str, str]
    body: Dict[str, Any]

    def format(self, with_color: bool = True) -> str:
        """Format request for display"""
        if with_color:
            separator = "\033[96m" + "━" * 70 + "\033[0m"
            title = "\033[1;96m🚀 REQUEST\033[0m"
            method_color = "\033[93m"
            reset = "\033[0m"
        else:
            separator = "━" * 70
            title = "🚀 REQUEST"
            method_color = ""
            reset = ""

        lines = [
            "",
            separator,
            f"{title} [{self.timestamp}]",
            separator,
            f"{method_color}{self.method} {self.url}{reset}",
            ""
        ]

        # Headers
        if self.headers:
            lines.append("Headers:")
            for key, value in self.headers.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Body
        if self.body:
            lines.append("Body:")
            body_str = json.dumps(self.body, indent=2, ensure_ascii=False)
            for line in body_str.split('\n'):
                lines.append(f"  {line}")

        lines.append(separator)
        return "\n".join(lines)


@dataclass
class APIResponse:
    """Parsed API response"""
    timestamp: str
    status_code: Optional[int]
    duration_ms: Optional[int]
    data: Dict[str, Any]

    def format(self, with_color: bool = True) -> str:
        """Format response for display"""
        if with_color:
            separator = "\033[92m" + "━" * 70 + "\033[0m"
            title = "\033[1;92m📥 RESPONSE\033[0m"
            reset = "\033[0m"
        else:
            separator = "━" * 70
            title = "📥 RESPONSE"
            reset = ""

        # Build status line
        status_parts = [title, f"[{self.timestamp}]"]
        if self.status_code:
            status_parts.append(f"• {self.status_code} OK")
        if self.duration_ms:
            status_parts.append(f"• {self.duration_ms}ms")

        lines = [
            "",
            separator,
            " ".join(status_parts),
            separator
        ]

        # Extract key fields
        if 'model' in self.data:
            lines.append(f"Model: {self.data['model']}")

        if 'id' in self.data:
            lines.append(f"ID: {self.data['id']}")

        # Content
        if 'choices' in self.data and len(self.data['choices']) > 0:
            choice = self.data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                lines.append(f"\nContent:")
                lines.append(f"  {content}")

        # Usage
        if 'usage' in self.data:
            usage = self.data['usage']
            lines.append(f"\nTokens: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={usage.get('total_tokens', 0)}")

        lines.append(separator)
        return "\n".join(lines)


class RequestLogParser:
    """Parser for LiteLLM request logs"""

    # Regex patterns
    REQUEST_PATTERN = re.compile(
        r'POST Request Sent from LiteLLM:\s*\ncurl -X POST.*?\n(.*?)\n-H \'Authorization: (.*?)\'.*?\n-d \'(.*)\'',
        re.DOTALL
    )

    RESPONSE_PATTERN = re.compile(
        r'RAW RESPONSE:\s*(\{.*\})',
        re.DOTALL
    )

    TIMESTAMP_PATTERN = re.compile(
        r'(\d{2}:\d{2}:\d{2})'
    )

    @staticmethod
    def extract_url(curl_text: str) -> Optional[str]:
        """Extract URL from curl command"""
        # Pattern: curl -X POST \nhttps://.../ \n
        url_pattern = re.compile(r'curl -X POST.*?\n(https?://[^\s]+)', re.DOTALL)
        match = url_pattern.search(curl_text)
        if match:
            url = match.group(1).strip().rstrip('\\').strip()
            # If URL ends with /v1/, append chat/completions
            if url.endswith('/v1/') or url.endswith('/v1'):
                url = url.rstrip('/') + '/chat/completions'
            return url
        return None

    @staticmethod
    def extract_request_body(body_str: str) -> Optional[Dict[str, Any]]:
        """Extract request body from curl -d parameter"""
        try:
            # Convert Python dict string to JSON
            # {'key': 'value'} -> {"key": "value"}
            body_str = body_str.replace("'", '"')
            body_str = body_str.replace('True', 'true').replace('False', 'false')
            data = json.loads(body_str)
            # Remove extra_body if empty
            if 'extra_body' in data and not data['extra_body']:
                del data['extra_body']
            return data
        except:
            return None

    @staticmethod
    def parse_request(log_chunk: str) -> Optional[APIRequest]:
        """Parse API request from log chunk"""
        # Extract timestamp
        ts_match = RequestLogParser.TIMESTAMP_PATTERN.search(log_chunk)
        timestamp = ts_match.group(1) if ts_match else datetime.now().strftime("%H:%M:%S")

        # Extract URL
        url = RequestLogParser.extract_url(log_chunk)
        if not url:
            return None

        # Extract authorization header
        auth_match = re.search(r'-H \'Authorization: ([^\']+)\'', log_chunk)
        headers = {}
        if auth_match:
            auth = auth_match.group(1)
            headers['Authorization'] = f'Bearer {auth}'

        # Extract body
        body_match = re.search(r'-d \'(.*)\'', log_chunk, re.DOTALL)
        body = {}
        if body_match:
            body = RequestLogParser.extract_request_body(body_match.group(1)) or {}

        return APIRequest(
            timestamp=timestamp,
            method="POST",
            url=url,
            headers=headers,
            body=body
        )

    @staticmethod
    def parse_response(log_chunk: str) -> Optional[APIResponse]:
        """Parse API response from log chunk"""
        # Extract timestamp
        ts_match = RequestLogParser.TIMESTAMP_PATTERN.search(log_chunk)
        timestamp = ts_match.group(1) if ts_match else datetime.now().strftime("%H:%M:%S")

        # Extract JSON response
        response_match = RequestLogParser.RESPONSE_PATTERN.search(log_chunk)
        if not response_match:
            return None

        try:
            data = json.loads(response_match.group(1))
            return APIResponse(
                timestamp=timestamp,
                status_code=200,  # LiteLLM only logs successful responses here
                duration_ms=None,  # Not available in logs
                data=data
            )
        except json.JSONDecodeError:
            return None

    @staticmethod
    def is_request_log(line: str) -> bool:
        """Check if line contains request log marker"""
        return "POST Request Sent from LiteLLM:" in line

    @staticmethod
    def is_response_log(line: str) -> bool:
        """Check if line contains response log marker"""
        return "RAW RESPONSE:" in line


class LogStreamFilter:
    """Filters and processes log stream for API requests/responses"""

    def __init__(self):
        self.buffer = ""
        self.in_request = False
        self.in_response = False

    def process_line(self, line: str) -> Optional[str]:
        """
        Process a single log line and return formatted output if complete entry found.

        Returns:
            Formatted string if complete request/response found, None otherwise
        """
        if RequestLogParser.is_request_log(line):
            self.in_request = True
            self.buffer = line
            return None

        elif RequestLogParser.is_response_log(line):
            self.in_response = True
            self.buffer = line
            return None

        elif self.in_request or self.in_response:
            self.buffer += line

            # Check if we have complete request/response
            if self.in_request and (line.strip() == "" or line.startswith("[")):
                request = RequestLogParser.parse_request(self.buffer)
                self.buffer = ""
                self.in_request = False
                return request.format() if request else None

            elif self.in_response and (line.strip() == "" or line.startswith("[")):
                response = RequestLogParser.parse_response(self.buffer)
                self.buffer = ""
                self.in_response = False
                return response.format() if response else None

        return None
