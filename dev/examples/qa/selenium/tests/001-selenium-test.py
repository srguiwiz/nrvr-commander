#!/usr/bin/python

from selenium import webdriver

import sys
import time

print "STARTING running %s" % (__file__)
sys.stdout.flush()

hasReachedEnd = False
try:
    browser = webdriver.Firefox()
    browser.implicitly_wait(45)
    
    try:
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
        
        time.sleep(3)
        browser.find_element_by_link_text("News").click()
        time.sleep(3)
        browser.find_element_by_link_text("US & Canada").click()
        time.sleep(3)
        browser.find_element_by_link_text("Europe").click()
        time.sleep(3)
        browser.find_element_by_link_text("Weather").click()
        time.sleep(3)
        browser.find_element_by_link_text("Capital").click()
        
        hasReachedEnd = True
    finally:
        time.sleep(3)
        browser.quit()

except Exception as ex:
    sys.stderr.flush()
    print "EXCEPTION running %s:" % (__file__)
    print ex
    sys.stdout.flush()
    hasReachedEnd = True

finally:
    sys.stderr.flush()
    if not hasReachedEnd:
        print "ABNORMAL unspecified end to running %s" % (__file__)
    print "DONE running %s" % (__file__)
    sys.stdout.flush()
