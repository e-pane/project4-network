# Core utilities to support Selenium testing of front end vanilla js(test_frontend.py) in network app
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def find_by_id(driver, id_str):
    """
    Locate and return a DOM element by ID using Selenium WebDriver.
    Args:
        driver (WebDriver): The Selenium browser instance.
        id_str (str): The ID of the target element.
    Returns:
        WebElement: The located DOM element.
    Raises:
        AssertionError: If the element is not found.
        """
   
    try:
        return driver.find_element(By.ID, id_str)
    except NoSuchElementException:
        raise AssertionError(f"Element with ID '{id_str}' not found")
    
def find_by_name(driver, name_str):
    """
    Locate and return a DOM element by name using Selenium WebDriver.
    Args:
        driver (WebDriver): The Selenium browser instance.
        id_str (str): The ID of the target element.
    Returns:
        WebElement: The located DOM element.
    Raises:
        AssertionError: If the element is not found.
        """
   
    try:
        return driver.find_element(By.NAME, name_str)
    except NoSuchElementException:
        raise AssertionError(f"Element with NAME '{name_str}' not found")
        
def wait_for_element(driver, by, value, timeout=10):
    """
    Waits for a web element to be present and visible in the DOM before rendering.  Pauses test execution 
    Args:
        driver (WebDriver): The Selenium browser instance.
        by (selenium.webdriver.common.by.By): locating strategy to find the element
        value (str): The selector string bound to the target element.
        timeout (int): max # of seconds to wait for the element to be visible - defaults to 10
    Returns:
        WebElement: The located DOM element with confirmation of its visibility within timeout period
    Raises:
        TimeoutException: If the element is not found or not visible within timeout period
        """
    try:
        return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )
    except TimeoutException:
        raise AssertionError(f"Element with ({by}, '{value}') not found within {timeout} seconds.")
    
def click_when_clickable(driver, by, value, timeout=10):
    """
    Waits for a web element to be present and visible and enabled in the DOM before rendering. Confirms
    visibility, then clicks on the element
    Args:
        driver (WebDriver): The Selenium browser instance.
        by (selenium.webdriver.common.by.By): locating strategy to find the element
        value (str): The selector string bound to the target element.
        timeout (int): max # of seconds to wait for the element to be visible - defaults to 10
    Returns:
        None, just executes side effect of clicking on the visible element
    Raises:
        TimeoutException: If the element is not found or not visible or enabled within timeout period
        AssertionError: 
        """
    try:
        enabled_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))      
        )
        enabled_element.click()
        
    except TimeoutException:
        raise AssertionError(f"Element with ({by}, '{value}') not found within {timeout} seconds.")
    
def assert_text_in_element(driver,by,value,expected_text,timeout=10):
    """
    Waits for a web element to be present and visible, then checks that the element .text is properly rendered
    Args:
        driver (WebDriver): The Selenium browser instance.
        by (selenium.webdriver.common.by.By): locating strategy to find the element
        value (str): The selector string bound to the target element.
        expected_text (str): the innerHTML or text of the element, as properly rendered
        timeout (int): max # of seconds to wait for the element to be visible - defaults to 10
    Returns:
        None, wraps an assertion 
    Raises:
        TimeoutException: If the element is not found or not visible or enabled within timeout period
        AssertionError: 
        """
    try:
        rendered_element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        assert expected_text in rendered_element.text 

    except TimeoutException:
        raise AssertionError(f"Element with ({by}, '{value}') did not render {expected_text}")

def wait_for_spinner(driver, action="appear", timeout=10):
    """
    Waits for the AJAX spinner element to either appear or disappear in the DOM
    Args: 
        driver (WebDriver): The Selenium browser instance.
        action (str): used conditionally to drive action
        timeout (int): max # of seconds to wait for the element to be visible - defaults to 10
    Returns:
        WebElement, or none, depending on the action
    Raises:
        TimeoutException: If the element is not found or not visible or enabled within timeout period
        AssertionError:
        """
    try:
        if action == "appear":
            return WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "spinner"))
            )
        else:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.ID, "spinner"))
            )
            return None
    except TimeoutException:
        raise AssertionError(f"Spinner element could not be managed correctly")

def find_by_data_attr(driver, attr, value, timeout=10):
    """
    Locates webelement in the DOM by custom data attributes
    Args: 
        driver (WebDriver): The Selenium browser instance.
        attr (str): name of the data attribute
        value (str): value of the attribute
        timeout (int): max # of seconds to wait for the element to be visible - defaults to 10
    Returns:
        first matching web element
    Raises:
        AssertionError if element not found by data attribute
        """    
    try:
        xpath_query = f"//*[@data-{attr}='{value}']"
        locator = (By.XPATH, xpath_query)
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        raise AssertionError(f"Element with data attribute {value} not found within {timeout} seconds.")
    
def fill_input_field(driver, by, value, text, timeout=10):
    """
    Waits for an input field to be visible, clears it, then sends text.
    Args:
        driver (WebDriver): The Selenium browser instance.
        by (By): Locator strategy.
        value (str): The selector string.
        text (str): Text to input into the field.
        timeout (int): How long to wait for the element to be visible.
    Returns:
        None
    Raises:
        AssertionError: If the field is not found or not interactable.  
    """
    try:
        field = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        field.clear()
        field.send_keys(text)

    except TimeoutException:
        raise AssertionError(f"Element with ({by}, '{value}') not found within {timeout} seconds.")
    
def assert_element_not_present(driver, by, value, timeout=5):
    """
    Asserts that an element does not exist or disappears within timeout.
    Args:
        driver (WebDriver)
        by (By)
        value (str)
        timeout (int)
    Returns:
        None
    Raises:
        AssertionError: If the element is still present.
    """
    try:
        WebDriverWait(driver, timeout).until_not(
        EC.presence_of_element_located((by, value))
    )
    
    except TimeoutException:
        raise AssertionError(f"Element with ({by}, '{value}') still present after {timeout} seconds.")
    
def get_elements_by_class(driver, class_name):
    """
    Returns a list of elements matching a class name.
    Args:
        driver (WebDriver)
        class_name (str)
    Returns:
        list of WebElements
    """
    return driver.find_elements(By.CLASS_NAME, class_name)

def build_query_params(params):
    """
    Build a URL-encoded query string from a dictionary of parameters.

    Args:
        params: A dictionary where keys and values represent query parameter names and values.

    Returns:
        A URL-encoded query string suitable for appending to a URL.
    """
    query_string_pairs = []
    for key in params:
        query_string_pair = f"{key}={params[key]}"
        query_string_pairs.append(query_string_pair)

    query_string = "?" + "&".join(query_string_pairs) 
    return query_string   

    