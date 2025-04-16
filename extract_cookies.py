import os
import json
import sys
import time
from seleniumbase import BaseCase
from seleniumbase import SB
from seleniumbase.common import exceptions  # Import specific exceptions

# --- Pytest Integration ---
# Allows running with "pytest extract_cookies.py --uc -s"
class OpenRouterCookieExtractor(BaseCase):

    # Keep credentials accessible within the class scope if needed later
    email = os.environ.get("OPENROUTER_EMAIL")
    password = os.environ.get("OPENROUTER_PASSWORD")

    # --- Main Logic Function (called by the test) ---
    def run_extraction_logic(self):
        if not self.email:
            self.fail("Missing environment variable: OPENROUTER_EMAIL")
        if not self.password:
            self.fail("Missing environment variable: OPENROUTER_PASSWORD")

        print("Starting OpenRouter login process...")
        signin_url = "https://openrouter.ai/sign-in"
        page_source = None
        screenshot_path = None

        try:
            print(f"Opening stealthily: {signin_url}")
            print("Using uc_open_with_reconnect (long time)...")
            # Use reconnect, longer time, keep it headed for macOS GUI
            self.uc_open_with_reconnect(signin_url, reconnect_time=8.0)
            print("Page opened/reconnected. Adding extra sleep...")
            self.sleep(6.0) # Moderate sleep after reconnect

            # Optional: Try early CAPTCHA click (still might fail)
            print("Attempting early CAPTCHA click (might do nothing if none)...")
            try:
                self.uc_gui_click_captcha()
                print("Early CAPTCHA click attempted.")
                self.sleep(3.0)
            except Exception as captcha_err:
                print(f"Early CAPTCHA click failed or not needed: {captcha_err}")

            print("Waiting for email field...")
            email_selector = '#identifier-field'
            # Wait a reasonable time, but expect this might fail
            self.wait_for_element_visible(email_selector, timeout=25)

            print(f"Typing email: {self.email}")
            self.cdp.type(email_selector, self.email)
            self.sleep(1.0)

            print("Clicking Continue (Email)...")
            continue_button_selector = 'form button:contains("Continue")'
            self.cdp.click(continue_button_selector)
            self.sleep(7.0) # Long sleep for password page

            # --- Password Step ---
            print("Waiting for password field...")
            password_selector = '#password-field'
            self.wait_for_element_visible(password_selector, timeout=20)
            print("Typing password...")
            self.cdp.type(password_selector, self.password)
            self.sleep(1.0)

            print("Clicking Continue (Password)...")
            self.cdp.click(continue_button_selector)
            print("Adding long sleep after final continue click...")
            self.sleep(10.0)

            # --- Verify & Navigate ---
            print("Reconnecting WebDriver to verify login...")
            # Reconnect ONLY IF DISCONNECTED (uc_open_with_reconnect leaves it connected)
            if not self.is_connected(): self.reconnect(0.5)
            print("Waiting for successful login indicator...")
            self.wait_for_element('a[href="/settings"]', timeout=40)
            print("Login appears successful.")
            self.sleep(3.0)

            keys_url = "https://openrouter.ai/settings/keys"
            print(f"Navigating to Keys page: {keys_url}")
            self.open(keys_url)
            print("Waiting for Keys page elements...")
            self.wait_for_element('h2:contains("API Keys")', timeout=30)
            print("Keys page loaded.")
            self.sleep(3.0)

            # --- Cookie Extraction ---
            print("Extracting cookies for domain 'clerk.openrouter.ai'...")
            all_cookies = self.get_cookies()
            clerk_cookies = [
                cookie for cookie in all_cookies
                if cookie.get('domain') == 'clerk.openrouter.ai'
            ]

            if not clerk_cookies:
                print("WARNING: No cookies found for domain 'clerk.openrouter.ai'.")
                self.fail("No cookies found for domain 'clerk.openrouter.ai'.")
            else:
                print(f"Found {len(clerk_cookies)} cookies for the domain.")

            output_file = "openrouter_cookies.json"
            print(f"Saving cookies to {output_file}...")
            with open(output_file, 'w') as f:
                json.dump(clerk_cookies, f, indent=4)
            print(f"Successfully extracted and saved cookies to {output_file}")

        # --- Specific Exception Handling ---
        except (exceptions.NoSuchElementException, exceptions.ElementNotVisibleException) as element_error:
            print(f"\nElement Interaction Error: {element_error}")
            print("Attempting to capture page source for debugging...")
            try:
                 # Try reconnecting if needed before getting source
                if not self.is_connected(): self.reconnect(0.5)
                page_source = self.get_page_source()
                source_file = os.path.join(self.log_path, "page_source_on_error.html")
                with open(source_file, "w", encoding='utf-8') as f:
                    f.write(page_source)
                print(f"Page source saved to: {source_file}")
                # Optional: Print a snippet
                # print("Page source snippet:\n", page_source[0:1000])
            except Exception as source_err:
                print(f"WARNING: Failed to get page source: {source_err}")
            print("Attempting to save screenshot...")
            try:
                if not self.is_connected(): self.reconnect(0.5)
                screenshot_path = self.save_screenshot_to_logs(name="element_not_found_error")
                print(f"Screenshot saved to: {screenshot_path}")
            except Exception as ss_error:
                print(f"WARNING: Failed to save screenshot: {ss_error}")
            self.fail(f"Test failed finding/interacting with element: {element_error}")

        # --- General Exception Handling ---
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Attempting to save screenshot...")
            time.sleep(1) # Small delay
            try:
                if not self.is_connected(): self.reconnect(0.5)
                screenshot_path = self.save_screenshot_to_logs(name="unexpected_error")
                print(f"Screenshot saved to: {screenshot_path}")
            except Exception as ss_error:
                print(f"WARNING: Failed to save screenshot: {ss_error}")
            self.fail(f"Test failed during execution: {e}")

    # --- Pytest Test Method ---
    def test_run_extraction(self):
        # Add headless=False to ensure GUI for PyAutoGUI clicks
        # Note: SB() manager might be slightly more robust, but BaseCase works
        # If using BaseCase, ensure --uc is passed via pytest in workflow
        self.run_extraction_logic()
