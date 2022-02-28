from .browser import Browser
import time

class UdacityBrowser(Browser):
    REVIEW_URL_T = "https://review.udacity.com/#!/reviews/{}"
    def login(self, username, password, wait=1):
        url = "https://auth.udacity.com/sign-in?next=https%3A%2F%2Fmentor-dashboard.udacity.com%2F"
        print("Logging in...")
        self.driver.get(url)
        email_el = self._find_el_by_id("email")
        email_el.send_keys(username)
        password_el = self._find_el_by_id("revealable-password")
        password_el.send_keys(password)
        text = "Sign In"
        submit_el = self._find_el_by_xpath(
            "//span[contains(normalize-space(text()),'"+ text +"')]/parent::button")
        submit_el.click()
        print("Wait for {} seconds...".format(wait))
        time.sleep(wait)

    def get_feedbacks(self, wait=1):
        url = "https://review-api.udacity.com/api/v1/me/student_feedbacks"
        self.driver.get(url)
        print("Wait for {} seconds...".format(wait))
        return self.driver.find_element_by_css_selector('body > pre').text

    def is_meet_specifications(self, submission_id, wait=1):
        url = self.REVIEW_URL_T.format(submission_id)
        print("Checking review page {}".format(url))
        self.driver.get(url)
        css_classes = ["result-label", "h-slim-top", "ng-binding"]
        status = self._find_els_by_classes(tag="h2", classes=css_classes, operator="and")[0]
        print("Wait for {} seconds...".format(wait))
        time.sleep(wait)
        if "Requires Changes" in status.text:
            return False
        else:
            return True
