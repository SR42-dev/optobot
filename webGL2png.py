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

# capturing the chart
driver.get("https://binomo.com/trading")

canvas = driver.find_elements(By.CLASS_NAME, "chart")
print(canvas)

# get the canvas as a PNG base64 string
#canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)

# decode
#canvas_png = base64.b64decode(canvas_base64)
