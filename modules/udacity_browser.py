from .browser import Browser
import time
from selenium.common.exceptions import TimeoutException

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

    def get_is_passed(self, submission_id, wait=1):
        url = self.REVIEW_URL_T.format(submission_id)
        print("Checking if this review had passed: {}".format(url))
        self.driver.get(url)
        css_classes = ["result-label", "h-slim-top", "ng-binding"]
        status = self._find_els_by_classes(tag="h2", classes=css_classes, operator="and")[0]
        print("Wait for {} seconds...".format(wait))
        time.sleep(wait)
        if "Requires Changes" in status.text:
            return False
        else:
            return True

    def get_graded_version(self, submission_id=None, max_graded_version=2, wait=1):
        """ Get project's graded version.

        Rejected projects are not taken into account.
        """
        if submission_id is not None:
            url = self.REVIEW_URL_T.format(submission_id)
            print("Checking the grade of this review: {}".format(url))
            self.driver.get(url)

        try:
            # Find the History tab (a href with text "History" whose ancestor
            # does not have a class "ng-hide").
            history = self._find_el_by_xpath(
                "//a[contains(normalize-space(text()),'History')" + \
                " and not(ancestor::*[contains(@class, 'ng-hide')])]")
            print("History found")
            history.click()

            # Find review links whose ancestor does not have a class "ng-hide"/
            review_links = self._find_els_by_xpath(
                "//a[contains(@class, 'review-list-name')" + \
                " and not(ancestor::*[contains(@class, 'ng-hide')])]"
            )

        except TimeoutException:
            print("History not found")
            return 1

        # Find this review's version (not ungraded version) i.e. h2 with class
        # 'current-review-name' whose ancestor does not have a class "ng-hide",
        # then get its first span.
        this_review = self._find_el_by_xpath(
            "//h2[contains(@class, 'current-review-name')" + \
            " and not(ancestor::*[contains(@class, 'ng-hide')])]/span[1]"
        )
        version = int(this_review.text.split("#")[1])

        other_versions = [int(l.text.split("#")[1]) for l in review_links]
        other_versions.reverse()
        other_ids = [l.get_attribute('href').split("/")[-1] for l in review_links]
        other_ids.reverse()
        other_submissions = dict(zip(other_versions, other_ids))
        print("Found submission Ids:")
        print(other_submissions)
        graded_version = 1
        for k in other_submissions:
            if k < version:
                if self.is_graded(other_submissions[k]):
                    graded_version += 1
                    if graded_version > max_graded_version:
                        graded_version = ">{}".format(max_graded_version)
                        break

        print("Graded version: {}".format(graded_version))
        print("Wait for {} seconds...".format(wait))
        time.sleep(wait)
        return graded_version

    def is_graded(self, submission_id, wait=1):
        url = self.REVIEW_URL_T.format(submission_id)
        print("Checking if this review was graded: {}".format(url))
        self.driver.get(url)

        try:
            # Get the un-hidden "Unable to review" element:
            ungraded_element = self._find_el_by_xpath(
                "//h2[contains(normalize-space(text()),'Unable to review')" +
                " and not(ancestor::*[contains(@class, 'ng-hide')])]"
            )
            print("Review was ungraded")
            print("Wait for {} seconds...".format(wait))
            time.sleep(wait)
            return False
        except TimeoutException:
            print("Review was graded")
            print("Wait for {} seconds...".format(wait))
            time.sleep(wait)
            return True
