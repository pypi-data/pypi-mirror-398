from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse
from fastapi.responses import JSONResponse
from usageflow.core import UsageFlowClient
import time
import re
import json
from typing import Dict, Any, Optional, Tuple
from starlette.routing import Match
class UsageFlowMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage with UsageFlow.

    This middleware integrates with FastAPI to track API requests and responses,
    providing detailed usage analytics and insights.
    :param app: The FastAPI application instance
    :param api_key: The UsageFlow API key
    :param pool_size: Number of WebSocket connections in the pool (default: 10)
    """
    def __init__(self, app: FastAPI, api_key: str, pool_size: int = 10):
        super().__init__(app)
        self.client = UsageFlowClient(api_key, pool_size=pool_size)
        # Connect WebSocket when app is ready
        self.client.connect()

    async def dispatch(self, request: Request, call_next):
        """Middleware to execute logic before and after the request."""
        start_time = time.time()

        route_path = get_router_path(request)

        # Skip tracking for whitelisted routes (server-side config)
        if route_path and self.client.is_endpoint_whitelisted(route_path, request.method):
            return await call_next(request)

        # Track only specific routes if monitor list is set (server-side config)
        if route_path and not self.client.is_endpoint_monitored(route_path, request.method):
            return await call_next(request)

        # Extract metadata (Before Request)
        request_metadata = await self._before_request(request)


        if request_metadata.get("blocked"):
            return JSONResponse(content={"detail": request_metadata["error"]}, status_code=request_metadata["status_code"])

        # Process the request
        response = await call_next(request)

        # Create a streaming wrapper to capture body without blocking
        captured_body = []
        original_iterator = response.body_iterator

        async def capture_and_stream():
            async for chunk in original_iterator:
                captured_body.append(chunk)
                yield chunk

        # Create new streaming response with captured body
        new_response = StreamingResponse(
            content=capture_and_stream(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

        # Schedule post-processing as background task (non-blocking)
        background_task = BackgroundTask(
            self._after_request_background,
            request,
            response,
            captured_body,
            start_time
        )
        new_response.background = background_task

        return new_response

    async def _before_request(self, request: Request) -> Dict[str, Any]:
        """Handle logic before the request reaches the endpoint."""
        request.state.body_data = await self._get_request_body(request)

        metadata = {
            "method": request.method,
            "url": get_router_path(request),
            "rawUrl": str(request.url.path),
            "clientIP": request.client.host if request.client else None,
            "userAgent": request.headers.get("user-agent"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "headers": {k: ("****" if "key" in k.lower() else v) for k, v in request.headers.items()},
            "queryParams": dict(request.query_params),
            "pathParams": dict(request.path_params),
            "body": request.state.body_data,
            "userId": self._extract_user_id(request),
        }


        ledger_id, has_rate_limit, response_tracking_field = self._guess_ledger_id(request)

        request.state.metadata = metadata
        request.state.response_tracking_value = response_tracking_field

        # Check if url is blocked
        if self.client.is_endpoint_blocked(ledger_id):
            return {
                "blocked": True,
                "error": "Endpoint blocked",
                "status_code": 403,
            }

        # Allocate request
        success, result = self.client.allocate_request(ledger_id, metadata, has_rate_limit, response_tracking_field)

        if not success:
            error_message = result.get('error', 'Request fulfillment failed') if result else 'Request fulfillment failed'
            status_code = result.get('status_code', 500) if result else 500

            if status_code == 520:
                # Continue with normal flow for status code 520
                return {"blocked": False}

            return {
                "blocked": True,
                "error": error_message,
                "status_code": status_code,
            }

        # Store event ID and response status code
        # The new format returns allocationId in the payload
        if result and isinstance(result, dict):
            # Check for allocationId in the result (new format)
            if 'allocationId' in result:
                request.state.event_id = result['allocationId']
            elif 'eventId' in result:
                request.state.event_id = result['eventId']
            request.state.response_status_code = 200

        request.state.ledger_id = ledger_id
        return {"blocked": False}

    async def _after_request_background(
        self,
        request: Request,
        original_response: Response,
        captured_body: list,
        start_time: float
    ):
        """Handle logic after the request has been processed (runs in background)."""
        if hasattr(request.state, "event_id") and request.state.event_id:
            metadata = getattr(request.state, "metadata", {})

            # Parse captured body
            response_body = None
            try:
                if captured_body:
                    body_bytes = b"".join(captured_body)
                    content_type = original_response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        response_body = json.loads(body_bytes.decode("utf-8"))
                    else:
                        response_body = body_bytes.decode("utf-8")
            except Exception:
                pass  # Fail silently if parsing fails

            # Extract schema from response body
            response_schema = self.client.extract_schema(response_body) if response_body is not None else None
            amount = None
            if request.state.response_tracking_value:
                # Get By dot notation
                amount = self._get_by_dot_notation(response_body, request.state.response_tracking_value)

            metadata.update({
                "responseStatusCode": original_response.status_code,
                "responseHeaders": dict(original_response.headers),
                "requestDuration": int((time.time() - start_time) * 1000),
                "responseSchema": response_schema,
            })

            self.client.fulfill_request(request.state.ledger_id, request.state.event_id, metadata, amount)


    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request body safely."""
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                return await request.json()
            elif "application/x-www-form-urlencoded" in content_type:
                return dict(await request.form())
            elif "multipart/form-data" in content_type:
                return dict(await request.form())
            else:
                return (await request.body()).decode("utf-8")
        except Exception:
            return None

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from JWT or headers."""
        token = self.client.extract_bearer_token(request.headers.get("Authorization"))
        if token:
            claims = self.client.decode_jwt_unverified(token)
            return claims.get("sub", "anonymous") if claims else "anonymous"
        return request.headers.get("X-User-ID", "anonymous")

    def _parse_jwt_cookie_field(self, field_name: str) -> Optional[Dict[str, str]]:
        """Parse JWT cookie field format: '[technique=jwt]cookieName[pick=claim]'"""
        technique_match = re.match(r'^\[technique=([^\]]+)\]', field_name)
        if not technique_match or technique_match.group(1) != 'jwt':
            return None

        pick_match = re.search(r'\[pick=([^\]]+)\]', field_name)
        if not pick_match:
            return None

        # Extract cookie name: everything between [technique=jwt] and [pick=...]
        technique_end = len(technique_match.group(0))
        pick_start = field_name.find('[pick=')
        if pick_start == -1 or pick_start <= technique_end:
            return None

        cookie_name = field_name[technique_end:pick_start]
        if not cookie_name:
            return None

        return {
            "cookieName": cookie_name,
            "claim": pick_match.group(1),
        }

    def _get_cookie_value(self, headers: Any, cookie_name: str) -> Optional[str]:
        """Parse and extract a specific cookie value from the Cookie header"""
        cookie_header = headers.get("Cookie") or headers.get("cookie")
        if not cookie_header:
            return None

        # Parse cookies from the Cookie header string
        # Format: "name1=value1; name2=value2; name3=value3"
        cookies = []
        for cookie in cookie_header.split(';'):
            parts = cookie.strip().split('=', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                value = parts[1].strip()  # Handle values that might contain '='
                cookies.append({"name": name, "value": value})

        # Find the cookie with the matching name (case-insensitive)
        for cookie in cookies:
            if cookie["name"].lower() == cookie_name.lower():
                return cookie["value"]

        return None

    def _get_by_dot_notation(self, obj: Any, path: str) -> Any:
        """Access nested object properties using dot notation, supporting array iteration with [*]"""
        parts = path.split('.')
        result = obj

        for i, part in enumerate(parts):
            if result is None:
                return None

            # Check if this part contains array iteration [*]
            if '[*]' in part:
                # Split the part: e.g., "users[*]" -> "users" and remaining path
                array_key = part.replace('[*]', '')
                remaining_path = '.'.join(parts[i + 1:]) if i + 1 < len(parts) else None

                # Get the array
                if isinstance(result, dict):
                    array = result.get(array_key)
                else:
                    return None

                # If not an array, return None
                if not isinstance(array, list):
                    return None

                # If there's a remaining path, iterate and return the first matching element
                if remaining_path:
                    for item in array:
                        value = self._get_by_dot_notation(item, remaining_path)
                        if value is not None:
                            return value
                    return None
                else:
                    # No remaining path, return the first element of the array
                    return array[0] if array else None

            # Regular property access
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, list):
                # If result is a list and we're trying to access a property,
                # we might want to handle this differently, but for now return None
                return None
            else:
                return None

        return result

    def _extract_identity_from_location(self, field_name: str, location: str, request: Request, method: str, url: str) -> Optional[str]:
        """Extract identity from the specified location"""
        match location:
            case "path_params":
                path_params = dict(request.path_params)
                if field_name in path_params:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(path_params[field_name])

            case "query_params":
                if field_name in request.query_params:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(request.query_params[field_name])

            case "body":
                if hasattr(request.state, "body_data") and isinstance(request.state.body_data, dict):
                    if field_name in request.state.body_data:
                        return method + " " + url + " " + self.client.transform_to_ledger_id(request.state.body_data[field_name])

            case "headers" | "header":
                header_value = request.headers.get(field_name)
                if header_value:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(header_value)

            case "bearer_token":
                auth_header = request.headers.get("Authorization")
                if auth_header:
                    token = self.client.extract_bearer_token(auth_header)
                    if token:
                        claims = self.client.decode_jwt_unverified(token)
                        if claims and field_name in claims:
                            return method + " " + url + " " + self.client.transform_to_ledger_id(claims[field_name])

            case "cookie":
                # Handle JWT cookie format: '[technique=jwt]cookieName[pick=claim]'
                jwt_cookie_match = self._parse_jwt_cookie_field(field_name)
                if jwt_cookie_match:
                    cookie_name = jwt_cookie_match["cookieName"]
                    claim = jwt_cookie_match["claim"]
                    cookie_value = self._get_cookie_value(request.headers, cookie_name)
                    if cookie_value:
                        claims = self.client.decode_jwt_unverified(cookie_value)
                        if claims and claim in claims:
                            return method + " " + url + " " + self.client.transform_to_ledger_id(claims[claim])
                else:
                    # Handle standard cookie access (e.g., "cookie.session" or "session")
                    cookie_value = None
                    if field_name.lower().startswith("cookie."):
                        cookie_name = field_name[7:]  # Remove "cookie." prefix
                        cookie_value = self._get_cookie_value(request.headers, cookie_name)
                    else:
                        # Use dot notation for regular headers
                        cookie_value = self._get_by_dot_notation(request.headers, field_name)

                    if cookie_value:
                        return method + " " + url + " " + self.client.transform_to_ledger_id(cookie_value)

        return None

    def _guess_ledger_id(self, request: Request) -> Tuple[str, bool, str | None]:
        """Determine the ledger ID from the request"""
        method = request.method
        url = get_router_path(request)

        # Try to get identity from policies first
        policies_map = self.client.get_policies_map()
        policy = policies_map.get(f"{method}:{url}")
        response_tracking_field = None

        if policy:
            if policy.is_response_tracking_enabled:
                response_tracking_field = policy.response_tracking_field

        if policy and policy.identity_field_name and policy.identity_field_location:
            result = self._extract_identity_from_location(policy.identity_field_name, policy.identity_field_location, request, method, url)
            if result:
                return result, policy.has_rate_limit, response_tracking_field

        # If no policy match, try config
        # config = self.client.get_config()
        # if config:
        #     field_name = config.get("identityFieldName")
        #     location = config.get("identityFieldLocation")
        #     if field_name and location:
        #         result = self._extract_identity_from_location(field_name, location, request, method, url)
        #         if result:
        #             return result

        # Fallback to default ledgerId
        return f"{method} {url}", False, response_tracking_field

def get_router_path(request: Request) -> Optional[str]:
    current_path = None
    for route in request.app.routes:
        if route.matches(request.scope):
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path
            elif match == Match.PARTIAL and current_path is None:
                current_path = route.path

    return current_path

__version__ = "0.3.4"
__all__ = ["UsageFlowMiddleware"]
