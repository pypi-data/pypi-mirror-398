# Authentication - Python SDK

The Python SDK keeps auth tokens and the authenticated record inside a local `AuthStore`. All services reuse the stored token on every request.

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
```

## Superusers / Admin API

```python
pb.collection("_superusers").auth_with_password(
    "admin@example.com",
    "password",
)
```

The `_superusers` collection is an auth collection, so you can call all `RecordService` auth helpers on it as well (`auth_refresh`, `request_password_reset`, etc.).

## Auth Collections

Authenticate with the collection that represents your end users:

```python
users = pb.collection("users")

auth_data = users.auth_with_password("demo@example.com", "secret123")
print(auth_data["token"])
print(pb.auth_store.record)  # automatically populated
```

### Refreshing Tokens

```python
if not pb.auth_store.is_valid():
    users.auth_refresh()
```

### Logout

```python
pb.auth_store.clear()
```

## OAuth2 Flow

`auth_with_oauth2` uses realtime callbacks to complete the flow without extra HTTP servers.

```python
def open_oauth_url(url: str) -> None:
    print("Visit:", url)

auth_data = users.auth_with_oauth2(
    "google",
    url_callback=open_oauth_url,
    scopes=["profile", "email"],
    create_data={"name": "Google User"},
)
```

If you already have the OAuth2 code/verifier pair (for example in server‑side code), call `auth_with_oauth2_code()`.

## OTP & MFA Helpers

```python
otp = users.request_otp("demo@example.com")
users.auth_with_otp(otp["otpId"], "123456")
```

MFA enforcement is configured per auth collection and is evaluated automatically by the backend.

## Password Reset & Verification

```python
users.request_password_reset("demo@example.com")
users.confirm_password_reset(token, "newpass", "newpass")

users.request_verification("demo@example.com")
users.confirm_verification(verification_token)

users.request_email_change("new@example.com")
users.confirm_email_change(change_token, "currentPassword")
```

## Auth Store

`pb.auth_store` exposes:

- `token`: the current JWT
- `record`: the current auth record (or `None`)
- `is_valid()`: quick expiry check
- `save(new_token, record)`
- `clear()`

You can also instantiate the client with a custom store:

```python
from bosbase import BosBase, AuthStore

class MemoryStore(AuthStore):
    pass  # override save/clear if you want to hook external persistence

pb = BosBase("http://127.0.0.1:8090", auth_store=MemoryStore())
```

## Impersonation

Superusers can generate short-lived tokens for another auth collection:

```python
customer_client = users.impersonate("CUSTOMER_ID", duration=600)
customer_profile = customer_client.collection("profiles").get_first_list_item(
    "user = {:id}", {"id": customer_client.auth_store.record["id"]}
)
```

## Tips

- Store tokens in memory when running inside trusted server environments.
- When exposing the SDK in desktop/CLI apps, wrap `pb.auth_store` with encrypted storage.
- Use `pb.auth_store.on_change` style hooks by building your own store subclass that notifies the UI whenever `save()` or `clear()` is called.

## Detailed Examples

### Example 1: Complete Authentication Flow with Error Handling

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("http://localhost:8090")

def authenticate_user(email: str, password: str):
    """Authenticate user with password, handling MFA if required."""
    try:
        # Try password authentication
        auth_data = pb.collection("users").auth_with_password(email, password)
        
        print(f"Successfully authenticated: {auth_data['record']['email']}")
        return auth_data
        
    except ClientResponseError as err:
        # Check if MFA is required
        if err.status == 401 and err.response and err.response.get("mfaId"):
            print("MFA required, proceeding with second factor...")
            return handle_mfa(email, err.response["mfaId"])
        
        # Handle other errors
        if err.status == 400:
            raise ValueError("Invalid credentials")
        elif err.status == 403:
            raise ValueError("Password authentication is not enabled for this collection")
        else:
            raise

def handle_mfa(email: str, mfa_id: str):
    """Handle multi-factor authentication flow."""
    # Request OTP for second factor
    otp_result = pb.collection("users").request_otp(email)
    
    # In a real app, show a modal/form for the user to enter OTP
    # For this example, we'll simulate getting the OTP
    user_entered_otp = get_user_otp_input()  # Your UI function
    
    try:
        # Authenticate with OTP and MFA ID
        auth_data = pb.collection("users").auth_with_otp(
            otp_result["otpId"],
            user_entered_otp,
            body={"mfaId": mfa_id}
        )
        
        print("MFA authentication successful")
        return auth_data
    except ClientResponseError as err:
        if err.status == 429:
            raise ValueError("Too many OTP attempts, please request a new OTP")
        raise ValueError("Invalid OTP code")

def get_user_otp_input() -> str:
    """Simulate getting OTP from user input."""
    # In a real application, this would prompt the user
    return input("Enter OTP code: ")

# Usage
try:
    authenticate_user("user@example.com", "password123")
    print("User is authenticated:", pb.auth_store.record)
except ValueError as e:
    print(f"Authentication failed: {e}")
```

