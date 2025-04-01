import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests


PATH = "/Users/chaicharn/Documents/chromedriver-mac-arm64/chromedriver"
areas = ['หมอชิต']

service = Service(executable_path=PATH)
driver = webdriver.Chrome(service=service)
driver.maximize_window()
# driver.implicitly_wait(5)
driver.get("https://www.livinginsider.com/searchword/all/all/1/%E0%B8%A3%E0%B8%A7%E0%B8%A1%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%81%E0%B8%B2%E0%B8%A8-%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD-%E0%B8%82%E0%B8%B2%E0%B8%A2-%E0%B9%80%E0%B8%8A%E0%B9%88%E0%B8%B2-%E0%B9%80%E0%B8%8B%E0%B9%89%E0%B8%87-%E0%B8%84%E0%B8%AD%E0%B8%99%E0%B9%82%E0%B8%94-%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99-%E0%B8%97%E0%B8%B5%E0%B9%88%E0%B8%94%E0%B8%B4%E0%B8%99.html")

for area in areas:
    for _ in range(2):
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="frm-search-top"]/div/div[2]/div/input')
                )
            )
            search_bar = driver.find_element(By.XPATH, '//*[@id="frm-search-top"]/div/div[2]/div/input')
            search_bar.clear()
            search_bar.send_keys(area + Keys.ENTER)
        except:
            print("No element try again")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/header/nav/div[2]/div/div/form/div/div[3]/div/button/span[1]')
        )
    )
    property_type = driver.find_element(By.XPATH, '/html/body/header/nav/div[2]/div/div/form/div/div[3]/div/button/span[1]')
    property_type.click()
    type_element = driver.find_element(By.XPATH, '//*[@id="building"]/li[2]')

    # i = 0
    # while True:

    #     page_content = requests.get(page_url)
    #     soup = BeautifulSoup(page_content.content, 'html.parser')
    #     posts = soup.find_all('div', class_="col-md-3 col-sm-4 col-xs-6")

    #     for post in posts:

    #         link = post.find('a', class_="image-ratio-4-3").get('href')
    #         in_post_content = requests.get(link)
    #         in_post_soup = BeautifulSoup(in_post_content.content, 'html.parser')
    #         detail_content = in_post_soup.find('div', class_="detail-content col-sm-12 main-detail-content")
    #         owner = detail_content.find('label').text
    #         if owner in agent_name_list:
    #             print(f"Owner : {owner} continue")
    #             continue
    #         condo_name = detail_content.find('span', class_="text_project_detail_green").text
    #         price = detail_content.find('span', class_="t-24 price-detail mt-0").text.replace('\n', '')

    #         detail_property = detail_content.find('div', class_="row detail-row")
    #         room_details = detail_property.find_all('span', class_="detail-property-list-text")
    #         properties = []
    #         for detail in room_details:
    #             room_detail = detail.text
    #             room_detail = re.sub(r'[\s\n]', '', room_detail)
    #             properties.append(room_detail)

    #         room_dict['condo_name'].append(condo_name)
    #         room_dict['price'].append(price)
    #         room_dict['owner'].append(owner)
    #         room_dict['url'].append(link)
    #         room_dict['area'].append(properties[0])
    #         room_dict['floor'].append(properties[1])
    #         room_dict['bedroom'].append(properties[2])
    #         room_dict['bathroom'].append(properties[3])

    #     ul = soup.find('ul', class_="pagination")
    #     pages = ul.find_all('a', class_="loading_page")
    #     next_page = pages[-2]
    #     if next_page.text != " Next ›":
    #         break
    #     else:
    #         page_url = next_page.get('href')
    #         i += 1
    #         print(i)

time.sleep(5)
driver.quit()