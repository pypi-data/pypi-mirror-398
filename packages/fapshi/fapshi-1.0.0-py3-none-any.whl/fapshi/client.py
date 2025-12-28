"""Main client for the Fapshi Payment API."""

from typing import Optional, Dict, List, Union, Any
import requests

from fapshi.utils import (
    get_base_url,
    validate_user_id,
    validate_external_id,
    validate_amount,
    validate_email,
    normalize_phone,
)
from fapshi.exceptions import (
    FapshiAPIError,
    FapshiValidationError,
    FapshiAuthenticationError,
)
from fapshi.models import (
    Transaction,
    PaymentResponse,
    BalanceResponse,
    ErrorResponse,
)


class FapshiClient:
    """
    Client for interacting with the Fapshi Payment API.
    
    Automatically detects the environment (sandbox or live) based on the API key format.
    - Sandbox API keys start with 'FAK_TEST_'
    - Live API keys start with 'FAK_' (but not 'FAK_TEST_')
    
    Args:
        api_user: Your Fapshi API user
        api_key: Your Fapshi API key (sandbox: FAK_TEST_xxx, live: FAK_xxx)
        base_url: Optional base URL override (auto-detected if not provided)
    """
    
    def __init__(
        self,
        api_user: str,
        api_key: str,
        base_url: Optional[str] = None,
    ):
        if not api_user:
            raise FapshiValidationError("api_user is required")
        if not api_key:
            raise FapshiValidationError("api_key is required")
        
        # Validate API key format
        try:
            detected_base_url = get_base_url(api_key)
        except ValueError as e:
            raise FapshiValidationError(str(e))
        
        self.api_user = api_user
        self.api_key = api_key
        self.base_url = base_url or detected_base_url
        
        self.session = requests.Session()
        self.session.headers.update({
            "apiuser": self.api_user,
            "apikey": self.api_key,
            "Content-Type": "application/json",
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_models: bool = False,
    ) -> Union[Dict, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST requests)
            params: Query parameters (for GET requests)
            use_models: If True, return model instances instead of dicts
            
        Returns:
            Response data as dict or model instance
            
        Raises:
            FapshiAPIError: For API errors
            FapshiAuthenticationError: For authentication failures
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise FapshiAuthenticationError(
                    "Authentication failed. Please check your API credentials."
                )
            
            # Parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"message": response.text}
            
            # Handle error responses (4XX)
            if 400 <= response.status_code < 500:
                error_msg = response_data.get("message", "API error occurred")
                raise FapshiAPIError(
                    error_msg,
                    status_code=response.status_code,
                    response_data=response_data,
                )
            
            # Handle server errors (5XX)
            if response.status_code >= 500:
                error_msg = response_data.get("message", "Server error occurred")
                raise FapshiAPIError(
                    error_msg,
                    status_code=response.status_code,
                    response_data=response_data,
                )
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise FapshiAPIError(f"Request failed: {str(e)}")
    
    def initiate_pay(
        self,
        amount: int,
        email: Optional[str] = None,
        redirect_url: Optional[str] = None,
        user_id: Optional[str] = None,
        external_id: Optional[str] = None,
        message: Optional[str] = None,
        use_models: bool = False,
    ) -> Union[Dict, PaymentResponse]:
        """
        Generate a payment link where users complete payment on a Fapshi-hosted page.
        
        Args:
            amount: Payment amount (minimum 100)
            email: Customer email (optional)
            redirect_url: URL to redirect to after payment (optional)
            user_id: User ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            external_id: External ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            message: Payment message (optional)
            use_models: If True, return PaymentResponse model instead of dict
            
        Returns:
            Payment response with link, transId, etc.
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if not validate_amount(amount):
            raise FapshiValidationError("Amount must be an integer >= 100")
        
        if email and not validate_email(email):
            raise FapshiValidationError("Invalid email format")
        
        if user_id and not validate_user_id(user_id):
            raise FapshiValidationError(
                "user_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        if external_id and not validate_external_id(external_id):
            raise FapshiValidationError(
                "external_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        data = {"amount": amount}
        if email:
            data["email"] = email
        if redirect_url:
            data["redirectUrl"] = redirect_url
        if user_id:
            data["userId"] = user_id
        if external_id:
            data["externalId"] = external_id
        if message:
            data["message"] = message
        
        response = self._make_request("POST", "/initiate-pay", data=data)
        
        if use_models:
            return PaymentResponse.from_dict(response)
        return response
    
    def direct_pay(
        self,
        amount: int,
        phone: str,
        medium: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        external_id: Optional[str] = None,
        message: Optional[str] = None,
        use_models: bool = False,
    ) -> Union[Dict, PaymentResponse]:
        """
        Initiate a direct payment request to a user's mobile device.
        
        Args:
            amount: Payment amount (minimum 100)
            phone: User's phone number (required, must start with 6, without country code 237)
            medium: Payment medium - "mobile money" or "orange money" (optional)
            name: Payer name (optional)
            email: Customer email (optional)
            user_id: User ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            external_id: External ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            message: Payment message (optional)
            use_models: If True, return PaymentResponse model instead of dict
            
        Returns:
            Payment response with transId, etc.
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if not validate_amount(amount):
            raise FapshiValidationError("Amount must be an integer >= 100")
        
        if not phone:
            raise FapshiValidationError("phone is required")
        
        # Normalize phone number (remove 237 country code if present)
        try:
            phone = normalize_phone(phone)
        except ValueError as e:
            raise FapshiValidationError(str(e))
        
        if email and not validate_email(email):
            raise FapshiValidationError("Invalid email format")
        
        if user_id and not validate_user_id(user_id):
            raise FapshiValidationError(
                "user_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        if external_id and not validate_external_id(external_id):
            raise FapshiValidationError(
                "external_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        if medium and medium not in ["mobile money", "orange money"]:
            raise FapshiValidationError(
                'medium must be "mobile money" or "orange money"'
            )
        
        data = {"amount": amount, "phone": phone}
        if medium:
            data["medium"] = medium
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        if user_id:
            data["userId"] = user_id
        if external_id:
            data["externalId"] = external_id
        if message:
            data["message"] = message
        
        response = self._make_request("POST", "/direct-pay", data=data)
        
        if use_models:
            return PaymentResponse.from_dict(response)
        return response
    
    def get_payment_status(
        self,
        trans_id: str,
        use_models: bool = False,
    ) -> Union[Dict, Transaction]:
        """
        Retrieve the status of a payment by transaction ID.
        
        Args:
            trans_id: Transaction ID
            use_models: If True, return Transaction model instead of dict
            
        Returns:
            Single transaction object
            
        Raises:
            FapshiAPIError: For API errors
        """
        if not trans_id:
            raise FapshiValidationError("trans_id is required")
        
        response = self._make_request("GET", f"/payment-status/{trans_id}")
        
        # API returns a single transaction object
        if use_models:
            return Transaction.from_dict(response)
        return response
    
    def expire_pay(
        self,
        trans_id: str,
        use_models: bool = False,
    ) -> Union[Dict, Transaction]:
        """
        Invalidate a payment link to prevent further payments.
        
        Args:
            trans_id: Transaction ID to expire
            use_models: If True, return Transaction model instead of dict
            
        Returns:
            Transaction with status "EXPIRED"
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if not trans_id:
            raise FapshiValidationError("trans_id is required")
        
        data = {"transId": trans_id}
        response = self._make_request("POST", "/expire-pay", data=data)
        
        if use_models:
            return Transaction.from_dict(response)
        return response
    
    def get_transactions_by_user(
        self,
        user_id: str,
        use_models: bool = False,
    ) -> Union[List[Dict], List[Transaction]]:
        """
        Retrieve all transactions associated with a user ID.
        
        Args:
            user_id: User ID (format: ^[a-zA-Z0-9\\-_]{1,100}$)
            use_models: If True, return Transaction models instead of dicts
            
        Returns:
            List of transactions
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if not validate_user_id(user_id):
            raise FapshiValidationError(
                "user_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        response = self._make_request("GET", f"/transaction/{user_id}")
        
        # API returns Transaction[] (array)
        if isinstance(response, dict):
            transactions = [response]
        else:
            transactions = response
        
        if use_models:
            return [Transaction.from_dict(t) for t in transactions]
        return transactions
    
    def search_transactions(
        self,
        status: Optional[str] = None,
        medium: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        amt: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
        use_models: bool = False,
    ) -> Union[List[Dict], List[Transaction]]:
        """
        Search transactions by filters.
        
        Args:
            status: Transaction status - "created", "successful", "failed", or "expired" (optional)
            medium: Payment medium - "mobile money" or "orange money" (optional)
            start: Start date (YYYY-MM-DD) (optional)
            end: End date (YYYY-MM-DD) (optional)
            amt: Amount filter (optional)
            limit: Result limit (1-100, default 10) (optional)
            sort: Sort order - "asc" or "desc" (default "desc") (optional)
            use_models: If True, return Transaction models instead of dicts
            
        Returns:
            List of transactions
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if status and status not in ["created", "successful", "failed", "expired"]:
            raise FapshiValidationError(
                'status must be one of: "created", "successful", "failed", "expired"'
            )
        
        if medium and medium not in ["mobile money", "orange money"]:
            raise FapshiValidationError(
                'medium must be "mobile money" or "orange money"'
            )
        
        if limit is not None and (limit < 1 or limit > 100):
            raise FapshiValidationError("limit must be between 1 and 100")
        
        if sort and sort not in ["asc", "desc"]:
            raise FapshiValidationError('sort must be "asc" or "desc"')
        
        params = {}
        if status:
            params["status"] = status
        if medium:
            params["medium"] = medium
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if amt is not None:
            params["amt"] = amt
        if limit is not None:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        
        response = self._make_request("GET", "/search", params=params)
        
        # API returns Transaction[] (array)
        if isinstance(response, dict):
            transactions = [response]
        else:
            transactions = response
        
        if use_models:
            return [Transaction.from_dict(t) for t in transactions]
        return transactions
    
    def get_balance(
        self,
        use_models: bool = False,
    ) -> Union[Dict, BalanceResponse]:
        """
        Get the current service balance.
        
        Args:
            use_models: If True, return BalanceResponse model instead of dict
            
        Returns:
            Balance information (service, balance, currency)
            
        Raises:
            FapshiAPIError: For API errors
        """
        response = self._make_request("GET", "/balance")
        
        if use_models:
            return BalanceResponse.from_dict(response)
        return response
    
    def payout(
        self,
        amount: int,
        phone: Optional[str] = None,
        medium: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        external_id: Optional[str] = None,
        message: Optional[str] = None,
        use_models: bool = False,
    ) -> Union[Dict, PaymentResponse]:
        """
        Make a payout to a user's mobile money, orange money, or fapshi account.
        
        Conditional requirements:
        - If medium is not specified: amount and phone are required.
        - If medium = "fapshi": amount and email are required.
        
        Args:
            amount: Payout amount (minimum 100)
            phone: User's phone number (conditional - required if medium not "fapshi", must start with 6, without country code 237)
            medium: Payout medium - "mobile money", "orange money", or "fapshi" (optional)
            name: Recipient name (optional)
            email: Recipient email (conditional - required if medium = "fapshi")
            user_id: User ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            external_id: External ID (optional, format: ^[a-zA-Z0-9\\-_]{1,100}$)
            message: Payout message (optional)
            use_models: If True, return PaymentResponse model instead of dict
            
        Returns:
            Payout response with transId, etc.
            
        Raises:
            FapshiValidationError: For validation errors
            FapshiAPIError: For API errors
        """
        if not validate_amount(amount):
            raise FapshiValidationError("Amount must be an integer >= 100")
        
        # Validate conditional requirements
        if medium == "fapshi":
            if not email:
                raise FapshiValidationError(
                    "email is required when medium is 'fapshi'"
                )
        else:
            if not phone:
                raise FapshiValidationError(
                    "phone is required when medium is not 'fapshi'"
                )
            
            # Normalize phone number (remove 237 country code if present)
            try:
                phone = normalize_phone(phone)
            except ValueError as e:
                raise FapshiValidationError(str(e))
        
        if email and not validate_email(email):
            raise FapshiValidationError("Invalid email format")
        
        if user_id and not validate_user_id(user_id):
            raise FapshiValidationError(
                "user_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        if external_id and not validate_external_id(external_id):
            raise FapshiValidationError(
                "external_id must match pattern: ^[a-zA-Z0-9\\-_]{1,100}$"
            )
        
        if medium and medium not in ["mobile money", "orange money", "fapshi"]:
            raise FapshiValidationError(
                'medium must be "mobile money", "orange money", or "fapshi"'
            )
        
        data = {"amount": amount}
        if phone:
            # Phone is already normalized above
            data["phone"] = phone
        if medium:
            data["medium"] = medium
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        if user_id:
            data["userId"] = user_id
        if external_id:
            data["externalId"] = external_id
        if message:
            data["message"] = message
        
        response = self._make_request("POST", "/payout", data=data)
        
        if use_models:
            return PaymentResponse.from_dict(response)
        return response

