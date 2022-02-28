from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

class Browser:
    WAIT_VISIBILITY = 'visibility'
    WAIT_PRESENCE = 'presence'
    WAIT_CLICKABLE = 'clickable'
    WAIT_SELECTED = 'selected'

    def __init__(self, chromedriver_path="/usr/lib/chromium-browser/chromedriver"):
        self.chromedriver_path = chromedriver_path

    def connect(self):
        self.driver = webdriver.Chrome(self.chromedriver_path)

    def disconnect(self):
        self.driver.quit()

    def _find_el_by_text(self, text, tag="*", **kwargs):
        el = self._find_el_by_xpath(
            "//{}[contains(normalize-space(text()),'{}')]".format(tag, text), **kwargs)
        return el

    def _find_el_by_tag(self, tag, **kwargs):
        el = self._find_el_by_xpath("//"+ tag +"", **kwargs)
        return el

    def _find_el_by_id(self, id, tag="*", **kwargs):
        el = self._find_el_by_xpath("//{}[@id='{}']".format(tag, id), **kwargs)
        return el

    def _find_els_by_classes(self, classes=[], operator="and", tag="*", **kwargs):
        class_contains = []
        for c in classes:
            class_contains.append("contains(@class, '{}')".format(c))
        class_contains_str = " {} ".format(operator).join(class_contains)
        xpath = "//{}[{}]".format(tag, class_contains_str)
        el = self._find_els_by_xpath(xpath, **kwargs)
        return el

    def _find_el_by_xpath(self, xpath, wait='clickable', wait_max_seconds=5):
        """
        Args:
            wait (str): 'clickable', None
        """
        if wait is not None:
            wdwait = WebDriverWait(self.driver, wait_max_seconds)

        if wait==self.WAIT_CLICKABLE:
            el = wdwait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        else:
            el = self.driver.find_element(By.XPATH, xpath)
        return el

    def _find_els_by_xpath(self, xpath, wait='visibility', wait_max_seconds=5):
        """
        Args:
            wait (str): 'visibility', 'presence', None
        """
        if wait is not None:
            wdwait = WebDriverWait(self.driver, wait_max_seconds)

        if wait==self.WAIT_VISIBILITY:
            els = wdwait.until(
                EC.visibility_of_all_elements_located((By.XPATH, xpath))
            )
        elif wait==self.WAIT_PRESENCE:
            els = wdwait.until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        else:
            els = self.driver.find_elements(By.XPATH, xpath)
        return els
