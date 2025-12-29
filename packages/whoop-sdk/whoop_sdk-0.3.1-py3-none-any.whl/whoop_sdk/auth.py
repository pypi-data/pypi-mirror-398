import os
import json
import shutil
import time
import webbrowser
import urllib.parse
from pathlib import Path
import requests
import http.server
import socketserver
import threading
from typing import Optional, Tuple


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler to capture OAuth callback."""
    
    def __init__(self, callback_event, callback_data, *args, **kwargs):
        self.callback_event = callback_event
        self.callback_data = callback_data
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Extract code and state from query parameters
        code = query_params.get("code", [None])[0]
        state = query_params.get("state", [None])[0]
        
        if code:
            print(f"   [OK] Authorization code found in callback")
            self.callback_data["code"] = code
            self.callback_data["state"] = state
            self.callback_event.set()
            
            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to your application.</p>
                </body>
                </html>
            """)
        else:
            # Send error response if no code found
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Error</title></head>
                <body>
                    <h1>Authorization Error</h1>
                    <p>No authorization code received. Please try again.</p>
                </body>
                </html>
            """)
    
    def log_message(self, format, *args):
        """Suppress default logging to keep output clean."""
        pass


class AuthManager:
    """Handles WHOOP OAuth authentication and token management."""

    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
    CONFIG_PATH = Path.home() / ".whoop_sdk" / "config.json"
    SETTINGS_PATH = Path.home() / ".whoop_sdk" / "settings.json"

    def __init__(self):
        self.settings = self._load_settings()

        # Prefer environment variables, then fallback to local settings file
        self.client_id = os.getenv("WHOOP_CLIENT_ID") or self.settings.get("client_id")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET") or self.settings.get("client_secret")
        # Default to Google redirect for manual fallback (automated flow uses dynamic localhost ports)
        self.redirect_uri = self.settings.get("redirect_uri") or "https://www.google.com"

        # If nothing found, prompt the user interactively (first run)
        if not self.client_id or not self.client_secret:
            print("WHOOP SDK setup required.")
            print("You can get these credentials from https://developer.whoop.com/")
            print("--------------------------------")
            print("(Type 'quit', 'exit', or 'cancel' at any time to exit)")
            print()
            
            while True:
                try:
                    self.client_id = input("Enter your WHOOP Client ID: ").strip()
                    
                    # Check for exit commands
                    if self.client_id.lower() in ['quit', 'exit', 'cancel']:
                        print("\n Setup cancelled by user.")
                        raise RuntimeError("Setup cancelled - no credentials provided.")
                    
                    if not self.client_id:
                        print(" Client ID cannot be empty. Please try again.")
                        continue
                    
                    self.client_secret = input("Enter your WHOOP Client Secret: ").strip()
                    
                    # Check for exit commands
                    if self.client_secret.lower() in ['quit', 'exit', 'cancel']:
                        print("\n Setup cancelled by user.")
                        raise RuntimeError("Setup cancelled - no credentials provided.")
                    
                    if not self.client_secret:
                        print(" Client Secret cannot be empty. Please try again.")
                        continue
                    
                    # Use localhost as default (for fallback to Google redirect if needed)
                    # Note: Automated flow uses dynamic localhost ports
                    self.redirect_uri = "https://www.google.com"
                    
                    # Validate the inputs
                    if len(self.client_id) < 10:
                        print(" Client ID seems too short. Please check and try again.")
                        continue
                    
                    if len(self.client_secret) < 10:
                        print(" Client Secret seems too short. Please check and try again.")
                        continue
                    
                    break
                    
                except KeyboardInterrupt:
                    print("\n Setup cancelled by user.")
                    raise RuntimeError("Setup cancelled - no credentials provided.")
                except RuntimeError:
                    # Re-raise RuntimeError (from exit commands)
                    raise
                except Exception as e:
                    print(f" Error during setup: {e}")
                    print("Please try again.")
                    continue
            
            self._save_settings({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            })
            print(f"Credentials saved to {self.SETTINGS_PATH}")

        self.scopes = "offline read:profile read:recovery read:sleep read:workout read:cycles read:body_measurement"
        self.state = "whoop_sdk_state_12345"
        self.tokens = self._load_tokens()

    # ---------- Public Methods ----------

    def reset_config(self):
        """Reset/clear all stored configuration and tokens."""
        
        config_dir = self.CONFIG_PATH.parent
        
        if config_dir.exists():
            shutil.rmtree(config_dir)
            print("[OK] Configuration and tokens cleared.")
            print("Next time you initialize AuthManager, you'll be prompted for new credentials.")
        else:
            print("[INFO] No configuration found to clear.")

    def reset_auth(self):
        """Clear tokens only (keeps credentials) and trigger OAuth flow."""
        
        # Ensure credentials are loaded
        if not self.client_id or not self.client_secret:
            # Reload settings in case they weren't loaded
            self.settings = self._load_settings()
            self.client_id = os.getenv("WHOOP_CLIENT_ID") or self.settings.get("client_id")
            self.client_secret = os.getenv("WHOOP_CLIENT_SECRET") or self.settings.get("client_secret")
            
            if not self.client_id or not self.client_secret:
                raise RuntimeError(
                    "No client credentials found. Please set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET "
                    "environment variables, or use reset_config() to set them up."
                )
        
        # Clear tokens but keep settings (credentials)
        if self.CONFIG_PATH.exists():
            self.CONFIG_PATH.unlink()
            print("[OK] Tokens cleared.")
        else:
            print("[INFO] No tokens found to clear.")
        
        # Clear tokens from memory
        self.tokens = {}
        
        # Trigger OAuth flow
        print("Starting OAuth flow...")
        return self.login()

    def login(self):
        """Perform one-time OAuth login."""
        # Check if we already have valid tokens
        if self.tokens and self.tokens.get("access_token"):
            print("You're already logged in!")
            print("If you need to re-authenticate or change your profile, call auth.reset_config() first.")
            return True
        
        # Ensure credentials are available before proceeding
        if not self.client_id or not self.client_secret:
            # Reload settings in case they weren't loaded
            self.settings = self._load_settings()
            self.client_id = os.getenv("WHOOP_CLIENT_ID") or self.settings.get("client_id")
            self.client_secret = os.getenv("WHOOP_CLIENT_SECRET") or self.settings.get("client_secret")
            
            # If still no credentials, prompt for them (like __init__ does)
            if not self.client_id or not self.client_secret:
                print("WHOOP SDK setup required.")
                print("You can get these credentials from https://developer.whoop.com/")
                print("--------------------------------")
                print("(Type 'quit', 'exit', or 'cancel' at any time to exit)")
                print()
                
                while True:
                    try:
                        self.client_id = input("Enter your WHOOP Client ID: ").strip()
                        
                        # Check for exit commands
                        if self.client_id.lower() in ['quit', 'exit', 'cancel']:
                            print("\n Setup cancelled by user.")
                            raise RuntimeError("Setup cancelled - no credentials provided.")
                        
                        if not self.client_id:
                            print(" Client ID cannot be empty. Please try again.")
                            continue
                        
                        self.client_secret = input("Enter your WHOOP Client Secret: ").strip()
                        
                        # Check for exit commands
                        if self.client_secret.lower() in ['quit', 'exit', 'cancel']:
                            print("\n Setup cancelled by user.")
                            raise RuntimeError("Setup cancelled - no credentials provided.")
                        
                        if not self.client_secret:
                            print(" Client Secret cannot be empty. Please try again.")
                            continue
                        
                        # Use localhost as default (for fallback to Google redirect if needed)
                        self.redirect_uri = "https://www.google.com"
                        
                        # Validate the inputs
                        if len(self.client_id) < 10:
                            print(" Client ID seems too short. Please check and try again.")
                            continue
                        
                        if len(self.client_secret) < 10:
                            print(" Client Secret seems too short. Please check and try again.")
                            continue
                        
                        break
                        
                    except KeyboardInterrupt:
                        print("\n Setup cancelled by user.")
                        raise RuntimeError("Setup cancelled - no credentials provided.")
                    except RuntimeError:
                        # Re-raise RuntimeError (from exit commands)
                        raise
                    except Exception as e:
                        print(f" Error during setup: {e}")
                        print("Please try again.")
                        continue
                
                self._save_settings({
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                })
                print(f"Credentials saved to {self.SETTINGS_PATH}")
        
        # First attempt: Try automated localhost flow
        print("\n" + "="*60)
        print("Starting OAuth Authentication")
        print("="*60)
        print("Attempting automated localhost flow (preferred method)...")
        server_result = self._start_localhost_server()
        
        if not server_result:
            print("\n[WARNING] Automated localhost flow unavailable")
            print("Falling back to manual authorization with Google redirect...")
        
        if server_result:
            callback_event, callback_data, server, port = server_result
            localhost_redirect_uri = f"http://localhost:{port}"
        
            url = self._build_auth_url(redirect_uri=localhost_redirect_uri)
            try:
                webbrowser.open(url)
                print(f"   [OK] Browser opened successfully at {url}")
            except Exception as e:
                print(f"   [WARNING] Could not automatically open browser: {e}")
                print(f"   Please manually open this URL in your browser: {url}")

            print(f"\nTip: Once you approve access in your browser, authorization will complete automatically and you can close the browser window.")
            
            try:
                # Wait for callback with timeout (2 minutes)
                if callback_event.wait(timeout=120):
                    # Callback received
                    code = callback_data.get("code")
                    if code:
                        print(f"   [OK] Authorization code extracted successfully")
                        
                        # Verify state matches
                        received_state = callback_data.get("state")
                        if received_state != self.state:
                            raise RuntimeError("State parameter mismatch. Possible CSRF attack.")
                        print(f"   [OK] State verification passed")
                        
                        # Shutdown server
                        server.shutdown()
                        server.server_close()
                        print(f"   [OK] Server shutdown complete - port {port} is now free")
        
                        tokens = self._exchange_code_for_tokens(code, redirect_uri=localhost_redirect_uri)
                        self._save_tokens(tokens)
                        print(f"   [OK] Tokens received and saved")
                        print(f"\n" + "="*60)
                        print(f"[SUCCESS] WHOOP SDK authorization complete!")
                        print(f"   Method: Automated localhost flow")
                        print(f"   Redirect URI: {localhost_redirect_uri}")
                        print(f"="*60)
                        return True
                    else:
                        raise RuntimeError("No authorization code received in callback.")
                else:
                    # Timeout - shutdown server before raising error
                    print(f"\n   [TIMEOUT] No callback received within 2 minutes")
                    try:
                        server.shutdown()
                        server.server_close()
                        print(f"   [OK] Server shutdown complete - port {port} is now free")
                    except Exception as cleanup_error:
                        print(f"   [WARNING] Error during server cleanup: {cleanup_error}")
                    raise RuntimeError("Authorization timeout. No callback received within 2 minutes.")
            except Exception as e:
                # Clean up server on error
                try:
                    print(f"\n   Cleaning up server due to error...")
                    server.shutdown()
                    server.server_close()
                    print(f"   [OK] Server shutdown complete - port {port} is now free")
                except Exception as cleanup_error:
                    print(f"   [WARNING] Error during server cleanup: {cleanup_error}")
                print(f"\n[ERROR] Automated localhost flow failed: {e}")
                print(f"Falling back to manual authorization with Google redirect...")
                # Fall through to manual method
        
        # Fallback: Manual copy-paste method with Google redirect
        print("\n" + "="*60)
        print("Manual Authorization Flow (Google Redirect)")
        print("="*60)
        print(f"Using redirect URI: {self.redirect_uri}")
        print(f"Opening WHOOP authorization page in your browser...")
        url = self._build_auth_url()
        print(f"   URL: {url}")
        try:
            webbrowser.open(url)
            print("   [OK] Browser opened successfully")
        except Exception as e:
            print(f"   [WARNING] Could not automatically open browser: {e}")
            print(f"   Please manually open this URL in your browser: {url}")

        print(f"\nAfter you approve access, you'll be redirected to:")
        print(f"   -> {self.redirect_uri}?code=XXXX&state={self.state}")
        print(f"\nInstructions:")
        print(f"   1. Copy the entire URL from your browser address bar")
        print(f"   2. Or just copy the code part (the value after 'code=')")
        print(f"   3. Paste it below")
        print(f"   To cancel, type 'cancel' or press Ctrl+C")
        
        while True:
            try:
                code = input("\nPaste the code from that URL (or 'cancel' to exit): ").strip()
                
                if code.lower() == 'cancel':
                    print("[ERROR] Login cancelled by user.")
                    raise RuntimeError("Login cancelled - no tokens obtained.")
                
                if not code:
                    print("   [WARNING] Code cannot be empty. Please try again.")
                    continue
                
                # Extract code from full URL if user pasted the whole thing
                if "code=" in code:
                    code = code.split("code=")[1].split("&")[0]
                    print(f"   [OK] Code extracted from URL")
                
                if len(code) < 10:
                    print(f"   [WARNING] Code seems too short. Please check and try again.")
                    continue
                
                print(f"   [OK] Code received and validated")
                print(f"\nExchanging authorization code for access tokens...")
                tokens = self._exchange_code_for_tokens(code)
                self._save_tokens(tokens)
                print(f"   [OK] Tokens received and saved")
                print(f"\n" + "="*60)
                print(f"[SUCCESS] WHOOP SDK authorization complete!")
                print(f"   Method: Manual authorization (Google redirect)")
                print(f"   Redirect URI: {self.redirect_uri}")
                print(f"="*60)
                return True
                
            except KeyboardInterrupt:
                print("\n[ERROR] Login cancelled by user.")
                raise RuntimeError("Login cancelled - no tokens obtained.")
            except Exception as e:
                print(f"\n[ERROR] Login failed: {e}")
                print("   Please check your code and try again.")
                retry = input("   Try again? (y/n): ").strip().lower()
                if retry not in ['y', 'yes']:
                    raise RuntimeError(f"Login failed: {e}")
                continue

    def ensure_access_token(self):
        """Return valid access token (auto-refresh if needed)."""
        if not self.tokens:
            raise RuntimeError("No tokens found. Run auth.login() first.")
        
        # Check if access token exists or is expired (with 60 second safety buffer)
        access_token = self.tokens.get("access_token")
        expires_at = self.tokens.get("expires_at")
        if not access_token or (expires_at and time.time() >= (expires_at - 60)):
            return self.refresh_access_token()

        return access_token

    def refresh_access_token(self):
        """Use the stored refresh token to get a new access token."""
        print("Refreshing access token...")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = requests.post(self.TOKEN_URL, data=data)
        resp.raise_for_status()
        new_tokens = resp.json()
        self.tokens.update(new_tokens)
        self._save_tokens(self.tokens)
        print(" Access token refreshed.")
        return self.tokens["access_token"]

    # ---------- Internal Helpers ----------

    def _start_localhost_server(self) -> Optional[Tuple[threading.Event, dict, socketserver.TCPServer, int]]:
        """
        Start a localhost HTTP server on port 8080 to capture OAuth callback.
        
        Returns:
            Tuple of (callback_event, callback_data, server, port) if successful, None if failed
        """
        callback_event = threading.Event()
        callback_data = {}
        
        port = 8080
        
        try:
            # Create a handler class that captures the callback data
            class OAuthHandler(CallbackHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(callback_event, callback_data, *args, **kwargs)
            
            # Create server with ThreadingMixIn for thread safety
            class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
                allow_reuse_address = True
                daemon_threads = True
            
            server = ThreadedTCPServer(("localhost", port), OAuthHandler)
            
            # Start server in a thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            print(f"   [OK] Server is now listening on http://localhost:{port}")
            
            return (callback_event, callback_data, server, port)
        except OSError as e:
            # Port 8080 is in use
            print(f"[ERROR] Port {port} is unavailable: {e}")
            print(f"   Gracefully falling back to manual authorization...")
            return None

    def _build_auth_url(self, redirect_uri: Optional[str] = None):
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri or self.redirect_uri,
            "scope": self.scopes,
            "state": self.state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def _exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            resp = requests.post(self.TOKEN_URL, data=data)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Network error: Could not connect to WHOOP servers. Please check your internet connection.")
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 400:
                raise RuntimeError("Invalid authorization code. Please try logging in again.")
            elif resp.status_code == 401:
                raise RuntimeError("Authentication failed. Please check your client credentials.")
            else:
                raise RuntimeError(f"HTTP error {resp.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")
        
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid response from WHOOP servers: {e}")

    def _save_tokens(self, tokens):
        # Calculate expiration timestamp if expires_in is provided
        if "expires_in" in tokens:
            tokens["expires_at"] = time.time() + tokens["expires_in"]
        
        try:
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(tokens, f, indent=2)
            self.tokens = tokens
        except PermissionError:
            raise RuntimeError(f"Permission denied: Cannot write to {self.CONFIG_PATH}. Please check file permissions.")
        except OSError as e:
            raise RuntimeError(f"Failed to save tokens: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error saving tokens: {e}")

    def _load_tokens(self):
        if self.CONFIG_PATH.exists():
            with open(self.CONFIG_PATH) as f:
                return json.load(f)
        return {}

    def _load_settings(self):
        if self.SETTINGS_PATH.exists():
            with open(self.SETTINGS_PATH) as f:
                return json.load(f)
        return {}

    def _save_settings(self, data):
        self.SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.SETTINGS_PATH, "w") as f:
            json.dump(data, f, indent=2)
