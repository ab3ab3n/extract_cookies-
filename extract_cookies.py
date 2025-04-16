import os
import json
import sys
from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class OpenRouterCookieExtractor(BaseCase):

    def test_extract_openrouter_cookies(self):
        # --- Get Credentials and Proxy Info ---
        email = os.environ.get("elisha49@ptct.net")
        password = os.environ.get("TesF@gm#32391Go")
        # Proxy is handled by the --proxy command-line arg from the workflow

        if not email:
            self.fail("Missing environment variable: OPENROUTER_EMAIL")
        if not password:
            self.fail("Missing environment variable: OPENROUTER_PASSWORD")
            # Note: Also check PROXY_STRING is set if --proxy is used in workflow

        print("Starting OpenRouter login process...")

        # --- Login Steps ---
        try:
            # Step a: Go to sign-in, enter email, click Continue
            signin_url = "https://openrouter.ai/sign-in"
            print(f"Opening: {signin_url}")
            self.open(signin_url)

            # Activate CDP Mode immediately for stealthy interactions
            print("Activating CDP Mode...")
            self.activate_cdp_mode()
            self.sleep(2.5) # Allow initial load & potential CAPTCHA checks

            print(f"Typing email: {email}")
            # Use CDP type for stealth
            self.cdp.type('input[name="identifier"]', email)
            self.sleep(0.6) # Human-like pause

            print("Clicking Continue (Email)...")
            # Use CDP click for stealth
            self.cdp.click('button:contains("Continue")')
            self.sleep(3.5) # Wait for redirect & password page load

            # Step b: Enter Password and click Continue again
            print("Waiting for password field...")
            # Wait for password field to ensure page transition
            self.wait_for_element('input[name="password"]')
            print("Typing password...")
            self.cdp.type('input[name="password"]', password)
            self.sleep(0.6) # Human-like pause

            print("Clicking Continue (Password)...")
            self.cdp.click('button:contains("Continue")')

            # CRUCIAL: Wait for login to complete and redirect
            # Check for an element that only appears when logged in
            print("Waiting for successful login indicator...")
            # Adjust selector if needed - e.g., user avatar, specific nav item
            self.wait_for_element('button[aria-label*="User menu"]', timeout=20)
            print("Login appears successful.")
            self.sleep(2) # Extra pause after login confirmation

            # Step c: Navigate to Keys page and extract cookies
            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            self.open(keys_url)
            print("Waiting for Keys page elements...")
            # Wait for an element specific to the keys page
            self.wait_for_element('button:contains("Create Key")', timeout=15)
            print("Keys page loaded.")
            self.sleep(2) # Pause on keys page

            print("Extracting cookies for domain 'clerk.openrouter.ai'...")
            all_cookies = self.get_cookies()
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
