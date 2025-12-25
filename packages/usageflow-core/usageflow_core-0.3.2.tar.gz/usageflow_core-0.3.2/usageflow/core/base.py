import jwt
import threading
import time
import uuid
from typing import Dict, Any, Optional, Tuple, List
from usageflow.core.types import Policy,PolicyV2, UsageFlowSocketMessage
from usageflow.core.socket_manager import UsageFlowSocketManager
from usageflow.core.types import RoutesMap

class UsageFlowClient:
    def __init__(self, api_key: str, pool_size: int = 10):
        self.api_key = api_key
        self.api_config = None
        self.policies: List[Policy] = []
        self.policies_map: Dict[str, Policy] = {}
        self.lock = threading.Lock()
        self.socket_manager = UsageFlowSocketManager(api_key, pool_size)
        self.blocked_endpoints: Dict[str, bool] = {}
        self.whitelist_map: RoutesMap = {}
        self.monitor_map: RoutesMap = {}
        # Connection is explicit - call connect() when ready
        # Do NOT auto-connect in constructor to avoid immediate execution

    def connect(self):
        """Establish WebSocket connections"""
        self.socket_manager.connect()
        self.start_config_updater()

    def start_config_updater(self):
        """Background thread to periodically fetch API configuration"""
        def update_config():
            while True:
                try:
                    config = self.fetch_api_config()
                    self.fetch_application_config()
                    self.fetch_blocked_endpoints()
                    if config:
                        with self.lock:
                            self.api_config = config
                        with self.lock:
                            policies_rsp = self.fetch_api_policies()
                            policies = policies_rsp.get("data", {}).get("items", [])
                            if policies:
                                self.policies = [PolicyV2.from_json(policy) for policy in policies]  # No need for json.loads
                                self.policies_map = {f"{policy.endpoint_method}:{policy.endpoint_pattern}": policy for policy in self.policies}
                except Exception as e:
                    print(f"Error fetching API config: {e}")
                
                time.sleep(10)  # Refresh every 10 seconds

        thread = threading.Thread(target=update_config, daemon=True)
        thread.start()

    def fetch_api_config(self) -> Dict[str, Any]:
        """Fetch API configuration from UsageFlow"""
        if not self.socket_manager.is_connected():
            raise RuntimeError("WebSocket not connected. Call connect() first.")

        message = UsageFlowSocketMessage(
            type="get_application_policies",
            payload=None
        )

        response = self.socket_manager.send_async(message)

        if response.type == 'error':
            error_msg = response.message or response.error or "Unknown error"
            raise Exception(f"Failed to fetch API config: {error_msg}")

        return response.payload or {}


    def fetch_api_policies(self) -> Dict[str, Any]:
        """Fetch API policies from UsageFlow"""
        if not self.socket_manager.is_connected():
            raise RuntimeError("WebSocket not connected. Call connect() first.")

        message = UsageFlowSocketMessage(
            type="get_application_policies",
            payload=None
        )

        response = self.socket_manager.send_async(message)

        if response.type == 'error':
            error_msg = response.message or response.error or "Unknown error"
            raise Exception(f"Failed to fetch API policies: {error_msg}")

        if response.type == 'success':
            # Extract policies from response payload
            policies_data = response.payload or {}
            policies = policies_data.get("policies", [])
            return {"data": {"items": policies}, "total": policies_data.get("total", len(policies))}

        return {"data": {"items": []}, "total": 0}


    def allocate_request(self, ledger_id: str, metadata: Dict[str, Any], has_rate_limit: bool) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Allocate usage for a request"""
        if not self.socket_manager.is_connected():
            return False, {"error": "WebSocket not connected"}

        payload = {
            "alias": ledger_id,
            "amount": 1,
            "metadata": metadata,
        }


        if not has_rate_limit:
            payload["allocationId"] = str(uuid.uuid4())

        message = UsageFlowSocketMessage(
            type="request_for_allocation",
            payload=payload
        )

        try:
            if not has_rate_limit:
                self.socket_manager.send(message)
                return True, {"allocationId": payload["allocationId"]}

            response = self.socket_manager.send_async(message)

            if response.type == 'error':
                error_msg = response.message or response.error or "Unknown error"

                return False, {"error": error_msg, "status_code": 478}

            if response.type == 'success':
                return True, response.payload

            return False, {"error": "Unknown response type"}
        except TimeoutError:
            return False, {"error": "Request timed out"}
        except RuntimeError:
            return False, {"error": "Service unavailable"}
        except Exception as e:
            return False, {"error": str(e)}

    def fulfill_request(self, ledger_id: str, allocation_id: str, metadata: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Fulfill the request by finalizing usage"""
        if not self.socket_manager.is_connected():
            return True, None  # Fail silently if not connected

        payload = {
            "alias": ledger_id,
            "amount": 1,
            "allocationId": allocation_id,
            "metadata": metadata,
        }

        message = UsageFlowSocketMessage(
            type="use_allocation",
            payload=payload
        )

        try:
            self.socket_manager.send(message)
            return True, None
        except Exception:
            return True, None  # Fail silently

    def extract_bearer_token(self, auth_header: Optional[str]) -> Optional[str]:
        if not auth_header:
            return None
        parts = auth_header.split()
        return parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else None

    def decode_jwt_unverified(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.DecodeError:
            return None

    def transform_to_ledger_id(self, identifier: str) -> str:
        """Transform an identifier to a ledger ID format"""
        return str(identifier)

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get the current API configuration"""
        with self.lock:
            return self.api_config

    def get_policies(self) -> List[Policy]:
        """Get the current API policies"""
        with self.lock:
            return self.policies

    def get_policies_map(self) -> Dict[str, Policy]:
        """Get the current API policies map"""
        with self.lock:
            return self.policies_map


    def log_response(self, metadata: Dict[str, Any]) -> None:
        """Log the response details"""
        if not self.socket_manager.is_connected():
            return  # Fail silently if not connected

        message = UsageFlowSocketMessage(
            type="log_response",
            payload=metadata
        )

        try:
            # Use send() for fire-and-forget logging
            self.socket_manager.send(message)
        except Exception:
            pass  # Fail silently for logging

    def _create_routes_map(self, routes: List[Dict[str, Any]]) -> RoutesMap:
        """Create a routes map from a list of routes"""
        route_map: RoutesMap = {}

        for route in routes:
            # Handle both dict-like and object-like route structures
            method = route.get("method") if isinstance(route, dict) else getattr(route, "method", None)
            url = route.get("url") if isinstance(route, dict) else getattr(route, "url", None)

            if method and url:
                if method not in route_map:
                    route_map[method] = {}
                route_map[method][url] = True

        return route_map

    def fetch_application_config(self) -> None:
        """Fetch application configuration and update whitelist and monitor maps"""
        if not self.socket_manager.is_connected():
            return

        message = UsageFlowSocketMessage(
            type="get_application_config",
            payload=None
        )

        response = self.socket_manager.send_async(message)

        if response.type == "success":
            whitelist_endpoints = response.payload.get("whitelistEndpoints", []) if response.payload else []
            monitor_endpoints = response.payload.get("monitoringPaths", []) if response.payload else []

            with self.lock:
                self.whitelist_map = self._create_routes_map(whitelist_endpoints)
                self.monitor_map = self._create_routes_map(monitor_endpoints)

    def fetch_blocked_endpoints(self) -> None:
        """Fetch blocked endpoints and update blocked_endpoints list"""
        if not self.socket_manager.is_connected():
            return

        message = UsageFlowSocketMessage(
            type="get_blocked_endpoints",
            payload=None
        )

        response = self.socket_manager.send_async(message)

        if response.type == "success":
            endpoints = response.payload.get("endpoints", []) if response.payload else []

            with self.lock:
                self.blocked_endpoints = {
                    f"{endpoint.get('method', '')} {endpoint.get('url', '')}{f' {identity}' if (identity := endpoint.get('identity')) else ''}": True
                    for endpoint in endpoints
                }

    def _check_endpoint(self, endpointUrl: str, method: str, whitelist_check: bool = True) -> bool:
        """Check if an endpoint matches patterns in whitelist or monitor map"""
        route_map = self.whitelist_map if whitelist_check else self.monitor_map
        # methods_endpoints = route_map.get(method, {})
        for monitored_method in route_map.keys():
            url_dict = route_map.get(monitored_method, {})
            if monitored_method == '*':
                    return self._url_matching(url_dict, endpointUrl)
            elif monitored_method == method:
                return self._url_matching(url_dict, endpointUrl)
        return False

    def _url_matching(self,url_dict: Dict[str, bool], endpointUrl: str) -> bool:
        for url in url_dict.keys():
            if url == '*':
                return True
            if '*' in url and endpointUrl.startswith(url.replace('*', '')):
                return True
            if url == endpointUrl:
                return True
            return False

    def is_endpoint_whitelisted(self, endpointUrl: str, method: str) -> bool:
        """Check if an endpoint is whitelisted"""
        return self._check_endpoint(endpointUrl, method, whitelist_check=True)

    def is_endpoint_monitored(self, endpointUrl: str, method: str) -> bool:
        """Check if an endpoint is monitored"""
        return self._check_endpoint(endpointUrl, method, whitelist_check=False)
    
    def is_endpoint_blocked(self, endpoint_presentation: str) -> bool:
        """Check if an endpoint is blocked"""
        return self.blocked_endpoints.get(endpoint_presentation, False)