from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from usageflow.core import UsageFlowClient
import time
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

        # Post-processing (After Request)
        await self._after_request(request, response, start_time)

        return response

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

        request.state.metadata = metadata
        ledger_id, has_rate_limit = self._guess_ledger_id(request)

        # Check if url is blocked
        if self.client.is_endpoint_blocked(ledger_id):
            return {
                "blocked": True,
                "error": "Endpoint blocked",
                "status_code": 403,
            }

        # Allocate request
        success, result = self.client.allocate_request(ledger_id, metadata, has_rate_limit)

        if not success:
            error_message = result.get('error', 'Request fulfillment failed') if result else 'Request fulfillment failed'
            status_code = result.get('status_code', 500) if result else 500

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

    async def _after_request(self, request: Request, response: Response, start_time: float):
        """Handle logic after the request has been processed."""
        if hasattr(request.state, "event_id") and request.state.event_id:
            metadata = getattr(request.state, "metadata", {})
            metadata.update({
                "responseStatusCode": response.status_code,
                "responseHeaders": dict(response.headers),
                "requestDuration": int((time.time() - start_time) * 1000),
            })

            self.client.fulfill_request(request.state.ledger_id, request.state.event_id, metadata)

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

        return None

    def _guess_ledger_id(self, request: Request) -> Tuple[str, bool]:
        """Determine the ledger ID from the request"""
        method = request.method
        url = get_router_path(request)

        # Try to get identity from policies first
        policies_map = self.client.get_policies_map()
        policy = policies_map.get(f"{method}:{url}")
        if policy and policy.identity_field_name and policy.identity_field_location:
            result = self._extract_identity_from_location(policy.identity_field_name, policy.identity_field_location, request, method, url)
            if result:
                return result, policy.has_rate_limit

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
        return f"{method} {url}", False

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

__version__ = "0.3.2"
__all__ = ["UsageFlowMiddleware"]
