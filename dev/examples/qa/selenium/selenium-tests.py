#!/usr/bin/python

from selenium import webdriver

browser = webdriver.Firefox()
browser.implicitly_wait(60)

browser.get("http://www.bbc.co.uk/")

browser.find_element_by_link_text("News").click()
browser.find_element_by_link_text("US & Canada").click()
browser.find_element_by_link_text("Europe").click()
browser.find_element_by_link_text("Weather").click()
browser.find_element_by_link_text("Capital").click()
