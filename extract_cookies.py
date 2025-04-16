import os
import json
import sys
import time
from seleniumbase import SB # Import SB
from seleniumbase.common import exceptions

# --- Get Credentials EARLY ---
email = os.environ.get("OPENROUTER_EMAIL")
password = os.environ.get("OPENROUTER_PASSWORD")

if not email:
    print("::error::Missing environment variable: OPENROUTER_EMAIL")
    sys.exit(1)
if not password:
    print("::error::Missing environment variable: OPENROUTER_PASSWORD")
    sys.exit(1)

# --- Use SB Context Manager ---
# SB will parse the --uc flag from the pytest command
# Add test=True to get logging benefits (screenshots on failure)
# Add headless=False for macOS runner GUI needed by uc_gui_click_captcha
# Add incognito/guest for potential extra stealth
try:
    with SB(uc=True, test=True, headless=False, incognito=True, guest=True) as sb:
        # 'sb' is now the SeleniumBase instance, replacing 'self'

        print("Starting OpenRouter login process...")
        signin_url = "https://openrouter.ai/sign-in"
        page_source = None
        screenshot_path = None

        print(f"Opening stealthily: {signin_url}")
        print("Using uc_open_with_reconnect (long time)...")
        # This method now belongs to the 'sb' object
        sb.uc_open_with_reconnect(signin_url, reconnect_time=8.0)
        print("Page opened/reconnected. Adding extra sleep...")
        sb.sleep(6.0)

        print("Attempting early CAPTCHA click (might do nothing if none)...")
        try:
            sb.uc_gui_click_captcha() # Use sb object
            print("Early CAPTCHA click attempted.")
            sb.sleep(3.0)
        except Exception as captcha_err:
            print(f"Early CAPTCHA click failed or not needed: {captcha_err}")

        print("Waiting for email field...")
        email_selector = '#identifier-field'
        # Use sb object for waits
        sb.wait_for_element_present(email_selector, timeout=30) # Increased timeout
        sb.sleep(1.0)
        sb.wait_for_element_visible(email_selector, timeout=5)

        print(f"Typing email: {email}")
        # Use sb.cdp (This should be initialized correctly by SB manager)
        sb.cdp.type(email_selector, email)
        sb.sleep(1.0)

        print("Clicking Continue (Email)...")
        continue_button_selector = 'form button:contains("Continue")'
        # Use sb.cdp
        sb.cdp.click(continue_button_selector)
        sb.sleep(8.0) # Increased sleep

        # --- Password Step ---
        print("Waiting for password field...")
        password_selector = '#password-field'
        # Use sb object
        sb.wait_for_element_present(password_selector, timeout=25) # Increased timeout
        sb.sleep(1.0)
        sb.wait_for_element_visible(password_selector, timeout=5)

        print("Typing password...")
        # Use sb.cdp
        sb.cdp.type(password_selector, password)
        sb.sleep(1.0)

        print("Clicking Continue (Password)...")
        # Use sb.cdp
        sb.cdp.click(continue_button_selector)
        print("Adding long sleep after final continue click...")
        sb.sleep(12.0)

        # --- Verify Login ---
        print("Reconnecting WebDriver if needed (usually not after reconnect)...")
        # Use sb object
        if not sb.is_connected(): sb.reconnect(0.5)
        print("Waiting for successful login indicator...")
        # Use sb object
        sb.wait_for_element('a[href="/settings"]', timeout=40)
        print("Login appears successful.")
        sb.sleep(4.0)

        # --- Navigate & Extract ---
        keys_url = "https://openrouter.ai/settings/keys"
        print(f"Navigating to Keys page: {keys_url}")
        # Use sb object
        sb.open(keys_url)
        print("Waiting for Keys page elements...")
        # Use sb object
        sb.wait_for_element('h2:contains("API Keys")', timeout=35)
        print("Keys page loaded.")
        sb.sleep(4.0)

        print("Extracting cookies for domain 'clerk.openrouter.ai'...")
        # Use sb object
        all_cookies = sb.get_cookies()
        clerk_cookies = [
            cookie for cookie in all_cookies
            if cookie.get('domain') == 'clerk.openrouter.ai'
        ]

        if not clerk_cookies:
            print("WARNING: No cookies found for domain 'clerk.openrouter.ai'.")
            sb.fail("No cookies found for domain 'clerk.openrouter.ai'.")
        else:
            print(f"Found {len(clerk_cookies)} cookies for the domain.")

        output_file = "openrouter_cookies.json"
        print(f"Saving cookies to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(clerk_cookies, f, indent=4)
        print(f"Successfully extracted and saved cookies to {output_file}")

# Handles exceptions outside the SB block or during SB init
except Exception as e:
    print(f"\nAn critical error occurred: {e}")
    print(f"::error::Test failed during execution: {e}")
    # SB with test=True handles screenshots automatically on failure/error
    sys.exit(1)


# --- Pytest Integration (Keep this for running via pytest) ---
class OpenRouterCookieExtractor(BaseCase):
    def test_verify_cookie_file_creation(self):
        print("\nVerifying if cookie file was created by the SB block...")
        output_file = "openrouter_cookies.json"
        if not os.path.exists(output_file):
            # Try to access logs from the SB run if possible (might be tricky)
            log_path = "./latest_logs/" # Default log path
            screenshot_path = os.path.join(log_path, "test_verify_cookie_file_creation", "error_screenshot.png") # Example path structure
            if os.path.exists(log_path):
                 print(f"::warning::Main logic failed. Check logs in {log_path} or the GitHub Actions artifacts if available.")
                 if os.path.exists(screenshot_path):
                     print(f"::warning::An error screenshot might be available at {screenshot_path}")
            self.fail(f"Cookie file '{output_file}' was NOT created! Main logic failed.")
        else:
            print(f"Cookie file '{output_file}' was created successfully.")
            try:
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        self.fail("Cookie file content is not a list!")
                    print("Cookie file content seems valid (it's a list).")
            except Exception as json_err:
                 self.fail(f"Error reading/verifying cookie file: {json_err}")
