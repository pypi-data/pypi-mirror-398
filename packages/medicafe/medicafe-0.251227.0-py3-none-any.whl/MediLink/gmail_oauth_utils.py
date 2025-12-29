import json, os, time, requests

# Google OAuth API endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"


def get_authorization_url(credentials_path, redirect_uri, scopes, log):
    """
    Build the Google OAuth authorization URL using the provided credentials file, redirect URI, and scopes.
    """
    with open(credentials_path, 'r') as credentials_file:
        credentials = json.load(credentials_file)
    client_id = credentials['web']['client_id']
    auth_url = (
        GOOGLE_AUTH_URL + "?" +
        "response_type=code&"
        "client_id={}&"
        "redirect_uri={}&"
        "scope={}&"
        "access_type=offline&"
        "prompt=consent"
    ).format(client_id, redirect_uri, scopes)
    log("Generated authorization URL: {}".format(auth_url))
    return auth_url


def exchange_code_for_token(auth_code, credentials_path, redirect_uri, log, retries=3):
    """
    Exchange an authorization code for tokens using credentials; retries a few times on failure.
    """
    for attempt in range(retries):
        try:
            with open(credentials_path, 'r') as credentials_file:
                credentials = json.load(credentials_file)
            token_url = GOOGLE_TOKEN_URL
            data = {
                'code': auth_code,
                'client_id': credentials['web']['client_id'],
                'client_secret': credentials['web']['client_secret'],
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(token_url, data=data)
            log("Token exchange response: Status code {}, Body: {}".format(response.status_code, response.text))
            token_response = response.json()
            if response.status_code == 200:
                token_response['token_time'] = time.time()
                return token_response
            else:
                log("Token exchange failed: {}".format(token_response))
                if attempt < retries - 1:
                    log("Retrying token exchange... (Attempt {}/{})".format(attempt + 1, retries))
        except (IOError, ValueError, KeyError, requests.exceptions.RequestException) as e:
            log("Error during token exchange: {}".format(e))
    return {}




def is_valid_authorization_code(auth_code, log):
    """
    Validate auth code shape without side effects.
    """
    if auth_code and isinstance(auth_code, str) and len(auth_code) > 0:
        return True
    log("Invalid authorization code format: {}".format(auth_code))
    return False


def clear_token_cache(token_path, log):
    """
    Delete token cache file if present.
    """
    if os.path.exists(token_path):
        os.remove(token_path)
        log("Cleared token cache.")


def load_token_file(token_path, log):
    """Load token data from file, return dict or None if file doesn't exist"""
    if os.path.exists(token_path):
        try:
            with open(token_path, 'r') as token_file:
                return json.load(token_file)
        except (IOError, ValueError) as e:
            log("Error loading token file: {}".format(e), level="ERROR")
            return None
    return None


def validate_token_data(token_data, log):
    """Validate token data structure. Returns True if valid, False otherwise."""
    if not isinstance(token_data, dict):
        log("Token data is not a dictionary", level="ERROR")
        return False

    if 'access_token' not in token_data or 'expires_in' not in token_data:
        log("Token file is missing required fields: access_token or expires_in", level="WARNING")
        return False

    return True


def compute_expiry(token_data, now, log):
    """Compute token expiry time. Returns expiry timestamp or None on error."""
    try:
        token_time = token_data.get('token_time', now)
        expires_at = token_time + token_data['expires_in']
        return expires_at
    except (KeyError, TypeError, ValueError) as e:
        log("Error calculating token expiry: {}".format(e), level="ERROR")
        return None


def is_token_expired(expires_at, now):
    """Check if token is expired. Returns True if expired."""
    return expires_at <= now


def refresh_and_save_token(token_path, credentials_path, refresh_token, log):
    """Refresh token and save to file. Returns new access_token or None on failure."""
    new_token_data = refresh_access_token(refresh_token, credentials_path, log)
    if 'access_token' not in new_token_data:
        log("Failed to refresh access token. Re-authentication required.", level="WARNING")
        clear_token_cache(token_path, log)
        return None

    # Preserve refresh_token if not in new response (Google refresh doesn't always return it)
    if 'refresh_token' not in new_token_data and refresh_token:
        new_token_data['refresh_token'] = refresh_token

    # Save refreshed token
    if save_token_file(token_path, new_token_data, log):
        log("Access token refreshed successfully.", level="INFO")
        return new_token_data['access_token']
    else:
        log("Failed to save refreshed token.", level="ERROR")
        return None


def save_token_file(token_path, token_data, log):
    """Save token data to file with token_time set"""
    try:
        token_data['token_time'] = time.time()
        with open(token_path, 'w') as token_file:
            json.dump(token_data, token_file)
        log("Token file saved successfully.", level="DEBUG")
        return True
    except (IOError, TypeError) as e:
        log("Error saving token file: {}".format(e), level="ERROR")
        return False


def get_access_token_with_refresh(token_path, credentials_path, log):
    """
    Get access token from file, refresh if expired, with proper validation.
    Returns access_token string or None if re-authentication needed.
    """
    token_data = load_token_file(token_path, log)
    if not token_data:
        log("Access token not found. Please authenticate.", level="INFO")
        return None

    if not validate_token_data(token_data, log):
        clear_token_cache(token_path, log)
        return None

    current_time = time.time()
    expires_at = compute_expiry(token_data, current_time, log)
    if expires_at is None:
        clear_token_cache(token_path, log)
        return None

    if not is_token_expired(expires_at, current_time):
        log("Access token is still valid. Expires in {} seconds.".format(int(expires_at - current_time)), level="DEBUG")
        return token_data['access_token']

    # Token expired, try to refresh
    log("Access token has expired. Current time: {}, Expiry time: {}".format(current_time, expires_at), level="DEBUG")
    refresh_token_value = token_data.get('refresh_token')
    if not refresh_token_value:
        log("Refresh token not found in token file. Re-authentication required.", level="WARNING")
        clear_token_cache(token_path, log)
        return None

    return refresh_and_save_token(token_path, credentials_path, refresh_token_value, log)


def refresh_access_token(refresh_token, credentials_path, log):
    """
    Refresh an access token using the stored client credentials.
    Returns dict with access_token and expires_in, or empty dict on failure.
    """
    log("Refreshing access token.")
    try:
        with open(credentials_path, 'r') as credentials_file:
            credentials = json.load(credentials_file)
        token_url = GOOGLE_TOKEN_URL
        data = {
            'client_id': credentials['web']['client_id'],
            'client_secret': credentials['web']['client_secret'],
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        response = requests.post(token_url, data=data)
        log("Refresh token response: Status code {}, Body:\n {}".format(response.status_code, response.text), level="DEBUG")
        if response.status_code == 200:
            log("Access token refreshed successfully.")
            return response.json()
        else:
            log("Failed to refresh access token. Status code: {}".format(response.status_code))
            return {}
    except (IOError, ValueError, requests.exceptions.RequestException) as e:
        log("Error during token refresh: {}".format(e), level="ERROR")
        return {}