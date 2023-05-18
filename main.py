import cv2
import json
import time
import base64
import numpy as np
import pandas as pd
from math import sqrt
from selenium import webdriver
from selenium.webdriver.common.by import By
from statsmodels.tsa.arima.model import ARIMA

# prediction pipeline 
'''
input : list of points in tuple format (x, y) where x is the time and y is the price
        an integer indicating the x coordinate of the finish line
output : string stating "up" or "down" 
'''
def predict(prices, x1):

    df = pd.DataFrame(prices, columns=['time', 'price'])
    df.drop_duplicates(subset='time', keep='first', inplace=True)

    forecasttill = x1 - df['time'].max() # number of points to forecast

    # tunable hyperparameters
    tts = 0.2 # train-test split
    alpha = 0.05 # confidence interval
    p = 3 # AR parameter
    d = 2 # differencing parameter
    q = 1 # MA parameter

    series = df['price']

    # split into train and test sets
    X = series.values
    size = int(len(X) * tts)
    train, test = X[0:size], X[size:len(X)]
    history = [x for x in train]
    predictions = list()

    # walk-forward validation
    for t in range(len(test)):

        model = ARIMA(history, order=(p,d,q))
        model_fit = model.fit()

        output = model_fit.forecast()
        yhat = output[0]
        predictions.append(yhat)

        obs = test[t]
        history.append(obs)

    # Forecast
    forecast = model_fit.forecast(forecasttill, alpha=alpha)  
    forecast = forecast.tolist()

    cur = int(test[len(test)-1])
    pred = int(forecast[len(forecast)-1])

    if pred > cur:
        return "up"
    elif pred < cur:
        return "down"
    else:
        return "none"


# driver profile settings
ffprofile = webdriver.FirefoxProfile()
ffprofile.set_preference("dom.webnotifications.enabled", False)

driver = webdriver.Firefox(ffprofile)
driver.get("https://binomo.com/trading")
driver.maximize_window()

# logging in
with open('credentials.json') as json_file:
    data = json.load(json_file)

email = driver.find_elements(By.TAG_NAME, "input")[0]
password = driver.find_elements(By.TAG_NAME, "input")[1]

email.send_keys(data['email'])
password.send_keys(data['password'])


# clicking the login button
button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[2]
button.click()

#time.sleep(10)
input("Press Enter to continue...")

# capturing the location of the canvas
canvas = driver.find_elements(By.TAG_NAME, "canvas")[0]
location = canvas.location
size = canvas.size
x = location['x']
y = location['y']
w = size['width']
h = size['height']
width = x + w
height = y + h

curTime = time.time()
while True:

    # initializing array of points
    prices = []

    # capturing the window and cropping chart
    canvas_base64 = driver.get_screenshot_as_base64()
    nparr = np.fromstring(base64.b64decode(canvas_base64), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = img[int(y):int(height), int(x)+350:int(width)-200]

    # converting to HSV
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    points = np.zeros_like(img)

    # finding the tops of the green candles
    greenMask = cv2.inRange(img, np.array([60 , 190 , 180]), np.array([90 , 255 , 255]))

    contours, _ = cv2.findContours(greenMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for j, contour in enumerate(contours):
        bbox = cv2.boundingRect(contour)
        top = (bbox[0] + (bbox[2] // 2), bbox[1])
        cv2.circle(points, top, 5, (255, 255, 255), -1)
        prices.append(top)

    # finding the bottoms of the red candles
    redMask = cv2.inRange(img, np.array([170 , 121 , 255]), np.array([179 , 170 , 255]))

    contours, _ = cv2.findContours(redMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for j, contour in enumerate(contours):
        bbox = cv2.boundingRect(contour)
        bottom = (bbox[0] + (bbox[2] // 2), bbox[1] + bbox[3])
        cv2.circle(points, bottom, 5, (255, 255, 255), -1)
        prices.append(bottom)

    # locating the finish line
    finishMask = cv2.inRange(img, np.array([172 , 32 , 130]), np.array([179 , 153 , 225]))

    # finding finish flag contour
    contours, _ = cv2.findContours(finishMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for j, contour in enumerate(contours):
        bbox = cv2.boundingRect(contour)
        x1 = bbox[0] + (bbox[2] // 2)
    cv2.line(points, (x1, 0), (x1, 876), (255, 255, 255), 2)

    decision = predict(prices, x1)

    if decision == "up":
        button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[4]
        button.click()
    elif decision == "down":
        button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[5]
        button.click()
    else:
        pass

    fps = 1 / (time.time() - curTime)
    curTime = time.time()
    cv2.putText(points, '{0:.2f}'.format(fps), (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(points, '{0:.2f}'.format((1 / fps) * 1000), (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 0), 1, cv2.LINE_AA)

    cv2.imshow('Window', points)
    # exit condition
    if cv2.waitKey(1) & 0xFF == ord('q'):

        cv2.destroyAllWindows()
        driver.close()
        break   
    

