from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import pyautogui
from time import sleep

from opensea_bot import settings
from opensea_bot import tools


class OpenSeaBot:
    def __init__(self) -> None:
        options = Options()
        options.add_argument("--log-level=3")

        if settings.METAMASK_EXTENSION_PATH:
            options.add_extension(settings.METAMASK_EXTENSION_PATH)

        self.driver = webdriver.Chrome(
            executable_path=settings.CHROMEDRIVER_PATH, options=options
        )
        self.wait = WebDriverWait(self.driver, 10)

    def connect_to_metamask(self, secret_phrase: str) -> None:
        # Connect to metamask:
        self.driver.get(
            r"chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#initialize/select-action"
        )
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='app-content']/div/div[2]/div/div/div[2]/div/div[2]/div[1]/button",
                )
            )
        ).click()
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='app-content']/div/div[2]/div/div/div/div[5]/div[1]/footer/button[1]",
                )
            )
        ).click()

        # Submit metamask secret phrase and password:
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='app-content']/div/div[2]/div/div/form/div[4]/div[1]/div/input",
                )
            )
        ).send_keys(secret_phrase)
        self.driver.find_element(By.XPATH, "//*[@id='password']").send_keys("12345678")
        self.driver.find_element(By.XPATH, "//*[@id='confirm-password']").send_keys(
            "12345678"
        )
        self.driver.find_element(
            By.XPATH, "//*[@id='app-content']/div/div[2]/div/div/form/div[7]/div"
        ).click()

        self.driver.find_element(
            By.XPATH, "//*[@id='app-content']/div/div[2]/div/div/form/button"
        ).click()
        sleep(settings.SLEEP_TIME)

        # Login to OpenSea
        self.driver.get(r"https://opensea.io/login?referrer=%2Faccount")

    def get_nfts(self, type: str = "all") -> list[str]:
        """
        type(str):  "all", "collected" or "hidden"
        """
        nfts = []
        collected_nfts = 0

        # Get collected NFTs
        if type == "all" or type == "collected":
            print("[STATUS] Looking for collected NFTs")
            self.driver.get("https://opensea.io/account")
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "Image--image"))
            )
            nfts += self._scroll_down_and_grab_nfts()
            collected_nfts = len(nfts)
            print(f"[STATUS] {collected_nfts} collected NFTs found")

        # Get hidden NFTs
        if type == "all" or type == "hidden":
            print("[STATUS] Looking for hidden NFTs")
            self.driver.get("https://opensea.io/account?tab=private")
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "Image--image"))
            )
            nfts += self._scroll_down_and_grab_nfts()
            print(f"[STATUS] {len(nfts) - collected_nfts} hidden NFTs found")

        return nfts

    def transfer_nfts(self, wallet: str, nfts: list[str]) -> None:
        print(f"[STATUS] Starting transference of {len(nfts)} nfts to {wallet}")
        for nft in nfts:
            try:
                self.driver.get(nft)
                sleep(settings.SLEEP_TIME)

                # Click transfer button:
                self.driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Transfer']"
                ).click()

                # Fill transference information
                sleep(settings.SLEEP_TIME)
                copies_owned = self._find_copies_owned()
                if copies_owned > 1:
                    quantity = self.driver.find_element(
                        By.CSS_SELECTOR, "input[id='quantity']"
                    )
                    quantity.send_keys(Keys.CONTROL + "a")
                    quantity.send_keys(Keys.DELETE)
                    quantity.send_keys(copies_owned)

                self.driver.find_element(
                    By.CSS_SELECTOR, "input[id='destination']"
                ).send_keys(wallet)

                submit = self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )
                submit.click()
                sleep(settings.SLEEP_TIME // 2)

                # Click last 'Transfer' button:
                pyautogui.click(*settings.TRANSFER_BUTTON_POS)

                # Confirm transaction:
                sleep(settings.SLEEP_TIME)
                pyautogui.click(*settings.METAMASK_CONTRACT_SCROLL_DOWN_ARROW_POS)
                pyautogui.click(*settings.METAMASK_SCROLL_DOWN_ARROW_POS)
                pyautogui.click(*settings.METAMASK_SCROLL_DOWN_ARROW_POS)
                pyautogui.click(*settings.METAMASK_SIGN_BUTTON_POS)
                sleep(settings.SLEEP_TIME)
                print(f"[STATUS] Successfully transfer {copies_owned} copies of {nft}")

            except Exception:
                print(f"[STATUS] Could not transfer {nft}")

    def _scroll_down_and_grab_nfts(self) -> list[str]:
        nfts = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            scroll_rate = last_height // 10

            for y in range(scroll_rate, last_height, scroll_rate):
                nfts += self._get_nft_links()
                self.driver.execute_script(f"window.scrollTo(0, {y})")
                sleep(settings.SCROLL_PAUSE_TIME)

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height <= last_height:
                return tools.delete_duplicates(nfts)

            last_height = new_height

    def _get_nft_links(self) -> list[str]:
        """
        Returns a list containing nfts link in the current website
        """
        elements = self.driver.find_elements(By.XPATH, "//a[@href]")
        try:
            links = [element.get_attribute("href").strip() for element in elements]
        except StaleElementReferenceException:
            return []
        nft_links = [link for link in links if "assets/" in link]
        return nft_links

    def _find_copies_owned(self) -> int:
        elements = self.driver.find_elements(By.TAG_NAME, "span")
        for element in elements:
            if "owned" in element.text:
                return tools.find_int_in_string(element.text)
