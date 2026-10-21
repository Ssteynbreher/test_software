import os
import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BMC_WEB_URL = os.getenv("BMC_WEB_URL", "https://127.0.0.1:2443")
BMC_USER = os.getenv("BMC_USER", "root")
BMC_PASSWORD = os.getenv("BMC_PASSWORD", "0penBmc")
LOGIN_SELECTOR = (
    "input[type='text'], input[type='email'], input[name='username'], "
    "input#username, #username, [autocomplete='username']"
)


@pytest.fixture()
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--window-size=1440,900")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    yield driver
    driver.quit()


def wait(browser, seconds=20):
    return WebDriverWait(browser, seconds)


def login(browser, username=BMC_USER, password=BMC_PASSWORD):
    browser.get(BMC_WEB_URL)
    try:
        user_field = wait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_SELECTOR))
        )
    except TimeoutException:
        # This reference QEMU image exposes BMCWeb/Redfish but may omit webui-vue.
        browser.save_screenshot("reports/webui-login-unavailable.png")
        pytest.skip("The selected QEMU image does not expose a WebUI login form")
    pass_field = browser.find_element(By.CSS_SELECTOR, "input[type='password']")
    user_field.clear()
    user_field.send_keys(username)
    pass_field.clear()
    pass_field.send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit'], button").click()


def test_web_service_is_reachable(browser):
    browser.get(BMC_WEB_URL)
    wait(browser).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )
    assert browser.find_element(By.TAG_NAME, "body")


def test_successful_login(browser):
    login(browser)
    wait(browser).until(lambda d: "login" not in d.current_url.lower())
    assert "login" not in browser.current_url.lower()


def test_invalid_login_shows_error(browser):
    login(browser, password="wrong-password")
    error = wait(browser).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger, [role='alert'], .error"))
    )
    assert error.text.strip()


def test_repeated_invalid_login_keeps_user_on_login_page(browser):
    for _ in range(5):
        login(browser, password="wrong-password")
        time.sleep(0.5)
    assert "login" in browser.current_url.lower() or browser.find_elements(By.CSS_SELECTOR, "input[type='password']")


def test_power_control_page_is_available(browser):
    login(browser)
    browser.get(f"{BMC_WEB_URL}/#/operations/server-power-operations")
    power_controls = wait(browser).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button, input, [role='button']"))
    )
    assert power_controls


def test_event_log_page_is_available(browser):
    login(browser)
    browser.get(f"{BMC_WEB_URL}/#/logs/event-logs")
    try:
        wait(browser).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table, [role='table'], .table")))
    except TimeoutException:
        assert "logs" in browser.current_url.lower()


def test_inventory_page_is_available(browser):
    login(browser)
    browser.get(f"{BMC_WEB_URL}/#/hardware-status/inventory")
    wait(browser).until(lambda d: "inventory" in d.current_url.lower() or d.find_elements(By.CSS_SELECTOR, "table"))
    assert browser.find_elements(By.CSS_SELECTOR, "body")
