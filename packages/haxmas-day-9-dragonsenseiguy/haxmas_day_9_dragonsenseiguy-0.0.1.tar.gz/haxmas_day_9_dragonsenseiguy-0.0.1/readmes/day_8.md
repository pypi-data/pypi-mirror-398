# Automating Cookie Clicker!

Prize: $5 Cookie Grant and 3 snowflakes :)

Hello! I am Aditya, and i'll teach you how to use Python and [Selenium](https://www.selenium.dev/). Selenium is a browser automation tool used by engineers to test their applications, today we will be using it for a completely different purpose, automating cookie clicker.

Perquisites:
- An Editor(I recommend PyCharm for this)
- Python(I recommend 3.13)

## Setup
Make a new folder for the project and make a virtual environment using
```
python3 -m venv .venv
```

to activate the virtual environment on
macOS/penguinOS(Linux) run:
```
source .venv/bin/activate
```
on windows run:
```
.venv\Scripts\activate.bat
```

now you need to install the `selenium` package, which lets us use selenium with
```
pip install selenium
```

now make a `main.py` file, this file will contain the main code for the project

## Writing the Code

Open up `main.py` and let's start by importing the necessary libraries:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
```

Now, let's initialize the browser and open Cookie Clicker:

```python
# Create a Chrome webdriver instance
driver = webdriver.Chrome()

# Open Cookie Clicker
driver.get("https://ozh.github.io/cookieclicker/")

# Wait for the page to load
time.sleep(10) # This is also time so you can click your language and it doesn't crash
```

The fun part: actually clicking cookies. Here's how to find and click the big cookie:

```python
# Find the big cookie element
cookie = driver.find_element(By.ID, "bigCookie")

# Click it a bunch of times (adjust the number based on your patience)
for i in range(100):
    cookie.click()
    time.sleep(0.1)  # Don't be TOO cruel to your CPU
```

Want to make it smarter? Let's add automatic building purchases:

```python
def buy_buildings(driver, how_many_times=5):
    """Automatically buy buildings because manual clicking buildings is for people
    who haven't discovered loops yet."""
    
    for _ in range(how_many_times):
        # Find all building purchase buttons
        buildings = driver.find_elements(By.CLASS_NAME, "product")
        
        # Click each building we can afford (from bottom to top, because we're fancy)
        for building in reversed(buildings):
            try:
                building.click()
            except:
                # If we can't afford it, just move on with our lives
                pass
        
        time.sleep(1)

# Call it
buy_buildings(driver, how_many_times=10)
```

Here's a complete script that clicks cookies and buys buildings forever (or until you get tired and stop it):

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.get("https://ozh.github.io/cookieclicker/")
time.sleep(10)

cookie = driver.find_element(By.ID, "bigCookie")

try:
    cycle = 0
    while True:  # Keep going forever
        cycle += 1
        
        # Click the cookie 50 times per cycle
        for _ in range(50):
            cookie.click()
            time.sleep(0.05)
        
        # Try to buy buildings
        buildings = driver.find_elements(By.CLASS_NAME, "product")
        for building in reversed(buildings):
            try:
                building.click()
            except:
                pass
        
        print(f"Cycle {cycle} complete. Your cookies are accumulating rapidly.")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nBot stopped. Check your cookie count - it's probably ridiculous now.")
finally:
    driver.quit()
```

The key change: we replaced `for cycle in range(50):` with `while True:` so the bot keeps clicking forever.

## What You've Learned

You now know:
- How to use Selenium to automate a web browser
- How to find and interact with elements on a webpage
- How to loop and conditionally perform actions
- How to waste a lot of computational resources for a silly game (a valuable life skill)

## Next Steps

Want to make it even more automated? Try:
- Adding logic to detect and click golden cookies
- Tracking your cookie per second (CPS) and logging it
- Creating a GUI to start/stop the bot
- Realizing this is just the beginning and you're now a full-stack Cookie Clicker developer

Now go forth and let your bot achieve cookie dominance.

P.S you need to add your own creative touch and new feature to get your project approved! Don't forget to put in that creative touch in the Description.
Submit Day 8 [here](https://forms.hackclub.com/haxmas-day-8)

WARNING: NO AI SHOULD BE USED