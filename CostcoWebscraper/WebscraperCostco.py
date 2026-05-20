import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from win10toast import ToastNotifier
from datetime import datetime
import customtkinter as ctk
import time, random, winsound, sys, os, tkinter.messagebox, threading, json

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ScraperUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🕷️ Costco Scraper")
        self.geometry("500x350")
        self.url = None
        self.xpath = None
        self.attribute = None
        self.sleep_range = (0, 0)
        self.config_file = "scraper_config.json"
        self.stop_requested = False
        self.ri = None
        self.driver = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # URL Input
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Product URL",  width=400)
        self.url_entry.pack(pady=20)

        # XPath Input
        self.xpath_entry = ctk.CTkEntry(self, placeholder_text="Elements XPath", width=400)
        self.xpath_entry.pack(pady=10)

        #Range Input Label
        self.range_label = ctk.CTkLabel(self, text="Run Time Range", font=("Arial", 14))
        self.range_label.pack(padx=5)

        # Sleep Time Range Frame
        self.sleep_frame = ctk.CTkFrame(self)
        self.sleep_frame.pack(pady=10)

        # Attribute Entry
        self.attribute_entry = ctk.CTkEntry(self.sleep_frame, placeholder_text="Attribute", width=100)
        self.attribute_entry.pack(side="left", padx=5)

        # Sleep Start Entry
        self.sleep_start_entry = ctk.CTkEntry(self.sleep_frame, placeholder_text="Start (sec)", width=100)
        self.sleep_start_entry.pack(side="left", padx=5)

        # Sleep End Entry
        self.sleep_end_entry = ctk.CTkEntry(self.sleep_frame, placeholder_text="End (sec)", width=100)
        self.sleep_end_entry.pack(side="left", padx=5)

        # Start & Stop Button
        self.start_stop_btn = ctk.CTkButton(self, text="Start Scraping", fg_color="steelblue", command=self.start_scraper)
        self.start_stop_btn.pack(side="bottom",pady=30)

        if os.path.exists("scraper_config.json"):
            url, xpath, attribute, (sleep_start, sleep_end) = self.load_inputs()
            self.url_entry.insert(0, url)
            self.xpath_entry.insert(0, xpath)
            self.attribute_entry.insert(0, attribute)
            self.sleep_start_entry.insert(0, str(sleep_start))
            self.sleep_end_entry.insert(0, str(sleep_end))

        self.status_label = ctk.CTkLabel(self, text="Status: Idle 💤")
        self.status_label.pack(side="bottom", pady=1)

    def save_inputs(self):
        config = {
            "url": self.url,
            "xpath": self.xpath,
            "attribute": self.attribute,
            "sleep_start": self.sleep_range[0],
            "sleep_end": self.sleep_range[1]
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            print("✅ Inputs successfully saved.")
        except Exception as e:
            print(f"❌ Error saving inputs: {e}")

    def load_inputs(self):
        try:
            with open(self.config_file, "r") as file:
                data = json.load(file)
                self.url = data.get("url", "")
                self.xpath = data.get("xpath", "")
                self.attribute = data.get("attribute", "")
                self.sleep_range = (
                    data.get("sleep_start", 0),
                    data.get("sleep_end", 0)
                )
                print("🔄 Inputs successfully loaded.")
                return self.url, self.xpath, self.attribute, self.sleep_range
        except Exception as e:
            print(f"⚠️ Failed to load inputs: {e}")

    def start_scraper(self):
        try:
            self.status_label.configure(text="Status: Running ✅")
            self.disable_start_button()
            self.stop_requested = False
            url = self.url_entry.get()
            xpath = self.xpath_entry.get()
            attribute = self.attribute_entry.get()
            sleep_start = int(self.sleep_start_entry.get())
            sleep_end = int(self.sleep_end_entry.get())

            self.ri = ScraperRunner(
                url,
                xpath,
                attribute,
                (sleep_start, sleep_end),
                lambda: self.stop_requested
            )

            def run_and_finish():
                self.ri.run()
                self.enable_start_button()
                self.status_label.configure(text="Status: Idle 💤")

            threading.Thread(target=run_and_finish, daemon=True).start()

        except Exception as e:
            self.enable_start_button()
            tkinter.messagebox.showerror("Error", f"⛔ {e}")

    def on_close(self):
        try:
            self.ri.shutdown()  # Stop the driver cleanly
            self.url = self.url_entry.get()
            self.xpath = self.xpath_entry.get()
            self.attribute = self.attribute_entry.get()
            self.sleep_range = (
                int(self.sleep_start_entry.get()),
                int(self.sleep_end_entry.get())
            )
            self.save_inputs()
            print("📝 Inputs saved to JSON config.")
        except Exception as e:
            print(f"⚠️ Failed during close: {e}")
        finally:
            self.destroy()

    def request_stop(self):
        self.stop_requested = True
        self.save_inputs()
        self.status_label.configure(text="Status: Stop Requested 🔴")
        self.ri.shutdown()
        self.enable_start_button()

    def disable_start_button(self):
        self.start_stop_btn.configure(text="Stop Scraping", fg_color="red", command=self.request_stop)

    def enable_start_button(self):
        self.start_stop_btn.configure(text="Start Scraping", fg_color="steelblue", command=self.start_scraper)

class ScraperRunner:
    def __init__(self, url, xpath, attribute, sleep_range, should_stop):
        self.url = url
        self.xpath = xpath
        self.attribute = attribute
        self.sleep_range = sleep_range
        self.should_stop = should_stop
        self.driver = None
        self._orig_stdout = sys.stdout

    def setup_logger(self):
        log_dir = os.path.join(os.getcwd(), "Logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "costco_log.txt")

        class Logger:
            def __init__(self, file_path, orig_stdout):
                self.terminal = orig_stdout
                self.log = open(file_path, "a", encoding="utf-8")

            def write(self, message):
                self.terminal.write(message)
                self.log.write(message)

            def flush(self):
                self.log.flush()

        sys.stdout = Logger(log_path, self._orig_stdout)

    def capture_screenshot(self, name_prefix="screenshot"):
        folder = os.path.join(os.getcwd(), "Screenshots")
        os.makedirs(folder, exist_ok=True)
        safe_prefix = name_prefix.replace(" ", "_")
        path = os.path.join(folder, f"{safe_prefix}_{self.get_timestamp()}.png")
        self.driver.save_screenshot(path)
        print(f"🖼️ Screenshot saved: {path}")

    def get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def notify(self, title, message):
        toaster = ToastNotifier()
        toaster.show_toast(title, message, icon_path=None, threaded=True)

    def build_driver(self):
        if self.driver:  # Optional: avoid re-instantiation
            return self.driver
        options = uc.ChromeOptions()
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        self.driver = QuietChrome(options=options, browser_executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

    def shutdown(self):
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Chrome driver shut down successfully.")
            except Exception as e:
                print(f"⚠️ Error while shutting down driver: {e}")
            finally:
                self.driver = None

        if sys.stdout is not self._orig_stdout:
            sys.stdout = self._orig_stdout
            print("🔄 Stdout restored.")

    def check_stock(self):
        print("⏱️" + self.get_timestamp() + ": Checking Product Status...")
        # self.capture_screenshot("before_check")
        try:
            wait = WebDriverWait(self.driver, 20)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            wait.until(lambda d: d.find_element(By.XPATH, self.xpath))
            button = self.driver.find_element(By.XPATH, self.xpath)
            status = button.get_attribute(self.attribute)
            if status == "Add to Cart":
                self.notify("✅ Costco Product Available!", f"In stock as of {self.get_timestamp()}")
                print("✅" + self.get_timestamp() + ": Item is in stock! Ending Script!")
                winsound.PlaySound('Time.wav', winsound.SND_FILENAME)
                return True
            else:
                print("❌" + self.get_timestamp() + f": Product status: {status}")
                return False
        except (TimeoutException, NoSuchElementException) as e:
            print("⚠️" + self.get_timestamp() + f": Error: {type(e).__name__}")
            self.capture_screenshot("Exception Error")
            return False

        except Exception as e:
            print("🔥" + self.get_timestamp() + f": Unhandled error: {e}")
            self.capture_screenshot("UnhandledError")
            return False

    def simulate_scroll_and_hover(self):
        # Simulate scroll with stop checks
        for i in range(0, 1400, random.randint(80, 120)):
            if callable(self.should_stop) and self.should_stop():
                print("🛑 Stopped during scrolling simulation.")
                return
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(random.uniform(0.2, 0.6))

        # Find visible elements
        elements = self.driver.find_elements(By.CSS_SELECTOR, "button,a,input,div")
        visible_elements = [el for el in elements if el.is_displayed() and el.size['height'] > 0]

        # Simulate hover and mouse wiggle with stop checks
        for _ in range(5):
            if callable(self.should_stop) and self.should_stop():
                print("🛑 Stopped during hover simulation.")
                return
            if visible_elements:
                target = random.choice(visible_elements)
                try:
                    ActionChains(self.driver).move_to_element(target).pause(
                        random.uniform(0.3, 1)
                    ).perform()
                    time.sleep(random.uniform(0.5, 1.2))

                    x = random.randint(50, 1200)
                    y = random.randint(50, 800)
                    self.driver.execute_script(f"""
                        var evt = new MouseEvent('mousemove', {{
                            clientX: {x},
                            clientY: {y},
                            bubbles: true
                        }});
                        document.dispatchEvent(evt);
                    """)
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    print(f"⚠️ Hover/wiggle simulation failed: {e}")

    def sleep_with_stop_check(self):
        sleep_time = random.randint(*self.sleep_range)
        minutes, seconds = divmod(sleep_time, 60)
        print(f"⏳{self.get_timestamp()}: Not in stock. Retrying in {minutes}m {seconds}s...")
        for _ in range(sleep_time):
            if self.should_stop():
                print("🛑 Stop requested during sleep.")
                return False
            time.sleep(1)
        return True

    def run(self):
        self.setup_logger()
        self.build_driver()
        self.driver.get(self.url)
        print("🚀 Scraper started.")

        self.driver.minimize_window()
        self.simulate_scroll_and_hover()
        try:
            while not self.should_stop():
                if self.check_stock():
                    break
                if not self.sleep_with_stop_check():
                    break
                self.driver.refresh()
                time.sleep(random.uniform(2.5, 3.1))
                self.simulate_scroll_and_hover()
        finally:
            self.shutdown()

class QuietChrome(uc.Chrome):
    def __del__(self):
        # Override to prevent double shutdown error
        try:
            if hasattr(self, '_del_called'):
                return
            self._del_called = True  # Optional: prevent re-entry
            # Optional: log or cleanup gently
            print("🔕 QuietChrome __del__ called.")
        except Exception(BaseException):
            pass  # Silently ignore any issues

ScraperUI().mainloop()