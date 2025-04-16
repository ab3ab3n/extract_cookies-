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
            print(f"Opening stealthily with disconnect: {signin_url}")

            # === Attempt 2: Use uc_open_with_disconnect, stay disconnected longer ===
            # This opens the page in a new tab and leaves the driver disconnected.
            # Use the correct keyword argument: timeout
            self.uc_open_with_disconnect(signin_url, timeout=8.0) # <<< CORRECTED KEYWORD
            print("Page opened (driver disconnected). Adding extra sleep...")
            # Longer sleep while disconnected - Keep this for extra buffer
            self.sleep(7.0)

            print("Attempting early CAPTCHA click (might do nothing if none)...")
            # Try clicking potential CAPTCHA area while still disconnected
            try:
                captcha_iframe_selector = 'iframe[title="Cloudflare Turnstile"]'
                iframe_rect = self.cdp.get_element_rect(captcha_iframe_selector, timeout=3)
                iframe_center_x = iframe_rect.x + (iframe_rect.width / 2)
                iframe_center_y = iframe_rect.y + (iframe_rect.height / 2)
                self.uc_gui_click_x_y(iframe_center_x, iframe_center_y)
                print("Early CAPTCHA click attempted via coordinates.")
                self.sleep(2.5)
            except Exception as captcha_err:
                print(f"Could not find/click CAPTCHA early (maybe none present): {captcha_err}")
                try:
                    self.uc_gui_click_captcha()
                    print("Early CAPTCHA click attempted via standard method.")
                    self.sleep(2.5)
                except Exception as captcha_err2:
                     print(f"Standard CAPTCHA click also failed: {captcha_err2}")

            print("Waiting for email field using CDP...")
            email_selector = '#identifier-field'
            self.cdp.wait_for_element_visible(email_selector, timeout=25)

            print(f"Typing email: {email}")
            self.cdp.type(email_selector, email)
            self.sleep(0.8)

            print("Clicking Continue (Email)...")
            continue_button_selector = 'form button:contains("Continue")'
            self.cdp.click(continue_button_selector)
            self.sleep(7.0)

            # === Step b: Enter Password (still disconnected) ===
            print("Waiting for password field using CDP...")
            password_selector = '#password-field'
            self.cdp.wait_for_element_visible(password_selector, timeout=20)
            print("Typing password...")
            self.cdp.type(password_selector, password)
            self.sleep(0.8)

            print("Clicking Continue (Password)...")
            self.cdp.click(continue_button_selector)
            print("Adding significant sleep after final continue click...")
            self.sleep(10.0)

            # === Reconnect and Verify Login ===
            print("Reconnecting WebDriver to verify login...")
            self.reconnect()
            print("Waiting for successful login indicator...")
            self.wait_for_element('button[aria-label*="User menu"]', timeout=30)
            print("Login appears successful.")
            self.sleep(3)

            # === Step c: Navigate to Keys page and extract cookies ===
            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            self.open(keys_url)
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
                if not self.is_connected(): self.reconnect(0.2)
                self.save_screenshot_to_logs(name="error_screenshot")
                print("Screenshot saved to logs.")
            except Exception as ss_error:
                print(f"WARNING: Failed to save screenshot: {ss_error}")
            self.fail(f"Test failed during execution: {e}")
