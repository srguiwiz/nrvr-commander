#!/usr/bin/python

from selenium import webdriver

browser = webdriver.Firefox()
browser.implicitly_wait(180)

browser.get("http://www.bbc.co.uk/")

# this is just a website we had picked as an example,
# it may have different links by the time you are trying it out
#
# why this doesn't go all of below links all the time apparently is a Selenium issue,
# possibly specific to versions of Selenium,
# maybe to a browser specific driver
#
# you should figure that out for your own site you are testing, and for your own script
#
# a universally correctly running example will gladly be included here as a replacement

browser.find_element_by_link_text("News").click()
browser.find_element_by_link_text("US & Canada").click()
browser.find_element_by_link_text("Europe").click()
browser.find_element_by_link_text("Weather").click()
browser.find_element_by_link_text("Capital").click()

print "DONE running %s" % (__file__)
