import json
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
driver.get("https://binomo.com/trading")

# logging in
with open('credentials.json') as json_file:
    data = json.load(json_file)

email = driver.find_elements(By.TAG_NAME, "input")[0]
password = driver.find_elements(By.TAG_NAME, "input")[1]

email.send_keys(data['email'])
password.send_keys(data['password'])

button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[2]
button.click()