### Example 2: OAuth2 Integration

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError

pb = BosBase("https://your-domain.com")

def handle_oauth2_login(provider_name: str):
    """Handle OAuth2 login flow."""
    try:
        # Check available providers first
        auth_methods = pb.collection("users").list_auth_methods()
        
        if not auth_methods.get("oauth2", {}).get("enabled"):
            print("OAuth2 is not enabled for this collection")
            return
        
        providers = auth_methods.get("oauth2", {}).get("providers", [])
        google_provider = next((p for p in providers if p["name"] == "google"), None)
        
        if not google_provider:
            print("Google OAuth2 is not configured")
            return
        
        # Authenticate with Google
        def open_browser(url: str):
            print(f"Please visit: {url}")
            # In a real app, you might use webbrowser.open(url)
            import webbrowser
            webbrowser.open(url)
        
        auth_data = pb.collection("users").auth_with_oauth2(
            "google",
            url_callback=open_browser,
            scopes=["profile", "email"]
        )
        
        # Check if this is a new user
        if auth_data.get("meta", {}).get("isNew"):
            print("Welcome new user!", auth_data["record"])
            # Redirect to onboarding
            # redirect_to_onboarding()
        else:
            print("Welcome back!", auth_data["record"])
            # Redirect to dashboard
            # redirect_to_dashboard()
        
    except ClientResponseError as err:
        if err.status == 403:
            print("OAuth2 authentication is not enabled")
        else:
            print(f"OAuth2 authentication failed: {err}")
```

### Example 3: Token Management and Refresh

> **BosBase note:** Calls to `pb.collection("users").auth_with_password()` now return static, non-expiring tokens. Environment variables can no longer shorten their lifetime, so the refresh logic below is only required for custom auth collections, impersonation flows, or any token you mint manually.

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError
import base64
import json
import threading
import time

pb = BosBase("http://localhost:8090")

def check_auth() -> bool:
    """Check if user is already authenticated."""
    if pb.auth_store.is_valid():
        print(f"User is authenticated: {pb.auth_store.record.get('email')}")
        
        try:
            # Verify token is still valid and refresh if needed
            pb.collection("users").auth_refresh()
            print("Token refreshed successfully")
            return True
        except ClientResponseError:
            print("Token expired or invalid, clearing auth")
            pb.auth_store.clear()
            return False
    return False

def setup_auto_refresh():
    """Auto-refresh token before expiration."""
    if not pb.auth_store.is_valid():
        return
    
    # Calculate time until token expiration (JWT tokens have exp claim)
    token = pb.auth_store.token
    if not token:
        return
    
    try:
        # Decode JWT payload
        parts = token.split(".")
        if len(parts) < 2:
            return
        
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        expires_at = payload.get("exp", 0) * 1000  # Convert to milliseconds
        now = int(time.time() * 1000)
        time_until_expiry = expires_at - now
        
        # Refresh 5 minutes before expiration
        refresh_time = max(0, time_until_expiry - 5 * 60 * 1000)
        
        def refresh():
            time.sleep(refresh_time / 1000.0)
            try:
                pb.collection("users").auth_refresh()
                print("Token auto-refreshed")
                setup_auto_refresh()  # Schedule next refresh
            except Exception as e:
                print(f"Auto-refresh failed: {e}")
                pb.auth_store.clear()
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
    except Exception as e:
        print(f"Error setting up auto-refresh: {e}")

# Usage
if check_auth():
    setup_auto_refresh()
else:
    # Redirect to login
    print("Please log in")
```

### Example 4: Admin Impersonation for Support

```python
from bosbase import BosBase

pb = BosBase("http://localhost:8090")

def impersonate_user_for_support(user_id: str):
    """Impersonate a user for support purposes."""
    # Authenticate as admin
    pb.collection("_superusers").auth_with_password("admin@example.com", "adminpassword")
    
    # Impersonate the user (1 hour token)
    user_client = pb.collection("users").impersonate(user_id, duration=3600)
    
    print(f"Impersonating user: {user_client.auth_store.record.get('email')}")
    
    # Use the impersonated client to test user experience
    user_records = user_client.collection("posts").get_full_list()
    print(f"User can see {len(user_records)} posts")
    
    # Check what the user sees
    user_view = user_client.collection("posts").get_list(
        page=1,
        per_page=10,
        query={"filter": 'published = true'}
    )
    
    return {
        "can_access": len(user_view["items"]),
        "total_posts": len(user_records)
    }

# Usage in support dashboard
try:
    result = impersonate_user_for_support("user_record_id")
    print("User access check:", result)
except Exception as e:
    print(f"Impersonation failed: {e}")
```

