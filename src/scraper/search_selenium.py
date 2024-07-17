# SELENIUM IMPORTS
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

# OTHER IMPORTS
import os
import pickle
import chromedriver_autoinstaller_fix

# MY IMPORTS
from . import search_loader
from data.pickle_helper import check_if_exists, clear_file
from .base import Offer

# VARIABLES FROM CONFIG
from config import SEARCH_INFO_LOCATION
# Internal imports
from time_utils import time_helper

# CONSTANTS TO BE USED LATER
IGNORED_EXCEPTIONS = (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

XPATH = (
    '//div[not(preceding::div[contains(descendant::text(), "Znaleźliśmy  0 ogłoszeń")])]'
    '/div[@data-testid="listing-grid"][1]'
    '/child::div[@data-cy="l-card"and not(contains(descendant::div, "Wyróżnione"))]'
)

LINK_LIST = search_loader.search_loader(SEARCH_INFO_LOCATION)

chromedriver_autoinstaller_fix.install()

def initialize_webdriver():
    # CREATES WEBDRIVER INSTANCE, WITH OPTIONS ADDED
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--incognito")
    # chrome_options.page_load_strategy = "eager"

    return webdriver.Chrome(options=chrome_options)

def search_selenium(link_list_inner=LINK_LIST) -> list[Offer]:
    offers = []     # "raw" offers
    olx_offers = []

    driver = initialize_webdriver()

    # GOES FOR EVERY LINK IN LIST OF LINKS
    for count, link in enumerate(link_list_inner):
        # DRIVER GOES TO LINK
        driver.get(link)

        # PROGRESS COUNT PRINT
        offer_progress = f"({count+1}/{len(link_list_inner)})"
        offer_notify_count = 1
        print(f"\n{time_helper.human_readable_time()}: {offer_progress} || {link}")

        try:
            # SEARCH ELEMENTS IN DOM WITH XPATH SPECIFIED EARLIER
            elements = WebDriverWait(
                driver, timeout=2, ignored_exceptions=IGNORED_EXCEPTIONS
            ).until(
                expected_conditions.visibility_of_all_elements_located(
                    (By.XPATH, XPATH)
                )
            )

            # ADDS LIST OF ELEMENTS TO OFFERS LIST
            offers.append(elements)

            # ITERATES THROUGH EVERY OFFER IN SEARCH
            for count2, offer in enumerate(offers[count]):
                split_offer = offer.text.split("\n")

                # HANDLES IF OFFER IS OPEN TO NEGOTIATIONS
                if split_offer[2] != "do negocjacji":
                    split_offer.insert(2, "nie do negocjacji")

                # INSERTS ID INTO OFFER
                split_offer.insert(0, offer.get_attribute("id"))

                ''' OLX modified their display UI, doesnt work (for now)
                # SEPARATES LOCATION FROM TIME
                try:
                    split_offer_buffer = split_offer[5].split(" - ")
                except IndexError:
                    pass
                split_offer.append(split_offer_buffer[1])
                split_offer[5] = split_offer_buffer[0]
                '''

                # APPENDS LINK TO SPLIT_OFFER
                split_offer.append(
                    offer.find_element(By.TAG_NAME, "a").get_attribute("href")
                )

                for _ in range(0, 10):
                    try:
                        if split_offer[_] is not None:
                            pass
                    except IndexError:
                        split_offer.append("error")

                offer = Offer(
                    split_offer[0],
                    split_offer[1],
                    split_offer[2],
                    split_offer[3],
                    split_offer[4],
                    split_offer[5],
                    split_offer[6],
                    split_offer[7]
                )

                olx_offers.append(offer)

                offer_notify_count += 1

        except TimeoutException:
            offer_notify_count = 0
            print(f"\tNo offers in search")
            # APPENDS EMPTY LIST TO OFFERS, SO LOOP CAN PROCEED NORMALLY
            offers.append([])

        if offer_notify_count == 1:
            print(f"\tNo new offers were seen")

    driver.quit()

    return olx_offers