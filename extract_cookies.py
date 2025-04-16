import os
import json
import sys
import time  # Import time for a potential manual sleep if needed
from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class OpenRouterCookieExtractor(BaseCase):

    def test_extract_openrouter_cookies(self):
        email = os.environ.get("OPENROUTER_EMAIL")
        password = os.environ.get("OPENROUTER_PASSWORD")

        if not email:
            self.fail("Missing environment variable: OPENROUTER_EMAIL")
        if not password:
            self.fail("Missing environment variable: OPENROUTER_PASSWORD")

        print("Starting OpenRouter login process...")

        try:
            signin_url = "https://openrouter.ai/sign-in"
            print(f"Opening stealthily: {signin_url}")

            # === Attempt 1: Longer Reconnect & Early CAPTCHA Click ===
            print("Using uc_open_with_reconnect (longer time)...")
            # Increased reconnect time significantly
            self.uc_open_with_reconnect(signin_url, reconnect_time=7.0)
            print("Page opened/reconnected. Adding extra sleep...")
            # Add a longer sleep AFTER reconnecting before doing anything else
            self.sleep(5.0) # <<< Longer sleep after reconnect

            print("Attempting early CAPTCHA click (might do nothing if none)...")
            # Try clicking potential CAPTCHA area immediately after loading/sleep
            # This might satisfy an early invisible check
            try:
                self.uc_gui_click_captcha() # Use the more robust click if needed
                print("Early CAPTCHA click attempted.")
                self.sleep(2.0) # Pause after potential CAPTCHA interaction
            except Exception as captcha_err:
                print(f"Early CAPTCHA click failed (maybe none present): {captcha_err}")
                # Continue anyway, might not have been necessary

            print("Waiting for email field...")
            email_selector = 'input[name="identifier"]'
            # Increase the timeout for the first wait significantly
            self.wait_for_element(email_selector, timeout=20) # <<< Increased timeout

            print(f"Typing email: {email}")
            # If wait_for_element succeeded, now use CDP type
            self.cdp.type(email_selector, email)
            self.sleep(0.7) # Slightly longer human-like pause

            print("Clicking Continue (Email)...")
            continue_button_selector = 'form button:contains("Continue")'
            self.cdp.click(continue_button_selector)
            self.sleep(6.0) # <<< Increased sleep after first continue

            # === Step b: Enter Password ===
            print("Waiting for password field...")
            password_selector = 'input[name="password"]'
            self.wait_for_element(password_selector, timeout=15) # <<< Increased timeout
            print("Typing password...")
            self.cdp.type(password_selector, password)
            self.sleep(0.7) # Slightly longer human-like pause

            print("Clicking Continue (Password)...")
            self.cdp.click(continue_button_selector)

            print("Waiting for successful login indicator...")
            self.wait_for_element('button[aria-label*="User menu"]', timeout=30) # <<< Increased timeout
            print("Login appears successful.")
            self.sleep(3) # <<< Increased sleep after login

            # === Step c: Navigate to Keys page and extract cookies ===
            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            self.open(keys_url)
            print("Waiting for Keys page elements...")
            self.wait_for_element('h2:contains("API Keys")', timeout=25) # <<< Increased timeout
            print("Keys page loaded.")
            self.sleep(3) # <<< Increased sleep on keys page

            print("Extracting cookies for domain 'clerk.openrouter.ai'...")
            all_cookies = self.get_cookies()
            clerk_cookies = [
                cookie for cookie in all_cookies
                if cookie.get('domain') == 'clerk.openrouter.ai'
            ]

            if not clerk_cookies:
                print("WARNING: No cookies found for domain 'clerk.openrouter.ai'.")
            else:
                print(f"Found {len(clerk_cookies)} cookies for the domain.")

            output_file = "openrouter_cookies.json"
            print(f"Saving cookies to {output_file}...")
            with open(output_file, 'w') as f:
                json.dump(clerk_cookies, f, indent=4)
            print(f"Successfully extracted and saved cookies to {output_file}")

        except Exception as e:
            print(f"\nAn error occurred during the process: {e}")
            print("Attempting to save screenshot...")
            # Add a small delay before screenshot in case it helps stability
            time.sleep(1)
            try:
                self.save_screenshot_to_logs(name="error_screenshot")
                print("Screenshot saved to logs.")
            except Exception as ss_error:
                print(f"WARNING: Failed to save screenshot: {ss_error}")
            self.fail(f"Test failed during execution: {e}")
