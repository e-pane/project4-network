from network.models import User, Post
import os
import pytest
from selenium import webdriver
import selenium_utils
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver_factory():
    
    driver_path = os.path.abspath(os.path.join(os.path.dirname(__file__)),"selenium_drivers", "chromedriver.exe")
    driver = webdriver.Chrome(service = Service(driver_path))
    
    yield driver

    driver.quit() 
    
@pytest.fixture
def user_factory():
    def create_user():
        try:
            user1 = User.objects.get(username="testuser1")
        except User.DoesNotExist:
            user1 = User.objects.create_user(username="testuser1", password="testpass1")
            
        try:
            user2 = User.objects.get(username="testuser2")
        except User.DoesNotExist:
            user2 = User.objects.create_user(username="testuser2", password="testpass2")

        users = {"user1":user1, "user2":user2}

        return users
    return create_user

class FrontendTestSession:
    def __init__(self,driver):
        self.driver = driver
        self.username = None
        self.user_id = None

    def login(self, username, password, expected_url_fragment=None, username_element_locator=None):
        selenium_utils.fill_input_field(self.driver, By.NAME, "username", username)
        selenium_utils.fill_input_field(self.driver, By.NAME, "password", password)

        selenium_utils.click_when_clickable(self.driver, By.ID, "login-submit")
        
        selenium_utils.wait_for_spinner(self.driver, "disappear")

        if expected_url_fragment:
            def url_contains_expected(driver):
                return expected_url_fragment in driver.current_url
        
        WebDriverWait(self.driver, 10).until(url_contains_expected)
        
        if username_element_locator:
            (by, value) = username_element_locator
            selenium_utils.assert_text_in_element(self.driver,by,value,username)

        self.username = username

    def submit_post(self, body_text, username):
        selenium_utils.fill_input_field(self.driver, By.ID, "poster-username", username)
        selenium_utils.fill_input_field(self.driver, By.ID, "post-body", body_text)

        selenium_utils.click_when_clickable(self.driver, By.CSS_SELECTOR, ".btn.btn-primary")

        selenium_utils.wait_for_spinner(self.driver, "disappear")

        selenium_utils.assert_text_in_element(self.driver,By.ID,"posts-view", body_text)

        xpath_query = f"//*[@id='posts-view']//div[contains(@class,'post')]/div[2][contains(text(), '{body_text}')]"

        locator = (By.XPATH, xpath_query)
        return WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(locator)
        )

    def toggle_follow(self, userB_username, action="follow"):
        xpath_query = f"//*[@id='posts-view']//div[contains(@class,'post')]/div[1]//a[contains(text(), '{userB_username}')]"
        
        locator = (By.XPATH, xpath_query)
        selenium_utils.click_when_clickable(self.driver, *locator)

        xpath_query = f"//*[@id='profile-view']//button[contains(text(), '{action.capitalize()}')]"
        locator = (By.XPATH, xpath_query)
        selenium_utils.assert_text_in_element(self.driver,*locator,action.capitalize())
        selenium_utils.click_when_clickable(self.driver, *locator)

        new_label = "Unfollow" if action.lower() == "follow" else "Follow"
        xpath_query = f"//*[@id='profile-view']//button[contains(text(), '{new_label}')]"
        locator = (By.XPATH, xpath_query)
        selenium_utils.assert_text_in_element(self.driver,*locator,new_label)
        
    def assert_post_visible(self, text):
        xpath_query = f"//*[@id='posts-view']//div[contains(@class,'post')]/div[2][contains(text(), '{text}')]"
        locator = (By.XPATH, xpath_query)
        selenium_utils.assert_text_in_element(self.driver, *locator, text)

    def view_profile(self, user_id, username):
        profile_link = selenium_utils.find_by_data_attr(self.driver, "user-id", user_id)

        profile_link.click()
        
        xpath_query = f"//*[@id='profile-view']//strong[contains(text(), '{username}')]"
        locator = (By.XPATH, xpath_query)
        selenium_utils.wait_for_element(self.driver, *locator)
        selenium_utils.assert_text_in_element(self.driver, *locator, username)
    
    def navigate_to_feed(self, feed_type="all-posts"):
        selenium_utils.click_when_clickable(self.driver, By.ID, feed_type)

        if feed_type in ("all-posts", "my-posts"):
            xpath_query = f"//*[@id='posts-view']//div[contains(@class,'post')]"
            expected_text = "👍"         

        elif feed_type == "following":
            xpath_query = f"//*[@id='usernames-view']//h3[contains(text(), 'You are following:')]"
            expected_text = 'You are following:'

        elif feed_type == "followers":
            xpath_query = f"//*[@id='usernames-view']//h3[contains(text(), 'You are followed by:')]"
            expected_text = 'You are followed by:'
        else:
            raise ValueError(f"Unknown feed_type: {feed_type}")
        
        locator = (By.XPATH, xpath_query)
      
        selenium_utils.wait_for_element(self.driver, *locator)
        selenium_utils.assert_text_in_element(self.driver, *locator, expected_text)












