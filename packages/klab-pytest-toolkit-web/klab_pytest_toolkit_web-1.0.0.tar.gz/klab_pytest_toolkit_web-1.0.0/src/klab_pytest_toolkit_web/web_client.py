import abc
from typing import Optional


class WebClient(abc.ABC):
    """A simple web client is a class which can test websites by making
    - searching element and clicking
    - filling forms
    - navigating pages
    - checks if page contains some text or elements

    This is an abstract base class that defines the interface for web clients.
    Implementations should provide browser automation capabilities for e2e testing.
    """

    @abc.abstractmethod
    def navigate_to(self, url: str) -> None:
        """Navigate to a specified URL.

        Args:
            url: The URL to navigate to
        """
        raise NotImplementedError

    @abc.abstractmethod
    def click(self, selector: str) -> None:
        """Click on an element identified by a selector.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element
        """
        raise NotImplementedError

    @abc.abstractmethod
    def fill(self, selector: str, value: str) -> None:
        """Fill a form field with a value.

        Args:
            selector: CSS selector, XPath, or text selector to identify the input element
            value: The value to fill into the field
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_text(self, selector: str) -> str:
        """Get the text content of an element.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element

        Returns:
            The text content of the element
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value of an element.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element
            attribute: The name of the attribute to retrieve

        Returns:
            The attribute value or None if not found
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_input_value(self, selector: str) -> str:
        """Get the current value of an input element.

        Args:
            selector: CSS selector to identify the input element

        Returns:
            The current value of the input
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_checked(self, selector: str) -> bool:
        """Check if a checkbox or radio button is checked.

        Args:
            selector: CSS selector to identify the checkbox/radio element

        Returns:
            True if checked, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_visible(self, selector: str) -> bool:
        """Check if an element is visible on the page.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element

        Returns:
            True if the element is visible, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_enabled(self, selector: str) -> bool:
        """Check if an element is enabled (not disabled).

        Args:
            selector: CSS selector, XPath, or text selector to identify the element

        Returns:
            True if the element is enabled, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def wait_for_element(self, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to be present in the DOM.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element
            timeout: Maximum time to wait in milliseconds (default: 30000)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def wait_for_element_visible(self, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to be visible on the page.

        Args:
            selector: CSS selector, XPath, or text selector to identify the element
            timeout: Maximum time to wait in milliseconds (default: 30000)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_title(self) -> str:
        """Get the page title.

        Returns:
            The title of the current page
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_url(self) -> str:
        """Get the current page URL.

        Returns:
            The current URL
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_page_source(self) -> str:
        """Get the HTML source of the current page.

        Returns:
            The HTML source as a string
        """
        raise NotImplementedError

    @abc.abstractmethod
    def contains_text(self, text: str) -> bool:
        """Check if the page contains the specified text.

        Args:
            text: The text to search for

        Returns:
            True if the text is found, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_elements_count(self, selector: str) -> int:
        """Get the count of elements matching the selector.

        Args:
            selector: CSS selector, XPath, or text selector to identify the elements

        Returns:
            The number of matching elements
        """
        raise NotImplementedError

    @abc.abstractmethod
    def select_option(self, selector: str, value: str) -> None:
        """Select an option from a dropdown/select element.

        Args:
            selector: CSS selector to identify the select element
            value: The value of the option to select
        """
        raise NotImplementedError

    @abc.abstractmethod
    def check(self, selector: str) -> None:
        """Check a checkbox or radio button.

        Args:
            selector: CSS selector to identify the checkbox/radio element
        """
        raise NotImplementedError

    @abc.abstractmethod
    def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox.

        Args:
            selector: CSS selector to identify the checkbox element
        """
        raise NotImplementedError

    @abc.abstractmethod
    def screenshot(self, path: str) -> None:
        """Take a screenshot of the current page.

        Args:
            path: File path where the screenshot should be saved
        """
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """Close the browser and clean up resources."""
        raise NotImplementedError

    def __enter__(self) -> "WebClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.close()


class PlayWrightWebClient(WebClient):
    """A web client implementation using Playwright."""

    def __init__(self, headless: bool = True):
        """Initialize Playwright web client.

        Args:
            headless: Whether to run the browser in headless mode (default: True)
        """
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()

    def navigate_to(self, url: str) -> None:
        """Navigate to a specified URL."""
        self._page.goto(url)

    def click(self, selector: str) -> None:
        """Click on an element identified by a selector."""
        self._page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        """Fill a form field with a value."""
        self._page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """Get the text content of an element."""
        return self._page.text_content(selector) or ""

    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value of an element."""
        return self._page.get_attribute(selector, attribute)

    def get_input_value(self, selector: str) -> str:
        """Get the current value of an input element."""
        return self._page.input_value(selector)

    def is_checked(self, selector: str) -> bool:
        """Check if a checkbox or radio button is checked."""
        return self._page.is_checked(selector)

    def is_visible(self, selector: str) -> bool:
        """Check if an element is visible on the page."""
        return self._page.is_visible(selector)

    def is_enabled(self, selector: str) -> bool:
        """Check if an element is enabled (not disabled)."""
        return self._page.is_enabled(selector)

    def wait_for_element(self, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to be present in the DOM."""
        self._page.wait_for_selector(selector, timeout=timeout)

    def wait_for_element_visible(self, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to be visible on the page."""
        self._page.wait_for_selector(selector, state="visible", timeout=timeout)

    def get_title(self) -> str:
        """Get the page title."""
        return self._page.title()

    def get_url(self) -> str:
        """Get the current page URL."""
        return self._page.url

    def get_page_source(self) -> str:
        """Get the HTML source of the current page."""
        return self._page.content()

    def contains_text(self, text: str) -> bool:
        """Check if the page contains the specified text."""
        return text in self._page.content()

    def get_elements_count(self, selector: str) -> int:
        """Get the count of elements matching the selector."""
        return len(self._page.query_selector_all(selector))

    def select_option(self, selector: str, value: str) -> None:
        """Select an option from a dropdown/select element."""
        self._page.select_option(selector, value)

    def check(self, selector: str) -> None:
        """Check a checkbox or radio button."""
        self._page.check(selector)

    def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        self._page.uncheck(selector)

    def screenshot(self, path: str) -> None:
        """Take a screenshot of the current page."""
        self._page.screenshot(path=path)

    def close(self) -> None:
        """Close the browser and Playwright."""
        self._browser.close()
        self._playwright.stop()


class WebClientFactory:
    """Factory to create web client instances."""

    class WebClientType:
        PLAYWRIGHT = "playwright"

    @staticmethod
    def create_client(client_type: str = "playwright", headless: bool = True) -> WebClient:
        """Create a web client based on the specified type.

        Args:
            client_type: Type of web client to create (e.g., "playwright")
            headless: Whether to run the browser in headless mode (default: True)

        Returns:
            An instance of WebClient
        """
        if client_type == WebClientFactory.WebClientType.PLAYWRIGHT:
            return PlayWrightWebClient(headless=headless)
        else:
            raise ValueError(f"Unsupported client type: {client_type}")
