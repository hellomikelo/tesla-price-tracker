from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import json
import selenium
import time

def get_data():
    # Initialize Chrome Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537'
    options.add_argument('user-agent={0}'.format(user_agent))

    driver = webdriver.Chrome(options=options) 
    driver.implicitly_wait(90)

    # Load the URL and get the page source
    URL = 'https://www.tesla.com/inventory/new/my?TRIM=LRAWD&WHEELS=NINETEEN&CABIN_CONFIG=FIVE&arrangeby=plh&zip=94043&range=0'
    driver.get(URL)

    results_container = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CLASS_NAME, "results-container"))
    )
    
    time.sleep(1) 

    sections = results_container.find_elements(By.CSS_SELECTOR, "#iso-container > div > div.inventory-app-wrapper.tds-scrim--white > main > div > article")
    
    assert len(sections) != 0, "No sections found! Please check."

    # Parse section for car info
    car_info = []
    for section in sections:
        # Get raw HTML
        purchase_price_str = section.find_element(By.CLASS_NAME, "result-purchase-price").get_attribute("innerHTML")
        try: 
            base_price_str = section.find_element(By.CLASS_NAME, "result-price-base-price").get_attribute("innerHTML")
        except Exception as e:
            # If there's no discount
            base_price_str = purchase_price_str
        after_credit_price_str = section.find_element(By.CSS_SELECTOR, '#iso-container > div > div.inventory-app-wrapper.tds-scrim--white > main > div > article > section.result-federal-incentive > div > span').get_attribute("innerHTML")
        try: 
            odometer_str = section.find_element(By.CSS_SELECTOR, "#iso-container > div > div.inventory-app-wrapper.tds-scrim--white > main > div > article > section.result-header > div.result-basic-info > div.tds-text--caption").get_attribute("innerHTML")
        except Exception as e:
            # If there's no miles driven
            odometer_str = '0'
        base_features_str = section.find_element(By.CSS_SELECTOR, '#iso-container > div > div.inventory-app-wrapper.tds-scrim--white > main > div > article > section.result-features.features-grid > ul.result-regular-features.tds-list.tds-list--unordered').get_attribute("innerHTML")
        car_type = section.find_element(By.CLASS_NAME, "tds-text_color--10").get_attribute("innerHTML")

        # Parse raw HTML
        purchase_price = int(purchase_price_str.replace('$', '').replace(',', ''))
        base_price = int(base_price_str.replace('$', '').replace(',', ''))
        after_credit_price = int(re.findall(r'\b\d+\b', after_credit_price_str.replace('$', '').replace(',', ''))[0])
        base_features = re.findall(r'<li.*?>(.*?)<\/li>', base_features_str)
        odometer = int(re.findall(r'\b\d+\b', odometer_str.replace('$', '').replace(',', ''))[0])
        url = 'https://www.tesla.com/my/order/7SAY' + section.get_attribute('data-id').replace('-search-result-container', '')

        assert car_type == 'Model Y Long Range Dual Motor All-Wheel Drive', "Car is not a Model Y!"

        car_info.append({
            'purchase_price': purchase_price,
            'after_tax_credit_price': after_credit_price,
            'odometer': odometer,
            'base_price': base_price,
            'price_adjustment': base_price - purchase_price,
            'pct_discount': round((base_price - purchase_price) / base_price * 100, 2),
            'base_features': base_features,
            'url': url
        })

    # Sort records based on purchase price and odometer 
    car_info = sorted(car_info, key=lambda x: (x['purchase_price'], x['odometer']))
    min_price = min(car_info, key=lambda x: x['purchase_price'])['purchase_price']
    [print(x) for x in car_info if x['purchase_price'] == min_price]

    # Write out results
    with open("latest_prices.json", "w") as f:
        # Dump the list to the file
        json.dump(car_info, f)

if __name__ == '__main__':
    get_data()