### Example 5: API Key Generation for Server-to-Server

```python
from bosbase import BosBase
from datetime import datetime, timedelta
import os

pb = BosBase("https://api.example.com")

def generate_api_key(admin_email: str, admin_password: str):
    """Generate a long-lived API key for server-to-server communication."""
    # Authenticate as admin
    pb.collection("_superusers").auth_with_password(admin_email, admin_password)
    
    # Get superuser ID
    admin_record = pb.auth_store.record
    
    # Generate impersonation token (1 year duration for long-lived API key)
    api_client = pb.collection("_superusers").impersonate(admin_record["id"], duration=31536000)
    
    api_key = {
        "token": api_client.auth_store.token,
        "expires_at": (datetime.now() + timedelta(seconds=31536000)).isoformat(),
        "generated_at": datetime.now().isoformat()
    }
    
    # Store API key securely (e.g., in environment variables, secret manager)
    print(f"API Key generated (store securely): {api_key['token'][:20]}...")
    
    return api_key

# Usage in server environment
try:
    api_key = generate_api_key("admin@example.com", "securepassword")
    # Store in your server configuration
    os.environ["BOSBASE_API_KEY"] = api_key["token"]
except Exception as e:
    print(f"Failed to generate API key: {e}")

# Using the API key in another service
from bosbase import BosBase, AuthStore

service_client = BosBase("https://api.example.com")
service_client.auth_store.save(
    os.environ["BOSBASE_API_KEY"],
    {
        "id": "superuser_id",
        "email": "admin@example.com"
    }
)

# Make authenticated requests
data = service_client.collection("records").get_full_list()
```

### Example 6: OAuth2 Manual Flow (Advanced)

```python
from bosbase import BosBase
from bosbase.exceptions import ClientResponseError
from urllib.parse import urlparse, parse_qs
import json

pb = BosBase("https://your-domain.com")

# In a real application, you would use a session store or database
# For this example, we'll use a simple dictionary
oauth2_state = {}

def get_oauth2_providers():
    """Get available OAuth2 providers."""
    auth_methods = pb.collection("users").list_auth_methods()
    return auth_methods.get("oauth2", {}).get("providers", [])

def initiate_oauth2_login(provider_name: str, redirect_url: str):
    """Initiate OAuth2 flow."""
    providers = get_oauth2_providers()
    provider = next((p for p in providers if p["name"] == provider_name), None)
    
    if not provider:
        raise ValueError(f"Provider {provider_name} not available")
    
    # Store provider info for verification
    oauth2_state[provider_name] = provider
    
    # In a real application, you would redirect to the provider's auth URL
    auth_url = provider["authURL"]
    print(f"Redirect to: {auth_url}")
    print(f"Redirect URL: {redirect_url}")
    
    # Return the auth URL and provider info for the application to handle
    return {
        "auth_url": auth_url,
        "provider": provider,
        "redirect_url": redirect_url
    }

def handle_oauth2_callback(code: str, state: str, provider_name: str, redirect_url: str):
    """Handle OAuth2 callback after redirect."""
    if not code or not state:
        raise ValueError("Missing OAuth2 parameters")
    
    # Retrieve stored provider info
    provider = oauth2_state.get(provider_name)
    if not provider:
        raise ValueError("Provider info not found")
    
    # Verify state parameter
    if provider.get("state") != state:
        raise ValueError("State parameter mismatch - possible CSRF attack")
    
    try:
        # Exchange code for token
        auth_data = pb.collection("users").auth_with_oauth2_code(
            provider_name,
            code,
            provider["codeVerifier"],
            redirect_url,
            body={
                # Optional: additional data for new users
                "emailVisibility": False
            }
        )
        
        print("OAuth2 authentication successful:", auth_data["record"])
        
        # Clear stored provider info
        del oauth2_state[provider_name]
        
        return auth_data
        
    except ClientResponseError as err:
        print(f"OAuth2 code exchange failed: {err}")
        raise ValueError("Authentication failed. Please try again.")

# Usage example (in a web framework like Flask/FastAPI)
# @app.route('/oauth2/login/<provider>')
# def oauth2_login(provider):
#     redirect_url = request.url_root + 'oauth2/callback'
#     info = initiate_oauth2_login(provider, redirect_url)
#     return redirect(info['auth_url'])
#
# @app.route('/oauth2/callback')
# def oauth2_callback():
#     code = request.args.get('code')
#     state = request.args.get('state')
#     provider = request.args.get('provider')
#     redirect_url = request.url_root + 'oauth2/callback'
#     auth_data = handle_oauth2_callback(code, state, provider, redirect_url)
#     return redirect('/dashboard')
```
