import cv2
import json
import base64
import numpy as np
import pandas as pd
from math import sqrt
from selenium import webdriver
from selenium.webdriver.common.by import By
from statsmodels.tsa.arima.model import ARIMA

# tunable parameters

tts = 0.2 # train-test split (lower the better in this case)
alpha = 0.05 # confidence interval
p = 3 # AR parameter
d = 2 # differencing parameter
q = 1 # MA parameter
forecasttill = 10 # number of points to forecast
threshold = 10 # number of frames to wait before placing a trade


# prediction pipeline 
'''
input : list of points in tuple format (x, y) where x is the time and y is the price
        an integer indicating the x coordinate of the finish line
output : string stating "up", "down" or "none" to skip the prediction
'''
def predict(prices):

    try:

        global tts, alpha, p, d, q, forecasttill

        df = pd.DataFrame(prices, columns=['time', 'price'])
        df.drop_duplicates(subset='time', keep='first', inplace=True)

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
        
    except:
            
        return "none"


# driver profile settings and options
ffprofile = webdriver.FirefoxProfile()
ffprofile.set_preference("dom.webnotifications.enabled", False)

# web driver initialization
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

# waiting for the user to complete the captcha
input("Complete the Captcha and press Enter to continue...")

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

frame = 0
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
        prices.append(top)

    # finding the bottoms of the red candles
    redMask = cv2.inRange(img, np.array([170 , 121 , 255]), np.array([179 , 170 , 255]))

    contours, _ = cv2.findContours(redMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for j, contour in enumerate(contours):
        bbox = cv2.boundingRect(contour)
        bottom = (bbox[0] + (bbox[2] // 2), bbox[1] + bbox[3])
        prices.append(bottom)

    decision = predict(prices)

    if decision == "up" and frame > threshold:
        button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[4]
        button.click()
        frame = 0
    elif decision == "down" and frame > threshold:
        button = driver.find_elements(By.CLASS_NAME, "button_btn__dCMn2")[5]
        button.click()
        frame = 0
    else:
        pass
    
    frame += 1

    # exit condition
    if cv2.waitKey(1) & 0xFF == ord('q'):

        cv2.destroyAllWindows()
        driver.close()
        break   
    

