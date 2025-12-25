"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Advanced Authentication Providers for Enterprise Integration

Provides enterprise authentication mechanisms:
- OAuth2 (Authorization Code, Client Credentials, Resource Owner)
- JWT (JSON Web Tokens) with RS256/HS256
- SAML 2.0 integration
- Multi-factor authentication support
- Token refresh and validation
"""

import json
import time
import base64
import hashlib
import hmac
from typing import Any, Optional, Union
from urllib.parse import urlencode, parse_qs
from .base import AAuthProvider, ATokenInfo, AUserInfo
from .errors import AuthenticationError, AuthorizationError, TokenExpiredError
from .defs import OAuth2GrantType

from ..config.logging_setup import get_logger

# Lazy imports to avoid import errors during test collection
# These are only imported when actually needed
def _get_jwt():
    """Lazy import jwt module."""
    try:
        import jwt
        return jwt
    except ImportError:
        raise ImportError(
            "PyJWT is required for JWT authentication. "
            "Install it with: pip install PyJWT"
        )

def _get_requests():
    """Lazy import requests module."""
    try:
        import requests
        return requests
    except ImportError:
        raise ImportError(
            "requests is required for OAuth2 authentication. "
            "Install it with: pip install requests"
        )

logger = get_logger("xwsystem.security.auth")


class OAuth2Provider(AAuthProvider):
    """OAuth2 authentication provider."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        userinfo_url: Optional[str] = None,
        scopes: Optional[list[str]] = None
    ):
        """
        Initialize OAuth2 provider.
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            authorization_url: Authorization endpoint URL
            token_url: Token endpoint URL
            userinfo_url: Optional user info endpoint URL
            scopes: Optional list of scopes to request
        """
        # requests is now required
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.scopes = scopes or []
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get authorization URL for OAuth2 flow."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes)
        }
        
        if state:
            params['state'] = state
        
        return f"{self.authorization_url}?{urlencode(params)}"
    
    async def authenticate(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Authenticate using OAuth2 flow."""
        import asyncio
        
        def _authenticate():
            grant_type = credentials.get('grant_type', OAuth2GrantType.AUTHORIZATION_CODE.value)
            
            if grant_type == OAuth2GrantType.AUTHORIZATION_CODE.value:
                return self._authenticate_authorization_code(credentials)
            elif grant_type == OAuth2GrantType.CLIENT_CREDENTIALS.value:
                return self._authenticate_client_credentials()
            elif grant_type == OAuth2GrantType.RESOURCE_OWNER.value:
                return self._authenticate_resource_owner(credentials)
            else:
                raise AuthenticationError(f"Unsupported grant type: {grant_type}")
        
        return await asyncio.to_thread(_authenticate)
    
    def _authenticate_authorization_code(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Authenticate using authorization code."""
        requests = _get_requests()
        data = {
            'grant_type': OAuth2GrantType.AUTHORIZATION_CODE.value,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': credentials['code'],
            'redirect_uri': credentials['redirect_uri']
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(f"OAuth2 authentication failed: {response.text}")
        
        token_data = response.json()
        return ATokenInfo(
            access_token=token_data['access_token'],
            token_type=token_data.get('token_type', 'Bearer'),
            expires_in=token_data.get('expires_in'),
            refresh_token=token_data.get('refresh_token'),
            scope=token_data.get('scope')
        )
    
    def _authenticate_client_credentials(self) -> ATokenInfo:
        """Authenticate using client credentials."""
        requests = _get_requests()
        data = {
            'grant_type': OAuth2GrantType.CLIENT_CREDENTIALS.value,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(f"OAuth2 authentication failed: {response.text}")
        
        token_data = response.json()
        return ATokenInfo(
            access_token=token_data['access_token'],
            token_type=token_data.get('token_type', 'Bearer'),
            expires_in=token_data.get('expires_in'),
            scope=token_data.get('scope')
        )
    
    def _authenticate_resource_owner(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Authenticate using resource owner credentials."""
        requests = _get_requests()
        data = {
            'grant_type': OAuth2GrantType.RESOURCE_OWNER.value,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': credentials['username'],
            'password': credentials['password'],
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(f"OAuth2 authentication failed: {response.text}")
        
        token_data = response.json()
        return ATokenInfo(
            access_token=token_data['access_token'],
            token_type=token_data.get('token_type', 'Bearer'),
            expires_in=token_data.get('expires_in'),
            refresh_token=token_data.get('refresh_token'),
            scope=token_data.get('scope')
        )
    
    async def validate_token(self, token: str) -> AUserInfo:
        """Validate OAuth2 token."""
        if not self.userinfo_url:
            raise AuthenticationError("User info URL not configured")
        
        import asyncio
        
        def _validate():
            requests = _get_requests()
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(self.userinfo_url, headers=headers)
            
            if response.status_code == 401:
                raise TokenExpiredError("Token expired or invalid")
            elif response.status_code != 200:
                raise AuthenticationError(f"Token validation failed: {response.text}")
            
            user_data = response.json()
            return AUserInfo(
                user_id=user_data.get('sub', user_data.get('id', 'unknown')),
                username=user_data.get('preferred_username', user_data.get('username')),
                email=user_data.get('email'),
                attributes=user_data
            )
        
        return await asyncio.to_thread(_validate)
    
    async def refresh_token(self, refresh_token: str) -> ATokenInfo:
        """Refresh OAuth2 token."""
        import asyncio
        
        def _refresh():
            requests = _get_requests()
            data = {
                'grant_type': OAuth2GrantType.REFRESH_TOKEN.value,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code != 200:
                raise AuthenticationError(f"Token refresh failed: {response.text}")
            
            token_data = response.json()
            return ATokenInfo(
                access_token=token_data['access_token'],
                token_type=token_data.get('token_type', 'Bearer'),
                expires_in=token_data.get('expires_in'),
                refresh_token=token_data.get('refresh_token', refresh_token),
                scope=token_data.get('scope')
            )
        
        return await asyncio.to_thread(_refresh)


class JWTProvider(AAuthProvider):
    """JWT (JSON Web Token) authentication provider."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        expiration_time: int = 3600
    ):
        """
        Initialize JWT provider.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (HS256, RS256, etc.)
            issuer: Token issuer
            audience: Token audience
            expiration_time: Token expiration time in seconds
        """
        # PyJWT is now required
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.expiration_time = expiration_time
    
    async def authenticate(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Create JWT token from user credentials."""
        import asyncio
        
        def _authenticate():
            jwt = _get_jwt()
            # In a real implementation, you'd validate credentials against a database
            user_id = credentials.get('user_id')
            if not user_id:
                raise AuthenticationError("user_id required for JWT authentication")
            
            now = time.time()
            payload = {
                'sub': user_id,
                'iat': now,
                'exp': now + self.expiration_time,
                **{k: v for k, v in credentials.items() if k not in ['user_id', 'password']}
            }
            
            if self.issuer:
                payload['iss'] = self.issuer
            if self.audience:
                payload['aud'] = self.audience
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            return ATokenInfo(
                access_token=token,
                token_type="Bearer",
                expires_in=self.expiration_time
            )
        
        return await asyncio.to_thread(_authenticate)
    
    async def validate_token(self, token: str) -> AUserInfo:
        """Validate JWT token."""
        import asyncio
        
        def _validate():
            jwt = _get_jwt()
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    issuer=self.issuer,
                    audience=self.audience
                )
                
                return AUserInfo(
                    user_id=payload['sub'],
                    username=payload.get('username'),
                    email=payload.get('email'),
                    roles=payload.get('roles', []),
                    attributes=payload
                )
                
            except jwt.ExpiredSignatureError:
                raise TokenExpiredError("JWT token has expired")
            except jwt.InvalidTokenError as e:
                raise AuthenticationError(f"Invalid JWT token: {e}")
        
        return await asyncio.to_thread(_validate)
    
    async def refresh_token(self, refresh_token: str) -> ATokenInfo:
        """Refresh JWT token (create new token from existing)."""
        jwt = _get_jwt()
        try:
            # Validate existing token (ignore expiration for refresh)
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            # Create new token with same payload but new timestamps
            now = time.time()
            payload.update({
                'iat': now,
                'exp': now + self.expiration_time
            })
            
            new_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            return ATokenInfo(
                access_token=new_token,
                token_type="Bearer",
                expires_in=self.expiration_time
            )
            
        except Exception as e:
            jwt_module = _get_jwt()
            if isinstance(e, jwt_module.InvalidTokenError):
                raise AuthenticationError(f"Invalid refresh token: {e}")
            raise


class SAMLProvider(AAuthProvider):
    """SAML 2.0 authentication provider (simplified implementation)."""
    
    def __init__(
        self,
        idp_url: str,
        sp_entity_id: str,
        certificate_path: Optional[str] = None
    ):
        """
        Initialize SAML provider.
        
        Args:
            idp_url: Identity Provider URL
            sp_entity_id: Service Provider entity ID
            certificate_path: Path to IdP certificate for validation
        """
        self.idp_url = idp_url
        self.sp_entity_id = sp_entity_id
        self.certificate_path = certificate_path
        
        logger.warning("SAML provider is a simplified implementation. Use a full SAML library for production.")
    
    async def authenticate(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Authenticate using SAML (simplified)."""
        # This is a placeholder implementation
        # In practice, you'd use a library like python3-saml
        raise AuthenticationError("SAML authentication requires a full SAML library implementation")
    
    async def validate_token(self, token: str) -> AUserInfo:
        """Validate SAML token (simplified)."""
        # This is a placeholder implementation
        raise AuthenticationError("SAML token validation requires a full SAML library implementation")
    
    async def refresh_token(self, refresh_token: str) -> ATokenInfo:
        """SAML doesn't typically support token refresh."""
        raise AuthenticationError("SAML does not support token refresh")
    
    def get_login_url(self, return_url: str) -> str:
        """Get SAML login URL."""
        # This would generate a proper SAML AuthnRequest
        params = {
            'SAMLRequest': base64.b64encode(f'<saml:AuthnRequest><saml:Issuer>{self.sp_entity_id}</saml:Issuer></saml:AuthnRequest>'.encode()).decode(),
            'RelayState': return_url
        }
        
        return f"{self.idp_url}?{urlencode(params)}"


class EnterpriseAuth:
    """Enterprise authentication manager."""
    
    def __init__(self):
        self._providers = {}
        self._active_provider = None
    
    def add_provider(self, name: str, provider: AAuthProvider):
        """Add authentication provider."""
        self._providers[name] = provider
    
    def set_active_provider(self, name: str):
        """Set active authentication provider."""
        if name not in self._providers:
            raise AuthenticationError(f"Provider '{name}' not found")
        self._active_provider = name
    
    def get_provider(self, name: Optional[str] = None) -> AAuthProvider:
        """Get authentication provider."""
        if name is None:
            name = self._active_provider
        
        if name is None:
            raise AuthenticationError("No active provider set")
        
        if name not in self._providers:
            raise AuthenticationError(f"Provider '{name}' not found")
        
        return self._providers[name]
    
    async def authenticate(self, credentials: dict[str, Any], provider: Optional[str] = None) -> ATokenInfo:
        """Authenticate using specified or active provider."""
        provider_instance = self.get_provider(provider)
        return await provider_instance.authenticate(credentials)
    
    async def validate_token(self, token: str, provider: Optional[str] = None) -> AUserInfo:
        """Validate token using specified or active provider."""
        provider_instance = self.get_provider(provider)
        return await provider_instance.validate_token(token)
    
    async def refresh_token(self, refresh_token: str, provider: Optional[str] = None) -> ATokenInfo:
        """Refresh token using specified or active provider."""
        provider_instance = self.get_provider(provider)
        return await provider_instance.refresh_token(refresh_token)
    
    def list_providers(self) -> list[str]:
        """List available providers."""
        return list(self._providers.keys())
    
    def remove_provider(self, name: str):
        """Remove authentication provider."""
        if name in self._providers:
            del self._providers[name]
            if self._active_provider == name:
                self._active_provider = None

