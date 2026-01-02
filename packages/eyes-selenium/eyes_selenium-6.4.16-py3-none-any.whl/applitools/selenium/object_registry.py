from __future__ import absolute_import, division, print_function

from typing import TYPE_CHECKING

from applitools.common.object_registry import ObjectRegistry

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement


class SeleniumWebdriverObjectRegistry(ObjectRegistry):
    def marshal_driver(self, driver):
        # type: (WebDriver) -> dict
        command_executor = driver.command_executor
        server_url = getattr(command_executor, "_url", None)
        if server_url is None:
            # seems latest appium client
            client_config = getattr(command_executor, "_client_config", None)
            if client_config is None:
                raise Exception("No client configuration available")
            server_url = client_config.remote_server_addr

        return {
            "sessionId": driver.session_id,
            "serverUrl": server_url,
            "capabilities": driver.capabilities,
        }

    def marshal_element(self, element):
        # type: (WebElement) -> dict
        return {"elementId": element._id}
