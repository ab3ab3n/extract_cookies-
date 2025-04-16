import os
import json
import sys
import time
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

            # === Revert to uc_open_with_reconnect ===
            # This method initializes self.cdp correctly after reconnecting
            print("Using uc_open_with_reconnect (longer time)...")
            # Keep increased reconnect_time
            self.uc_open_with_reconnect(signin_url, reconnect_time=7.0)
            print("Page opened/reconnected. Adding extra sleep...")
            # Keep increased sleep after reconnect
            self.sleep(5.0)

            print("Attempting early CAPTCHA click (might do nothing if none)...")
            # Keep this attempt after reconnecting
            try:
                # Use the standard click now, as PyAutoGUI might be less reliable
                # without precise coordinates / iframe handling yet
                self.uc_gui_click_captcha()
                print("Early CAPTCHA click attempted via standard method.")
                self.sleep(2.5) # Pause after potential CAPTCHA interaction
            except Exception as captcha_err:
                print(f"Early CAPTCHA click failed or not needed: {captcha_err}")

            print("Waiting for email field...")
            email_selector = '#identifier-field'
            # Use standard wait now that driver is connected and self.cdp exists
            self.wait_for_element(email_selector, timeout=25) # <<< Standard Wait

            print(f"Typing email: {email}")
            # Use CDP type for potential stealth benefits
            self.cdp.type(email_selector, email)
            self.sleep(0.8)

            print("Clicking Continue (Email)...")
            continue_button_selector = 'form button:contains("Continue")'
            # Use CDP click
            self.cdp.click(continue_button_selector)
            self.sleep(7.0) # <<< Keep increased sleep

            # === Step b: Enter Password ===
            print("Waiting for password field...")
            password_selector = '#password-field'
            # Use standard wait
            self.wait_for_element(password_selector, timeout=20) # <<< Standard Wait
            print("Typing password...")
            # Use CDP type
            self.cdp.type(password_selector, password)
            self.sleep(0.8)

            print("Clicking Continue (Password)...")
            # Use CDP click
            self.cdp.click(continue_button_selector)
            print("Adding sleep after final continue click...")
            self.sleep(5.0) # Reduced slightly, but still significant

            # === Verify Login (Driver is already connected) ===
            print("Waiting for successful login indicator...")
            self.wait_for_element('button[aria-label*="User menu"]', timeout=35) # <<< Increased timeout
            print("Login appears successful.")
            self.sleep(3)

            # === Step c: Navigate to Keys page and extract cookies ===
            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            self.open(keys_url) # Standard open
            print("Waiting for Keys page elements...")
            self.wait_for_element('h2:contains("API Keys")', timeout=30)
            print("Keys page loaded.")
            self.sleep(3)

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
            time.sleep(1)
            try:
                # No need to check is_connected, should be connected here
                self.save_screenshot_to_logs(name="error_screenshot")
                print("Screenshot saved to logs.")
            except Exception as ss_error:
                print(f"WARNING: Failed to save screenshot: {ss_error}")
            self.fail(f"Test failed during execution: {e}")
