# Sthenos API Stubs
# These definitions exist purely for IDE autocompletion.
# The actual logic is executed by the Go runtime.

from typing import Dict, Optional, Any, Union

ENV: Dict[str, str] = {}

class HTTPResponse:
    status: int
    def json(self) -> Any: ...

class HTTP:
    def get(self, url: str, params: Optional[Dict] = None) -> HTTPResponse: ...
    def post(self, url: str, body: Optional[str] = None, params: Optional[Dict] = None) -> HTTPResponse: ...

http = HTTP()

def check(val: Any, checks: Dict[str, Any]) -> bool: ...

def sleep(seconds: Union[int, float]): ...
