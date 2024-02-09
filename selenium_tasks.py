from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import base64
import shutil
from func_timeout import func_timeout, FunctionTimedOut
from config import selenium_config
import json


class SeleniumProcesses:
    def __init__(self):

        chrome_options = webdriver.ChromeOptions()

        self.download_directory = selenium_config.get('DOWNLOAD_DIRECTORY')

        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_directory,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        })
        chrome_options.add_argument("--disable-popup-blocking")
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(15)

        # GO FLOW CREDENTIALS
        self.goflow_url = None
        self.goflow_username = None
        self.goflow_password = None
        self.process_type = None
        self.log = []

    def login(self, cron_db_id):
        config = selenium_config.get(f'goflow_cred_{cron_db_id}')
        self.goflow_url = config.get('GOFLOW_URL')
        self.goflow_username = config.get('GOFLOW_USERNAME')
        self.goflow_password = config.get('GOFLOW_PASSWORD')
        self.driver.get(self.goflow_url)
        self.driver.find_element(By.NAME, "userName").send_keys(self.goflow_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.goflow_password)
        self.driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()

    def process_order(self, vals, cron_db_id):
        try:
            self.login(cron_db_id)
        except Exception as e:
            self.log.append(f"<p>Login Failed with error: {str(e)}</p>")
            return False, str(e), "Login Failed"

        self.log.append("<p>Login Successful</p>")

        try:
            func_timeout(180, self.execute_process, args=(self.driver, vals))
        except FunctionTimedOut:
            if self.driver is not None:
                self.driver.quit()
            self.log.append("<p>Session timed out after 180 seconds</p>")
            return False, "Session timed out after 180 seconds", "Process Failed"
        except Exception as e:
            if self.driver is not None:
                self.driver.quit()
            self.log.append(f"<p>Error {str(e)}. Process Failed Status Update Failed</p>")
            return False, e, "Process Failed"

        self.log.append(f"<p>Selenium Process Complete</p>")

        return True, "Process Completed", "Process Completed"

    def execute_process(self, driver, vals):
        actions = ActionChains(self.driver)
        order_name = vals.get("order_name")
        weight = vals.get("weight")
        length = vals.get("length")
        width = vals.get("width")
        height = vals.get("height")
        self.process_type = vals.get('main_operation_type')

        self.find_order(order_name)

        self.log.append(f"<p>Order found.</p>")

        lines = json.loads(vals.get('line_json_data'))
        self.log.append(f"<p>Started for Process Type: {self.process_type}</p>")

        if self.process_type == 'all':
            self.do_pack_all(weight, length, width, height)

        elif self.process_type == 'is_separate_box':
            self.do_pack_in_separate_box(actions)

        elif self.process_type == 'mixed':
            self._process_packages(lines.get('packages'))

        self.log.append(f"<p>Done for Process Type: {self.process_type}</p>")

        sleep(3)
        self.download_document(actions)
        self.driver.quit()

    def find_order(self, order_name):
        sleep(1)
        self.driver.find_element(By.XPATH, "//li[@data-bind='click: orderTotals.goto.pick']").click()
        self.driver.find_element(By.XPATH, "//input[@placeholder='Search']").send_keys(order_name)

        order_name_elements = self.driver.find_elements(By.XPATH, "//td[normalize-space()='" + order_name + "']")
        if len(order_name_elements) == 0:
            self.log.append(f"<p>Order not found</p>")
            raise Exception("Order Not Found")
        elif len(order_name_elements) > 1:
            self.log.append(f"<p>Multiple orders found</p>")
            raise Exception("Multiple Orders Found")

        order_name_elements[0].click()
        sleep(1)
        self.driver.find_element(By.XPATH,
                                 "(//button[@class='button-secondary button-icon icon-more tooltip-wrapper dropdown-toggle'])[1]").click()
        self.driver.find_element(By.XPATH, "//a[normalize-space()='Pack & Ship']").click()
        sleep(1)

    def do_pack_all(self, weight, length, width, height):
        try:
            self.driver.find_element(By.XPATH, "//button[normalize-space()='Pack All']").click()
            self.log.append(f"<p>Clicked Pack All</p>")
        except Exception as e:
            self.log.append(f"<p>Error in Clicking Pack ALl</p>")
            raise Exception(e)

        try:
            weight_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").get_attribute("value")
            if not float(weight_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").send_keys(str(weight))

            lenght_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").get_attribute("value")
            width_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").get_attribute("value")
            height_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").get_attribute("value")

            if not float(lenght_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").send_keys(str(length))
            if not float(width_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").send_keys(str(width))
            if not float(height_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").send_keys(str(height))
            self.log.append(f"<p>Added Dimensions</p>")
        except Exception as e:
            self.log.append(f"<p>Dimension update failed</p>")
            raise Exception(e)

        sleep(4)

        ship_close_button = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Ship & Close']")

        if not len(ship_close_button):
            prepare_and_ship = self.driver.find_elements(By.XPATH,
                                                         "//button[normalize-space()='Prepare Shipment & Close']")
            if not len(prepare_and_ship):
                raise Exception("Ship and Close Button and Prepare Shipment & Close not found")
            prepare_and_ship[0].click()
        else:
            ship_close_button[0].click()
            self.log.append(f"<p>Clicked Ship & Close.</p>")
            sleep(1)
            self.driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
            sleep(1)
            self.driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
            self.log.append(f"<p>Closed two dialogue box.</p>")
            sleep(1)

    def do_pack_in_separate_box(self, actions):
        self.driver.find_element(By.XPATH,
                                 "//button[@class='button-secondary button-small button-icon icon-caret-down dropdown-toggle']").click()

        anchor_element = self.driver.find_element(By.XPATH, "//a[@href='#'][normalize-space()='...in Separate Boxes']")
        try:
            anchor_element.click()
        except Exception as e:
            self.log.append(f"<p>In separate box button click issue.</p>")
            raise Exception(f"In separate box button click issue {e}")
        try:
            side_widow = self.driver.find_element(By.XPATH,
                                                  "//div[@class='window-column-narrow']//div[@class='grid-scroller']")

            actions.move_to_element(side_widow).perform()
            sleep(1)
            ship_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Ship']")

            if not ship_button.is_enabled():
                self.log.append(f"<p>Ship Button not enabled.</p>")
                raise Exception("Ship not enabled!")
            else:
                ship_button.click()
                self.log.append(f"<p>Shipped.</p>")

            sleep(4)
        except Exception as e:
            self.log.append(f"<p>Couldn't click Ship button.</p>")
            raise Exception(f"Couldn't click Ship button {e}")

    def _process_packages(self, packages):
        order_total_quantity = sum(
            int(product.get('quantity')) for package in packages for product in package.get('product_lines'))

        done_qty = 0
        for package in packages:
            self.log.append(f"Started package: {package.get('package_name')}<br>")
            product_lines = package.get('product_lines')
            for product in product_lines:
                try:
                    self.log.append(
                        f"Adding Product: {product.get('product_name')} with quantity: {product.get('quantity')}<br>")
                    item_number_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Item Number']")
                    item_number_input.clear()
                    item_number_input.send_keys(product.get('product_name'))
                    quantity_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Quantity']")
                    quantity_input.clear()
                    quantity_input.send_keys(int(product.get('quantity')))
                    quantity_input.send_keys(Keys.ENTER)
                    sleep(0.5)
                    done_qty += int(product.get('quantity'))
                except Exception as e:
                    self.log.append(f"<p>Error in adding product {product.get('product_name')} {e}</p>")
                    raise Exception(e)

            sleep(1)
            self.log.append(f"Created package: {package.get('package_name')}<br>")
            try:
                self.pack_box(order_total_quantity, done_qty)
                self.log.append(f"Closed package: {package.get('package_name')}<br><br>")
            except Exception as e:
                self.log.append(f"<p>Error in closing the package: {package.get('package_name')}</p>")
                raise Exception(e)

    def pack_box(self, order_total_quantity, done_qty):
        if order_total_quantity > done_qty:
            sleep(1)
            self.driver.find_element(By.XPATH, "//button[normalize-space()='Close Box']").click()
            sleep(1)
            self.driver.find_element(By.XPATH, "//button[normalize-space()='Save Label']").click()
            sleep(1)
        elif order_total_quantity == done_qty:
            sleep(1)
            self.driver.find_element(By.XPATH,
                                     "//button[normalize-space()='Prepare Shipment & Close']").click()
            sleep(1)

    def download_document(self, actions):
        try:
            download_button = self.driver.find_element(By.XPATH,
                                                       "//button[@class='button-secondary button-icon tooltip-wrapper icon-document']")
            actions.click(download_button).perform()
            sleep(1)
            self.driver.find_element(By.XPATH, "//a[normalize-space()='Download All']").click()
        except Exception as e:
            self.log.append(f"<p>Error in Downloading document: {e}</p>")
            raise Exception(e)
        sleep(3)
        self.log.append(f"<p>Document Downloaded</p>")

    def go_to_homepage(self):
        self.driver.find_element(By.XPATH, "//span[@class='main-logo clickable']").click()
        self.driver.refresh()
