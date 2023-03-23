#!/usr/bin/python3
# --------------------------------------------------------------------------------------------------------------------------------
# copied from https://gist.github.com/hbro/e8a640851bb8b076c37394903f28adf4 and basicly reworked the entire script to:
#       - use geckodriver instead of phantomJS
#       - use pushover instead of email
# --------------------------------------------------------------------------------------------------------------------------------
# Usage:
# - Modify the settings, fill in API credentials of pushover, then run with `python3 ImmowebScraper.py`.
# - First run won't send any push notifications (we assume you checked the current houses in your browser)
# --------------------------------------------------------------------------------------------------------------------------------
# Requirements:
# - python3
# - pushover: pip3 install python-pushover
# - selenium: pip3 install --upgrade pip; pip3 install selenium
# - Geckodriver: brew install geckodriver
# --------------------------------------------------------------------------------------------------------------------------------

import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from pushover import Client

# settings
## Immoweb
### Make sure to remove &page from the link! 
url = 'https://www.immoweb.be/nl/zoeken/huis/te-huur?countries=BE&maxPrice=1500&postalCodes=BE-2430,BE-3200,BE-3510,BE-3511,3270,3271,3290,3293,3294,3460,3510,3512,3540,3545,3560,3583,3980&orderBy=newest'
### Make sure to remove &p and "#gallery" from the link! 
url_zimmo = 'https://www.zimmo.be/nl/zoeken/?search=eyJmaWx0ZXIiOnsic3RhdHVzIjp7ImluIjpbIlRPX1JFTlQiXX0sInBsYWNlSWQiOnsiaW4iOlsxMzQsMTYyLDE4MywxOTcsMjQ3MiwyNDczLDI0NzQsMjQ3OCwyNDgwLDI0ODEsMjQ4MiwyNDgzLDI0ODQsMjQ4NSwyNDg2LDI0ODksMjQ5MCwyNDkxLDI1MTIsODg5LDg5MCw4OTEsODkyLDg5Myw4OTRdfSwiY2F0ZWdvcnkiOnsiaW4iOlsiSE9VU0UiXX0sInByaWNlIjp7InVua25vd24iOnRydWUsInJhbmdlIjp7Im1heCI6MTUwMH19LCJjb25zdHJ1Y3Rpb25UeXBlIjp7ImluIjpbIk9QRU4iXSwidW5rbm93biI6dHJ1ZX19LCJwYWdpbmciOnsiZnJvbSI6MCwic2l6ZSI6MTd9LCJzb3J0aW5nIjpbeyJ0eXBlIjoiREFURSIsIm9yZGVyIjoiREVTQyJ9XX0%3D'
maxpages = 2
## Pushover
userkey="<FILL IN>"   # <--------------------
apitoken="<FILL IN>"  # <--------------------


# preperation
## Database
db = sqlite3.connect('ImmowebScraper.db')
c = db.cursor()
## Browser
options = Options() 
options.headless = True # change to True for debugging
browser = webdriver.Firefox(options=options)
browser.implicitly_wait(5)
## pushover
pushoverClient = Client(userkey, api_token=apitoken)

# ---------- Zimmo   ------------------- #
print("************** Zimmo **************")
# create the immos database table
c.execute('CREATE TABLE IF NOT EXISTS zimmos (id varchar(10) PRIMARY KEY UNIQUE NOT NULL);')
db.commit()

# if there are no id's yet, this is the first run
c.execute('SELECT COUNT(*) FROM zimmos;')
firstRun = c.fetchone()[0] == 0

# scraping
for page in range(1,maxpages+1):
        print('Browsing page {} ...'.format(page))
        print("--------------------------")
        browser.get(url_zimmo + '&p=' + str(page))
        results = browser.find_elements(By.CLASS_NAME, "property-item")
        for result in results:
                ## find the necessairy data
                try:
                        item=result.find_element(By.CLASS_NAME, "property-item_title")
                except:
                        continue # this is probably an ad! :) 
                subitem = result.find_element(By.TAG_NAME, "a")
                zimmoweb_url = subitem.get_attribute('href')
                subitem = result.find_element(By.CLASS_NAME, "property-item_address")
                zimmo_title = subitem.get_attribute('innerHTML').strip().split("<br>")[1]
                subitem = result.find_element(By.CLASS_NAME, "property-item_price ")
                zimmo_price = subitem.get_attribute('innerHTML').strip()
                zimmo_title =  "huis te huur:" + ''.join([i for i in zimmo_title if not i.isdigit()]).rstrip().strip() + " (" + zimmo_price + " per maand)"
                subitem = result.find_element(By.TAG_NAME, "a")
                zimmoweb_id = result.get_attribute('data-code')
                print(zimmoweb_url)
                print(zimmo_title)
                print(zimmoweb_id)
                # pushoverClient.send_message('New house found: {}.'.format(zimmoweb_url), title=zimmo_title)
                print("++++++++++++++++++++++++++++")
                c.execute('SELECT COUNT(*) FROM zimmos WHERE id=:id;', {'id':zimmoweb_id})
                if c.fetchone()[0] == 0:
                        print('New property found: ID {}! Storing in db.'.format(zimmoweb_id))
                        c.execute('INSERT INTO zimmos(id) VALUES (:id);', {'id':zimmoweb_id})
                        db.commit()
                        if not firstRun:
                                print('Sending push notification about new property ID {}.'.format(zimmoweb_id))
                                ## Sent notification
                                pushoverClient.send_message('New house found: {}.'.format(zimmoweb_url), title=zimmo_title)




# ---------- ImmoWeb ------------------- #
print("************** ImmoWeb **************")
# create the immos database table
c.execute('CREATE TABLE IF NOT EXISTS immos (id INTEGER PRIMARY KEY UNIQUE NOT NULL);')
db.commit()

# if there are no id's yet, this is the first run
c.execute('SELECT COUNT(*) FROM immos;')
firstRun = c.fetchone()[0] == 0

# scraping
for page in range(1,maxpages+1):
        print('Browsing page {} ...'.format(page))
        print("--------------------------")
        browser.get(url + '&page=' + str(page))
        results = browser.find_elements(By.CLASS_NAME, "search-results__item")
        for result in results:
                ## find the necessairy data
                try:
                        item=result.find_element(By.CLASS_NAME, "card__title-link")
                except:
                        continue # this is probably an ad! :) 
                immoweb_url = item.get_attribute('href')
                immo_title = item.get_attribute('aria-label')
                item=result.find_element(By.TAG_NAME, "article")
                immoweb_id = item.get_attribute('id').replace('classified_','')
                print(immoweb_url)
                print(immo_title)
                print(immoweb_id)
                # pushoverClient.send_message('New house found: {}.'.format(immoweb_url), title=immo_title)
                print("++++++++++++++++++++++++++++")
                c.execute('SELECT COUNT(*) FROM immos WHERE id=:id;', {'id':immoweb_id})
                if c.fetchone()[0] == 0:
                        print('New property found: ID {}! Storing in db.'.format(immoweb_id))
                        c.execute('INSERT INTO immos(id) VALUES (:id);', {'id':immoweb_id})
                        db.commit()
                        if not firstRun:
                                print('Sending push notification about new property ID {}.'.format(immoweb_id))
                                ## Sent notification
                                pushoverClient.send_message('New house found: {}.'.format(immoweb_url), title=immo_title)

db.close()
browser.quit()
