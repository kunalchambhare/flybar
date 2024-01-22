from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
import os
import odoorpc
import base64
import shutil
from func_timeout import func_timeout, FunctionTimedOut
from config import selenium_config


class SeleniumProcesses:
    def __init__(self):

        chrome_options = webdriver.ChromeOptions()

        self.download_directory = selenium_config.get('DOWNLOAD_DIRECTORY')
        self.move_path = selenium_config.get('MOVE_PATH')

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
        self.goflow_url = selenium_config.get('GOFLOW_URL')
        self.goflow_username = selenium_config.get('GOFLOW_USERNAME')
        self.goflow_password = selenium_config.get('GOFLOW_PASSWORD')

        # ODOORPC CREDENTIALS
        self.odoo_username = selenium_config.get('ODOO_USERNAME')
        self.odoo_password = selenium_config.get('ODOO_PASSWORD')
        self.odoo_url = selenium_config.get('ODOO_URL')
        self.odoo_port = selenium_config.get('ODOO_PORT')
        self.odoo_db = selenium_config.get('ODOO_DATABASE')

    def login(self):
        self.driver.get(self.goflow_url)
        self.driver.find_element(By.NAME, "userName").send_keys(self.goflow_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.goflow_password)
        self.driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()

    def process_1(self, vals):
        try:
            self.login()
        except Exception as e:
            return False, e, "Login Failed"

        print("LOGIN SUCCESSFUL", vals)

        try:
            func_timeout(45, self.execute_process_1, args=(self.driver, vals))
        except FunctionTimedOut:
            if self.driver is not None:
                self.driver.quit()
            try:
                self._update_failed_status(vals)
                return False, "Session timed out after 45 seconds", "Process Failed Status Updated to Odoo"
            except Exception as e_2:
                return False, f"Session timed out after 45 seconds {str(e_2)}", "Process Failed Status Update Failed"
        except Exception as e:
            if self.driver is not None:
                self.driver.quit()
            try:
                self._update_failed_status(vals)
                return False, e, "Process Failed Status Updated to Odoo"
            except Exception as e_2:
                return False, f"{str(e)} {str(e_2)}", "Process Failed Status Update Failed"

        print("Selenium Process Successful")

        try:
            self.upload_document(vals)
        except Exception as e:
            return False, e, "Process Completed but document uploading failed"

        return True, "Document Uploaded", "Process Completed"

    def execute_process_1(self, driver, vals):
        actions = ActionChains(self.driver)
        order_name = vals.get("order_name")
        weight = vals.get("weight")
        length = vals.get("length")
        width = vals.get("width")
        height = vals.get("height")

        self.driver.find_element(By.XPATH, "//li[@data-bind='click: orderTotals.goto.pick']").click()
        self.driver.find_element(By.XPATH, "//input[@placeholder='Search']").send_keys(order_name)

        order_name_elements = self.driver.find_elements(By.XPATH, "//td[normalize-space()='" + order_name + "']")
        if len(order_name_elements) == 0:
            raise ValueError("Order Not Found")
        elif len(order_name_elements) > 1:
            raise ValueError("Multiple Orders Found")
        else:
            order_name_elements[0].click()
        sleep(2)
        self.driver.find_element(By.XPATH,
                                 "(//button[@class='button-secondary button-icon icon-more tooltip-wrapper dropdown-toggle'])[1]").click()

        self.driver.find_element(By.XPATH, "//a[normalize-space()='Pack & Ship']").click()
        self.driver.find_element(By.XPATH, "//button[normalize-space()='Pack All']").click()

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
        sleep(4)
        ship_close_button = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Ship & Close']")
        if not len(ship_close_button):
            raise ValueError("Ship and Close Button not found")
        ship_close_button[0].click()
        sleep(3)
        self.driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
        sleep(2)
        self.driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
        sleep(2)
        download_button = self.driver.find_element(By.XPATH,
                                                   "//button[@class='button-secondary button-icon tooltip-wrapper icon-document']")
        actions.click(download_button).perform()
        sleep(2)
        self.driver.find_element(By.XPATH, "//a[normalize-space()='Download All']").click()
        sleep(3)
        self.driver.quit()

    def upload_document(self, vals):
        picking_id = vals.get('picking')
        substring = vals.get('order_name')
        task_id = vals.get('ID')

        files_in_directory = os.listdir(self.download_directory)
        found_file_path = False
        matching_files = [file for file in files_in_directory if substring in file]

        if matching_files:
            found_file_path = os.path.join(self.download_directory, matching_files[0])

        if found_file_path:
            success, odoo_obj = self.connect_odoo_rpc()
            if success:
                picking_obj = odoo_obj.env['stock.picking']
                go_flow_packaging_update_log = odoo_obj.env['go.flow.packaging.update.log']
                with open(found_file_path, "rb") as zip_file:
                    data = zip_file.read()
                    picking_obj.write([int(picking_id)],
                                      {'goflow_document': base64.b64encode(data or b'').decode("ascii"),
                                       'goflow_routing_status': 'doc_generated'})
                go_flow_packaging_update_log_id = go_flow_packaging_update_log.search(
                    [('order_ref', '=', int(task_id))], limit=1)
                go_flow_packaging_update_log.write(go_flow_packaging_update_log_id[0], {'request_status': 'completed'})
            else:
                raise odoo_obj

            if not os.path.exists(self.move_path):
                os.mkdir(self.move_path)
            shutil.move(found_file_path, self.move_path + '/' + matching_files[0])

    def _update_failed_status(self, vals):
        success, odoo_obj = self.connect_odoo_rpc()
        picking_id = vals.get('picking')
        task_id = vals.get('ID')
        if success:
            picking_obj = odoo_obj.env['stock.picking']
            go_flow_packaging_update_log = odoo_obj.env['go.flow.packaging.update.log']
            picking_obj.write([int(picking_id)], {'goflow_routing_status': 'require_manual_shipment'})
            go_flow_packaging_update_log_id = go_flow_packaging_update_log.search([('order_ref', '=', int(task_id))],
                                                                                  limit=1)
            go_flow_packaging_update_log.write(go_flow_packaging_update_log_id[0], {'request_status': 'update_failed'})
        else:
            raise odoo_obj

    def connect_odoo_rpc(self):
        try:
            odoo = odoorpc.ODOO(self.odoo_url, port=self.odoo_port)
            odoo.login(self.odoo_db, self.odoo_username, self.odoo_password)
            return True, odoo
        except Exception as e:
            return False, e
