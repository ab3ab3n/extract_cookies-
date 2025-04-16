import os
import json
import sys
from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class OpenRouterCookieExtractor(BaseCase):

    def test_extract_openrouter_cookies(self):
        # --- Get Credentials and Proxy Info ---
        email = os.environ.get("OPENROUTER_EMAIL")
        password = os.environ.get("OPENROUTER_PASSWORD")
        # Proxy is handled by the --proxy command-line arg from the workflow

        if not email:
            self.fail("Missing environment variable: OPENROUTER_EMAIL")
        if not password:
            self.fail("Missing environment variable: OPENROUTER_PASSWORD")
            # Note: Also check PROXY_STRING is set if --proxy is used in workflow

        print("Starting OpenRouter login process...")

        # --- Login Steps ---
        try:
            # Step a: Go to sign-in stealthily, enter email, click Continue
            signin_url = "https://openrouter.ai/sign-in"
            print(f"Opening stealthily: {signin_url}")
            # Use uc_open_with_reconnect for initial load & CDP activation
            # Increased reconnect_time allows more time for page/CAPTCHA checks
            self.uc_open_with_reconnect(signin_url, reconnect_time=4.5) # <--- CHANGE HERE

            print("Waiting for email field...")
            # Explicitly wait for the element AFTER reconnecting
            email_selector = 'input[name="identifier"]'
            self.wait_for_element(email_selector) # <--- ADDED WAIT

            print(f"Typing email: {email}")
            # Use CDP type for stealth
            self.cdp.type(email_selector, email)
            self.sleep(0.6) # Human-like pause

            print("Clicking Continue (Email)...")
            # Use CDP click for stealth
            # Make selector more specific if needed
            continue_button_selector = 'form button:contains("Continue")'
            self.cdp.click(continue_button_selector)
            # Increase sleep after first continue click, password page might take time
            self.sleep(5.0) # <--- INCREASED SLEEP

            # Step b: Enter Password and click Continue again
            print("Waiting for password field...")
            # Wait for password field to ensure page transition is complete
            password_selector = 'input[name="password"]'
            self.wait_for_element(password_selector) # <--- ADDED WAIT
            print("Typing password...")
            self.cdp.type(password_selector, password)
            self.sleep(0.6) # Human-like pause

            print("Clicking Continue (Password)...")
            # Re-use the continue button selector (assuming it's the same structure)
            self.cdp.click(continue_button_selector)

            # CRUCIAL: Wait for login to complete and redirect
            print("Waiting for successful login indicator...")
            # Using the user menu button as a sign of successful login
            # Increased timeout for potentially slow post-login load
            self.wait_for_element('button[aria-label*="User menu"]', timeout=25) # <--- INCREASED TIMEOUT
            print("Login appears successful.")
            self.sleep(2) # Extra pause after login confirmation

            # Step c: Navigate to Keys page and extract cookies
            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            # Use standard open for subsequent navigations after login
            self.open(keys_url) # <--- Changed from activate_cdp_mode
            print("Waiting for Keys page elements...")
            # Wait for an element specific to the keys page
            # Increased timeout for potentially slow page load
            self.wait_for_element('h2:contains("API Keys")', timeout=20) # <--- More robust selector & INCREASED TIMEOUT
            print("Keys page loaded.")
            self.sleep(2) # Pause on keys page

            print("Extracting cookies for domain 'clerk.openrouter.ai'...")
            # Cookies should be available now via standard WebDriver methods
            all_cookies = self.get_cookies() # <--- Standard get_cookies is fine now
            clerk_cookies = [
                cookie for cookie in all_cookies
                if cookie.get('domain') == 'clerk.openrouter.ai'
            ]

            if not clerk_cookies:
                print("WARNING: No cookies found for domain 'clerk.openrouter.ai'.")
                # Consider failing if cookies are essential:
                # self.fail("No cookies found for domain 'clerk.openrouter.ai'.")
            else:
                print(f"Found {len(clerk_cookies)} cookies for the domain.")

            # --- Save Cookies ---
            output_file = "openrouter_cookies.json"
            print(f"Saving cookies to {output_file}...")
            with open(output_file, 'w') as f:
                json.dump(clerk_cookies, f, indent=4)

            print(f"Successfully extracted and saved cookies to {output_file}")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            # Take screenshot on error for debugging in Actions
            self.save_screenshot_to_logs(name="error_screenshot")
            self.fail(f"Test failed during execution: {e}")
