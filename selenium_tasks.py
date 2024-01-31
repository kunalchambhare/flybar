from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import odoorpc
import xmlrpc.client as xc
import base64
import shutil
from func_timeout import func_timeout, FunctionTimedOut
from config import selenium_config
import json


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
        odoo_connection_config = selenium_config.get('local_config')
        if odoo_connection_config:
            self.odoo_username = odoo_connection_config.get('ODOO_USERNAME')
            self.odoo_password = odoo_connection_config.get('ODOO_PASSWORD')
            self.odoo_url = odoo_connection_config.get('ODOO_URL')
            self.odoo_port = odoo_connection_config.get('ODOO_PORT')
            self.odoo_db = odoo_connection_config.get('ODOO_DATABASE')
            self.use_odoo_rpc = odoo_connection_config.get('use_odoo_rpc')

        self.process_type = None

    def login(self):
        self.driver.get(self.goflow_url)
        self.driver.find_element(By.NAME, "userName").send_keys(self.goflow_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.goflow_password)
        self.driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()

    def process_order(self, vals):
        try:
            self.login()
        except Exception as e:
            return False, e, "Login Failed"

        print("LOGIN SUCCESSFUL")

        try:
            func_timeout(300, self.execute_process, args=(self.driver, vals))
        except FunctionTimedOut:
            if self.driver is not None:
                self.driver.quit()
            try:
                self._update_failed_status(vals)
                return False, "Session timed out after 300 seconds", "Process Failed Status Updated to Odoo"
            except Exception as e_2:
                return False, f"Session timed out after 300 seconds {str(e_2)}", "Process Failed Status Update Failed"
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

    def execute_process(self, driver, vals):
        actions = ActionChains(self.driver)
        order_name = vals.get("order_name")
        weight = vals.get("weight")
        length = vals.get("length")
        width = vals.get("width")
        height = vals.get("height")

        self.find_order(order_name)
        print("ORDER FOUND!")

        self.process_type = vals.get('main_operation_type')
        lines = json.loads(vals.get('line_json_data'))
        if self.process_type == 'all':
            self.do_pack_all(weight, length, width, height)

        if self.process_type == 'is_separate_box':
            self.do_pack_in_separate_box(actions)

        if self.process_type == 'individual_separate_multi_box':
            self._process_individual_items_in_multi_box(lines)

        if self.process_type == 'individual_item_same_box':
            self._process_individual_items_in_same_box(lines)

        if self.process_type == 'split_multi_box':
            self._process_split_multi_box(lines, actions)

        if self.process_type == 'mixed':
            if lines.get('individual_separate_multi_box'):
                self._process_individual_items_in_multi_box(lines)
            if lines.get('individual_item_same_box'):
                self._process_individual_items_in_same_box(lines)
            if lines.get('split_multi_box'):
                self._process_split_multi_box(lines, actions)

        sleep(3)

        self.download_document(actions)

        self.driver.quit()

    def find_order(self, order_name):
        self.driver.find_element(By.XPATH, "//li[@data-bind='click: orderTotals.goto.pick']").click()
        self.driver.find_element(By.XPATH, "//input[@placeholder='Search']").send_keys(order_name)

        order_name_elements = self.driver.find_elements(By.XPATH, "//td[normalize-space()='" + order_name + "']")
        if len(order_name_elements) == 0:
            raise Exception("Order Not Found")
        elif len(order_name_elements) > 1:
            raise Exception("Multiple Orders Found")
        else:
            order_name_elements[0].click()
        sleep(2)
        self.driver.find_element(By.XPATH,
                                 "(//button[@class='button-secondary button-icon icon-more tooltip-wrapper dropdown-toggle'])[1]").click()

        self.driver.find_element(By.XPATH, "//a[normalize-space()='Pack & Ship']").click()

    def do_pack_all(self, weight, length, width, height):

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

    def do_pack_in_separate_box(self, actions):
        print("TEST")
        self.driver.find_element(By.XPATH,
                                 "//button[@class='button-secondary button-small button-icon icon-caret-down dropdown-toggle']").click()

        anchor_element = self.driver.find_element(By.XPATH, "//a[@href='#'][normalize-space()='...in Separate Boxes']")
        try:
            anchor_element.click()
        except:
            raise Exception("In separate box button disabled")
        side_widow = self.driver.find_element(By.XPATH,
                                              "//div[@class='window-column-narrow']//div[@class='grid-scroller']")

        actions.move_to_element(side_widow).perform()
        sleep(1)
        ship_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Ship']")

        if not ship_button.is_enabled():
            raise Exception("Ship not enabled!")
        else:
            ship_button.click()
        sleep(4)

    def _process_individual_items_in_multi_box(self, lines):
        packages = lines.get('individual_separate_multi_box')
        order_total_quantity = 0
        for package in packages:
            for product in package.get('product_lines'):
                order_total_quantity += int(product.get('quantity'))

        done_qty = 0
        for package in packages:
            product_lines = package.get('product_lines')
            for product in product_lines:
                product_td = self.driver.find_element(By.XPATH,
                                                      "//td[@class='grid-cell-text link-action break-words'][normalize-space()='" + product.get(
                                                          'product_name') + "']")
                parent_tr = product_td.find_element(By.XPATH, "..")
                for i in range(int(product.get('quantity'))):
                    parent_tr.find_element(By.XPATH, ".//i[contains(@class, 'icon-plus-circled-filled')]").click()
                done_qty += int(product.get('quantity'))
            sleep(1)
            print(order_total_quantity, done_qty)

            self.driver.find_element(By.XPATH, "//button[normalize-space()='Close Box']").click()
            save_label = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Save Label']")
            pack_shipment_and_close = self.driver.find_elements(By.XPATH,
                                                                "//button[normalize-space()='Prepare Shipment & Close']")
            if len(save_label) > 0:
                save_label[0].click()
                sleep(1)
            elif len(pack_shipment_and_close) > 0:
                pack_shipment_and_close[0].click()
                sleep(1)

    def _process_individual_items_in_same_box(self, lines):
        packages = lines.get('individual_item_same_box')
        order_total_quantity = 0
        for package in packages:
            for product in package.get('product_lines'):
                order_total_quantity += int(product.get('quantity'))

        done_qty = 0
        for package in packages:
            product_lines = package.get('product_lines')
            for product in product_lines:
                product_td = self.driver.find_element(By.XPATH,
                                                      "//td[@class='grid-cell-text link-action break-words'][normalize-space()='" + product.get(
                                                          'product_name') + "']")
                parent_tr = product_td.find_element(By.XPATH, "..")
                for i in range(int(product.get('quantity'))):
                    parent_tr.find_element(By.XPATH, ".//i[contains(@class, 'icon-plus-circled-filled')]").click()
                done_qty += int(product.get('quantity'))
            sleep(1)
            print(order_total_quantity, done_qty)

            self.driver.find_element(By.XPATH, "//button[normalize-space()='Close Box']").click()
            save_label = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Save Label']")
            pack_shipment_and_close = self.driver.find_elements(By.XPATH,
                                                                "//button[normalize-space()='Prepare Shipment & Close']")
            if len(save_label) > 0:
                save_label[0].click()
                sleep(1)
            elif len(pack_shipment_and_close) > 0:
                pack_shipment_and_close[0].click()
                sleep(1)

    def _process_split_multi_box(self, lines, actions):
        products = lines.get('split_multi_box')

        product_dict = {}

        for product in products:
            product_name = product.get('product_name')
            if not product_dict.get(product_name):
                product_dict[product_name] = {
                    'quantity': product.get('quantity'),
                    'total_splits': 1,
                    'box_type': product.get('box_type'),
                    'weight': product.get('weight'),
                    'length': product.get('length'),
                    'width': product.get('width'),
                    'height': product.get('height'),
                }
            else:
                product_dict[product_name]['total_splits'] += 1
                if product_dict[product_name]['quantity'] < product.get('quantity'):
                    product_dict[product_name]['quantity'] = product.get('quantity')
        print(product_dict)
        for key, value in product_dict.items():
            product_td = self.driver.find_element(By.XPATH,
                                                  "//td[@class='grid-cell-text link-action break-words'][normalize-space()='" + key + "']")
            parent_tr = product_td.find_element(By.XPATH, "..")
            pack_icon = parent_tr.find_element(By.XPATH, "//i[@class='icon-box-closed']")
            actions.move_to_element(pack_icon).perform()
            pack_icon.click()

            unit_per_box = self.driver.find_element(By.XPATH, "//input[@placeholder='Units per Box']")
            unit_per_box.send_keys(Keys.CONTROL + "a")  # Select all text
            unit_per_box.send_keys(Keys.BACKSPACE)
            unit_per_box.send_keys(
                int(value.get('quantity')))

            weight_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").get_attribute("value")
            if not float(weight_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").clear()
                sleep(4)
                self.driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").send_keys(int(value.get('weight')))

            length_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").get_attribute("value")
            width_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").get_attribute("value")
            height_val = self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").get_attribute("value")

            if not float(length_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Length']").send_keys(int(value.get('length')))
            if not float(width_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Width']").send_keys(int(value.get('width')))
            if not float(height_val):
                self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").clear()
                self.driver.find_element(By.XPATH, "//input[@placeholder='Height']").send_keys(int(value.get('height')))

            save_label = self.driver.find_elements(By.XPATH, "//button[normalize-space()='Save Label']")
            pack_shipment_and_close = self.driver.find_elements(By.XPATH,
                                                                "//button[normalize-space()='Prepare Shipment & Close']")
            if len(save_label) > 0:
                save_label[0].click()
                sleep(2)
            elif len(pack_shipment_and_close) > 0:
                pack_shipment_and_close[0].click()
                sleep(2)

    def download_document(self, actions):
        download_button = self.driver.find_element(By.XPATH,
                                                   "//button[@class='button-secondary button-icon tooltip-wrapper icon-document']")
        actions.click(download_button).perform()
        sleep(2)
        self.driver.find_element(By.XPATH, "//a[normalize-space()='Download All']").click()
        sleep(3)

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
                if self.use_odoo_rpc:
                    picking_obj = odoo_obj.env['stock.picking']
                    go_flow_packaging_update_log = odoo_obj.env['go.flow.packaging.update.log']
                    with open(found_file_path, "rb") as zip_file:
                        data = zip_file.read()
                        picking_obj.write([int(picking_id)],
                                          {'goflow_document': base64.b64encode(data or b'').decode("ascii"),
                                           'goflow_routing_status': 'doc_generated',
                                           'rpa_status': False})
                    go_flow_packaging_update_log_id = go_flow_packaging_update_log.search(
                        [('order_ref', '=', int(task_id))], limit=1)
                    go_flow_packaging_update_log.write(go_flow_packaging_update_log_id[0],
                                                       {'request_status': 'completed'})
                else:
                    uid = odoo_obj[0]
                    sock = odoo_obj[1]
                    with open(found_file_path, "rb") as zip_file:
                        data = zip_file.read()
                        sock.execute(self.odoo_db, uid, self.odoo_password, 'stock.picking', 'write', int(picking_id),
                                     {'goflow_document': base64.b64encode(data or b'').decode("ascii"),
                                      'goflow_routing_status': 'doc_generated',
                                      'rpa_status': False})
                    go_flow_log_id = sock.execute(self.odoo_db, uid, self.odoo_password, 'go.flow.packaging.update.log',
                                                  'search',
                                                  [('order_ref', '=', int(task_id))])

                    sock.execute(self.odoo_db, uid, self.odoo_password, 'go.flow.packaging.update.log', 'write',
                                 go_flow_log_id[0],
                                 {'request_status': 'completed'})
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
            picking_vals = {'goflow_routing_status': 'require_manual_shipment', 'rpa_status': False}
            go_flow_log_vals = {'request_status': 'update_failed'}
            if self.use_odoo_rpc:
                picking_obj = odoo_obj.env['stock.picking']
                go_flow_packaging_update_log = odoo_obj.env['go.flow.packaging.update.log']
                picking_obj.write([int(picking_id)], picking_vals)
                go_flow_packaging_update_log_id = go_flow_packaging_update_log.search(
                    [('order_ref', '=', int(task_id))],
                    limit=1)
                go_flow_packaging_update_log.write(go_flow_packaging_update_log_id[0], go_flow_log_vals)
            else:
                uid = odoo_obj[0]
                sock = odoo_obj[1]
                sock.execute(self.odoo_db, uid, self.odoo_password, 'stock.picking', 'write', int(picking_id),
                             picking_vals)

                go_flow_log_id = sock.execute(self.odoo_db, uid, self.odoo_password, 'go.flow.packaging.update.log',
                                              'search',
                                              [('order_ref', '=', int(task_id))])

                sock.execute(self.odoo_db, uid, self.odoo_password, 'go.flow.packaging.update.log', 'write',
                             go_flow_log_id[0],
                             go_flow_log_vals)
        else:
            raise odoo_obj

    def connect_odoo_rpc(self):
        try:
            if self.use_odoo_rpc:
                odoo = odoorpc.ODOO(self.odoo_url, port=self.odoo_port)
                odoo.login(self.odoo_db, self.odoo_username, self.odoo_password)
                return True, odoo
            else:
                sock_common = xc.ServerProxy(self.odoo_url + '/xmlrpc/common', allow_none=True)
                uid = sock_common.login(self.odoo_db, self.odoo_username, self.odoo_password)
                sock = xc.ServerProxy(self.odoo_url + '/xmlrpc/object', allow_none=True)
                return True, [uid, sock]
        except Exception as e:
            return False, e
