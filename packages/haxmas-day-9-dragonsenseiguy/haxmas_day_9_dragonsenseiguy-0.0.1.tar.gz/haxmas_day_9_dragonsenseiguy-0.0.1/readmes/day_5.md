# Full Stack App with Flask

Hi yall! I'm Niko and we're going to take Haxmas up a notch and build a full stack app in Python, using the Flask framework!

Expect this guide to take ~4 hours. If you have any questions, please direct them to #haxmas on Slack!

An example (though bland) can be found at https://nikospancakes.pythonanywhere.com.

# Prerequisites

**TL:DR: Python 3.13+ & Pip are required. A GitHub account along with a Railway account is required. VSCode is highly recommended, along with the Python extension. AI is prohibited.**

Check if Python + pip are installed with the commands below in your terminal app (on Windows, Command Prompt):

```bash
python --version
pip --version
```

If you need to install Python, Check the links below for installation instructions.

- [MacOS](https://docs.python.org/3.13/using/mac.html)

- [Windows](https://docs.python.org/3.13/using/windows.html#pymanager) (You may want to go through the Microsoft Store!)

- [Linux](https://docs.python-guide.org/starting/install3/linux/) (If you are using Linux, Python will likely be included already.)

This guide assumes that you are using Visual Studio Code, available [here](https://code.visualstudio.com/Download). 

We also recommend that you install the Python extension in VSCode before you begin. You will find how to install extensions at [this link](https://code.visualstudio.com/docs/getstarted/extensions)

Finally, you will need a [GitHub](https://github.com) and [Railway](https://www.railway.com) account. Both are free!

# Intro to a full stack app

A full stack app is an application which consists of two parts, the frontend and backend!

The frontend is what you can see. All of the behind the scenes stuff, like storing your info, user data, and more happens on the Backend.

Throughout the course of this guide, we are going to learn how to build both ends of a full stack app! If you've done previous workshops, you may know React and Hono. React is a frontend, Hono is a backend. Today, we're going to do both!

## Frontend

Uh oh! You have a lot of gifts to give out, but you keep forgetting who to give what! Let's build a website to fix that.

Start with the steps below:

1. Create a new project folder and open it in VSCode
2. Create a folder named `static`
3. Create an `index.html` file within `static`

![Gif showing how to create a folder](https://hc-cdn.hel1.your-objectstorage.com/s/v3/cc8dfbb2ecd2be11_adobe_express_-_screen_recording_2025-12-14_at_23.19.28.gif)

What we are going to do first is to:
1. Create a basic structure.
2. Add some basic text.

Copy down what you see below in `index.html`

```html
<!DOCTYPE html>
<html>
    <head></head>
    <body></body>
</html>
```

You may notice HTML uses tags like `<p></p>` to structure content. Let's go over our tags!

- `<head>` tells our browser information about our website.

- `<body>` is  what actually gets displayed on your website

- `<!DOCTYPE html>` tells our browser to render our website a certain way and prevents inconsistent rendering.

Next, lets add some content! Replace your code with this new code!

```html
<!DOCTYPE html>
<html>
    <head>
    </head>
    <body>
        <div class="content">
            <h1>[Your Name's] Gift Tracker!</h1>
            <p>Tracking gifts since 2025</p>
        </div>
    </body>
</html>
```

- `<h1>` indicates a header, and can vary from `<h1>` to `<h6>`, moving down in size.

- `<p>` indicates body text.

You may notice a `<div>` element! This is a "container", but we can leave it alone for now.

Now, you may want to take a look on your website. In order to do this, you'll want to install the "Live Server" extension by Ritwick Dey! You will find how to install extensions at [this link](https://code.visualstudio.com/docs/getstarted/extensions)

Next, click the button in the bottom right that says "Go Live"!

![Image of the bottom right with a red arrow pointing to a Go Live button](https://hc-cdn.hel1.your-objectstorage.com/s/v3/b0b41dbcb706e090_image.png)

Don't worry if you're redirected to a page like the page below. Click "static" to get to your webpage! If you're not automatically redirected, navigate to http://127.0.0.1:5500 in your browser.

![Image of a red arrow pointing to a icon of a folder and the word static to the right of it](https://hc-cdn.hel1.your-objectstorage.com/s/v3/5a4d09f68e7c45da_screenshot_2025-12-14_at_23.35.29.png)

![Image of the website](https://hc-cdn.hel1.your-objectstorage.com/s/v3/8fe20a12dfd51eec_screenshot_2025-12-14_at_23.39.44.png)

Our website looks a bit bland. Let's add a form so that we can add gifts, make it look good, and add some interactivity!

Firstly, let's start by adding an image to our website! We can use the `<img>` tag, which does not need a closing tag. The `src` attribute tells it where to find our image.
Add this beneath your title! 
```html
<img src="https://haxmas.hackclub.com/haxmas-logo.png">
```

![Image of the website](https://hc-cdn.hel1.your-objectstorage.com/s/v3/e29584b5f485fc17_screenshot_2025-12-14_at_23.59.09.png)

Now, we're going to want to work on a form element to take inputs.

We'll need a `<form>` tag in order to create our form! Take a look at the code below and copy it below your `<p>` tag.

```html
<form id="giftForm">
  <label for="name">First name: </label>
  <input id="name" type="text" name="name" required>
  <br>
  <label for="gift">Gift: </label>
  <input id="gift" type="text" name="gift" required>
  <br>
  <input type="submit" value="Submit!">
</form>

```

Okay, great! As a quick explanation, you may notice that the `<label>` tags have a "for" attribute! This tells it which input it corresponds to. In the `<input>` tags, you may notice three things: `type`, `name`, and `required`! The only one important for now will be `name`, which is what our backend will see when the form is submitted.

Next, in order for us to be able to display their data, we're going create a container that we can put their gifts into. Underneath the `<form>` closing tag, add in the code below:

```html
<div id="gifts"></div>
```

## Checkpoint 1

At this point, your code will look something like this:

```html
<!DOCTYPE html>
<html>
    <head>
    </head>
    <body>
        <div class="content">
            <h1>Niko's Gift Tracker!</h1>
            <img src="https://haxmas.hackclub.com/haxmas-logo.png">
            <p>Tracking gifts since 2025</p>
            <form id="giftForm">
                <label for="name">First name: </label>
                <input id="name" type="text" name="name" required>
                <br>
                <label for="gift">Gift: </label>
                <input id="gift" type="text" name="gift" required>
                <br>
                <input type="submit" value="Submit!">
            </form>
            <div id="gifts"></div>
        </div>
    </body>
</html>
```

It's alright if some text is different, but the core structure should be the same. Here's a photo of what this looks like!

![Image of the website](https://hc-cdn.hel1.your-objectstorage.com/s/v3/ca9da9937228813e_screenshot_2025-12-15_at_22.33.56.png
)

Okay! Now, you might notice that trying to submit the form does...nothing! Let's fix that with something called Javascript! Javascript lets us add interactivity to our website.

Inside of our `static` folder, create a file called `main.js`.

Next, return back to `index.html` and in between our `<head>` tags, add this:

```html
<script src="./main.js" defer></script>
```

All this code does is tell the website where to find the script. `defer` tells it to wait for the website to load before loading the script.

Inside of the main.js file, here's what we're going to need to do:

- Find our gift submission form
- Hook into it when they click submit
- Read the fields
- Add it into the page!

First, start by adding this to your file:

```javascript
const form = document.getElementById("giftForm")
const giftsContainer = document.getElementById("gifts");
```

Here, we use `const` because the variable (i.e. `form` or `giftsContainer`) itself won't change. Even if the page changes, the reference to the form stays the same. This is where our `id` attributes are coming in! document.getElementById stores a reference to our elements, which we can then modify!

You may have noticed that clicking submit reloads the page. This is default behavior, but we want to prevent that. Add this line below all of your code:

```javascript
form.addEventListener("submit", (event) => {
  event.preventDefault();
});
```

This tells our code to listen for a submit event on the form, and then prevent it from doing the default action. Next, after `event.preventDefault();`, you'll want to write this code:

```javascript
const name = form.elements.name.value;
const gift = form.elements.gift.value;

const item = document.createElement("p");
item.textContent = `Gift for ${name}: ${gift}`;
giftsContainer.appendChild(item);

form.reset();
```

Here, we define three constants. The first two constants are from our form. You may realize that now, our `name` attribute on our form elements have become handy! Next, we create a `<p>` element, add in our text, and then add it into the container so that we can see it. Finally, we clear the form. 

You can also, for example, use the `let` keyword instead of `const` to define a variable! This simply defines a variable instead of intializing it as a cosntant, meaning that you intend for the value to be modified.

## Checkpoint 2

Here is what your JS code should be looking like!

```javascript
const form = document.getElementById("giftForm")
const giftsContainer = document.getElementById("gifts");

form.addEventListener("submit", (event) => {
    event.preventDefault();

    const name = form.elements.name.value;
    const gift = form.elements.gift.value;

    const item = document.createElement("p");
    item.textContent = `Gift for ${name}: ${gift}`;
    giftsContainer.appendChild(item);

    form.reset();
})
```

Try submitting a gift and your website should look like this!

![Image of the website at checkpoint 2](https://hc-cdn.hel1.your-objectstorage.com/s/v3/d34f5cae0c7bd160_screenshot_2025-12-15_at_23.20.50.png)

Okay, everything *mostly* works, but it doesn't look great. let's style this a little bit using CSS (or Cascading Style Sheets). It lets us change how our website looks!

Create a file in `static` called styles.css and then add this line inside the `<head>` section of your HTML:


```html
<link rel="stylesheet" href="./styles.css">
```

This tells the browser to load our CSS file from the given location.

Here's what to put into our CSS file:

```css
body {
    margin: 0;
    padding: 0;
}

.content {
    text-align: center;
    font-family: Arial, sans-serif;
}
```

Confused? Don't worry, here's whats happening:

- `body` applies styles to the entire page. These are what we call selectors!
  - `margin: 0` and `padding: 0` remove the browser's default spacing to make our content container the main container. This is an example of a modifier.
  - `font-family` sets the font for all text on the page. 

- `.content` targets the main container we created earlier, specifically the class we assigned to it!
  - `text-align: center` centers the text inside the container.

All CSS modifiers must end with a semicolon!

If you want to customize it more or understand CSS better, a good resource will be [W3Schools](https://www.w3schools.com/css/default.asp)!


## Checkpoint 3

Here is what all of your files should look like so far:

index.html:
```html
<!DOCTYPE html>
<html>
    <head>
        <script src="./main.js" defer></script>
        <link rel="stylesheet" href="./styles.css">
    </head>
    <body>
        <div class="content">
            <h1>Niko's Gift Tracker!</h1>
            <img src="https://haxmas.hackclub.com/haxmas-logo.png">
            <p>Tracking gifts since 2025</p>
            <form id="giftForm">
                <label for="name">First name: </label>
                <input id="name" type="text" name="name" required>
                <br>
                <label for="gift">Gift: </label>
                <input id="gift" type="text" name="gift" required>
                <br>
                <input type="submit" value="Submit!">
            </form>
            <div id="gifts"></div>
        </div>
    </body>
</html>
```

main.js
```javascript
const form = document.getElementById("giftForm")
const giftsContainer = document.getElementById("gifts");

form.addEventListener("submit", (event) => {
    event.preventDefault();

    const name = form.elements.name.value;
    const gift = form.elements.gift.value;

    const item = document.createElement("p");
    item.textContent = `Gift for ${name}: ${gift}`;
    giftsContainer.appendChild(item);

    form.reset();
})
```

styles.css
```css
body {
    margin: 0;
    padding: 0;
}

.content {
    text-align: center;
    font-family: Arial, sans-serif;
}
```

# Backend

Now, you might notice that reloading the page causes our gifts to be lost! That's because there's no backend to keep track of our gifts! Let's fix that.

Before we begin, let's create a virtual environment. This keeps our project's Python packages isolated from the rest of your system, and prevents it from breaking!

In VSCode:
 
1. Go onto the top search bar
2. Type in `>Python: Create Environment`
3. Select Venv
4. Select your Python install

If you are not in VSCode, search up how to create a venv and follow these instructions inside of your project folder. VSCode should automatically activate your venv, but if not, on the bottom right select yes when prompted if you would like to activate the virtual environment.

Next, we need to install Flask.

1. Open the Command Palette
2. Type `>Create New Terminal (With Profile)`
3. Press Enter
4. Then, copy the line below into your terminal and hit enter:

```bash
pip install flask
```

If this fails, try `python -m pip install flask`

Now, create a `main.py` file **outside** of the `static` folder. This will be our backend.

Inside, add these lines:

```python
import flask

app = flask.Flask(
    __name__,
    static_folder="static",
    static_url_path="/"
)

@app.get("/")
def index():
    return flask.send_from_directory("static", "index.html")

if __name__ == "__main__":
    app.run()
```

Let's go through what this is doing:
- `app = flask.Flask(...)`
    - This creates our Flask app! __name__ tells Flask where our file is so it can find stuff correctly.
- `static_folder="static"`
    - This tells Flask where to find the frontend that we just created
- `static_url_path="/"`
    - This tells flask to serve our static files at the root (/) instead of /static.
- `@app.get("/")`
    - This tells flask that the next function should be served at the `/` route.
- `def index():`
    - This simply defines our function, anything indented after it is a part of it. Think of a function as a piece of reusable code which can be called anywhere.
- `return flask.send...`
    - This tells it to get our index.html file and "return" it to the client, letting us see it!
- `if __name__ ==...`
    - This simply tells the app to run. The == sign is an equality checker, and it could be useful later onwards for extra touches!

Next, we're going to modify our code a little bit to add something called a database! This is where our gifts will be stored. Think of it like a table! We're going to want three columns: an id, a name, and a gift column! Replace your code with this:

```python
import flask
import sqlite3

app = flask.Flask(
    __name__,
    static_folder="static",
    static_url_path="/"
)
conn = sqlite3.connect('gifts.db') 
cursor = conn.cursor()  
cursor.execute('''
    CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gift TEXT NOT NULL
    )
''')
conn.commit()  
conn.close()

@app.get("/")
def index():
    return flask.send_from_directory("static", "index.html")

if __name__ == "__main__":
    app.run()
```

You may notice some new sections. This is how we are creating our database!

First, at the top, we're importing our libraries. When the app is launched, it will:

1. Open a connection to our database (which will, as a side effect, create a file for the database if it doesn't exist yet)
2. Intialize a cursor that lets us execute SQL commands
3. Create a table called gifts if it doesn't exist yet with the following attributes:
    - A autoincrementing id
    - A name that is text and not empty
    - A gift that is text and not empty
4. Saves the changes to the database
5. Closes the connection to the database

This lets us make sure we are always writing to a valid table! Now. let's add two more routes: One for creating a gift, and one for reading a gift! 

Add these lines after your first route:

```python
@app.post("/gifts")
def create_gift():
    data = flask.request.get_json()
    name = data.get('name')
    gift = data.get('gift')
    
    conn = sqlite3.connect('gifts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO gifts (name, gift) VALUES (?, ?)', (name, gift))
    conn.commit()
    conn.close()

    return '', 201
    
@app.get("/gifts")
def get_gifts():
    conn = sqlite3.connect('gifts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, gift FROM gifts')
    rows = cursor.fetchall()
    conn.close()
    
    gifts = [{'id': row[0], 'name': row[1], 'gift': row[2]} for row in rows]
    return flask.jsonify(gifts)
```

Let's go through the routes one by one.

You may wonder why they are both able to be the same route. That's because they use different HTTP methods. For this use case, GET is used to *get* content while POST is used to *post* or send content to the server, which lets use use two functions for one route. `@app.get` indicates a GET request on a route, while `@app.post` indicates a POST request on a route.

You may notice that in the POST endpoint, we get the JSON from the request with `flask.request.get_json()`. This is so that we can convert what the frontend will eventually send into something the backend can read. JSON is just a way for us to store that data! Next, we do the same thing we did when creating the database, except we insert a new record with the recipient's name and their gift. Finally, we return no content and a status code of 201, which indicates it was created!

Next, we do the same thing with the DB in the GET endpoint, except we read all the gifts, create a list out of the gifts, and then return it in JSON form to the frontend. Now, our backend is complete!

## Checkpoint 4

Here is what your main.py code should look like:

```python
import flask
import sqlite3

app = flask.Flask(
    __name__,
    static_folder="static",
    static_url_path="/"
)

conn = sqlite3.connect('gifts.db') 
cursor = conn.cursor()  
cursor.execute('''
    CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gift TEXT NOT NULL
    )
''')
conn.commit()  
conn.close()

@app.get("/")
def index():
    return flask.send_from_directory("static", "index.html")

@app.post("/gifts")
def create_gift():
    data = flask.request.get_json()
    name = data.get('name')
    gift = data.get('gift')
    
    conn = sqlite3.connect('gifts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO gifts (name, gift) VALUES (?, ?)', (name, gift))
    conn.commit()
    conn.close()

    return '', 201
    
@app.get("/gifts")
def get_gifts():
    conn = sqlite3.connect('gifts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, gift FROM gifts')
    rows = cursor.fetchall()
    conn.close()
    
    gifts = [{'id': row[0], 'name': row[1], 'gift': row[2]} for row in rows]
    return flask.jsonify(gifts)

if __name__ == "__main__":
    app.run()
```

You can test it by going to your terminal (where you installed your dependencies) and run the following command:

`python3 main.py`

If this fails, you can also try `python main.py`.

Then, if prompted, allow local network access. Finally, navigate to 127.0.0.1:5000 on your browser. Note that 127.0.0.1:5500 (your live server link) will no longer work! 

# Putting it together

You may notice that while the backend works, nothing on the frontend actually uses anything on the backend! Let's fix that.

Go back to your `main.js` file in `static/*`

Let's add a function! Copy this code into your main.js after your variable declarations but before `form.addEventListener`.

```javascript
async function loadGifts() {
    const response = await fetch('/gifts');
    const gifts = await response.json();
    
    giftsContainer.innerHTML = '';
    gifts.forEach(gift => {
        const item = document.createElement("p");
        item.textContent = `Gift for ${gift.name}: ${gift.gift}`;
        giftsContainer.appendChild(item);
    });
}
```

Here, we are introduced to the concept of async! In short, imagine this like calling your friend and asking for something (in this case, a list of gifts). They tell you that they will give it to you later, and then you do something else until they give it to you. This is effectively what async does! It allows the website to respond even while waiting for web requests.

Here, we simply just fetch the gifts, wait for the JSON, then for each gift we receive, we create a `<p>` tag with the gifts info and add it to the container!

Next, we'll want to replace our current submission flow! Replace those lines with the code below:

```javascript
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = form.elements.name.value;
    const gift = form.elements.gift.value;

    await fetch('/gifts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, gift })
    });

    form.reset();
    await loadGifts(); 
});
```

All we change here is that instead of just adding it, we send it to the server and then refetch our gift list!

Finally, at the end of your file, add a new line and then add this code in:

```javascript
loadGifts();
```

This simply loads our gifts when the page loads, which allows us to see them instantly!

## Checkpoint 5

Here is what your JS code should look like!

```javascript
const form = document.getElementById("giftForm")
const giftsContainer = document.getElementById("gifts");

async function loadGifts() {
    const response = await fetch('/gifts');
    const gifts = await response.json();
    
    giftsContainer.innerHTML = '';
    gifts.forEach(gift => {
        const item = document.createElement("p");
        item.textContent = `Gift for ${gift.name}: ${gift.gift}`;
        giftsContainer.appendChild(item);
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = form.elements.name.value;
    const gift = form.elements.gift.value;

    await fetch('/gifts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, gift })
    });

    form.reset();
    await loadGifts(); 
});

loadGifts();
```

# Final touches

Alright, we're almost there! Let's add rate limiting!

We don't want people to spam our website! Rate limiting stops them from doing so by limiting how many requests they can make to our server in a given time period.

Open your terminal (instructions are at the beginning of the backend section), and run the command:

```bash
pip install Flask-Limiter
```

Next, after your imports, you'll want to add:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
```

Now, after you declare the app variable, add this:
```python
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day"],
    storage_uri="memory://",
)
```

Here's what this code is doing:

1. It creates a Limiter instance
2. Tells it our app instance
3. Tells it what our default limits are
4. Tells it to store it in memory.

Okay, now we can start adding rate limits! You can choose not to add rate limits if you believe the default is enough, or you can specify routes to be exempt!

For example, let's modify our root page to allow unlimited requests.

Modify the section of code which begins with `@app.get("/")` to look like:

```python
@app.get("/")
@limiter.exempt
def index():
    return flask.send_from_directory("static", "index.html")
```
This tells it that it's exempt from the rate limit! Here are some examples of what it would look like with higher or lower rate limits:

```python
@app.get("/")
@limiter.limit("1 per day")
def index():
    return flask.send_from_directory("static", "index.html")
```

```python
@app.get("/")
@limiter.limit("1 per second")
def index():
    return flask.send_from_directory("static", "index.html")
```

Feel free to add rate limits wherever!

**You MUST define limiter before all of your routes, or you will face errors!**

Now, what if you wanted to replace the image? That is surprisingly simple!

Head to Google images, click on an image you like, then right click it! Hit "Copy Image Address", then replace the URL with the URL you just copied. URLs that begin with `data:` should still work, but note you may run into issues.

As a final thought, you might want to look into how to check for a password! Let me lay it out for you in case you want to do this, though this is optional!

1. Add a password option on the form on your frontend
2. On each route, check if the input password matches the supply password
    - PS: To securely store the password, you might want to look into how environment variables work, or a .env file! [GeeksForGeeks](https://www.geeksforgeeks.org/python/how-to-create-and-use-env-files-in-python/) is a great resource.
    - You **DO NOT** want to store your password inside of your python file! This means everyone will be able to access your data.
    - Make sure that when deploying, you remember to copy your .env variables over! This is usually as simple as inputting your key and value, but on PythonAnywhere, you may need to manually create one.
        - For Railway, you may find [this](https://docs.railway.com/guides/variables) useful!
        - For PythonAnywhere, all you need to do is to create a .env file (`touch .env`), and then copy the contents of your file into it! (use `nano` to do so!)

# Before you submit...

Add a few of your own touches! A few resources will be linked below. Here are some ideas for you:

- Add a way to check gifts as complete
- Require the user to use a password to get in
- Add a custom background
- Switch the image

At the minimum, we expect you to mess around with the CSS a little bit, like changing the color around. (PS, you can add something like `background-color: green` in your `.content` section in the CSS!)

For resources, check out [W3Schools](https://w3schools.com)! Heres a list of some you might find useful:
- [HTML](https://www.w3schools.com/html/default.asp)
- [CSS](https://www.w3schools.com/css/default.asp)
- [JavaScript](https://www.w3schools.com/js/default.asp)
- [Python](https://www.w3schools.com/python/default.asp)

Finally, before you publish this, you'll want to create a file called .gitignore at your root, and then add `venv/` and `gifts.db` on separate lines inside of it! This is to prevent your virtual environment from being included.

You'll also want to create a file called `requirements.txt` with the following content:

```text
flask
Flask-Limiter
gunicorn
```

Okay, you're almost done!

Initialize a git repo and push it to GitHub! You can find out how to do so [here](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github#initializing-a-git-repository). This assumes you have already made a git repo!

You'll also want to test it. To reload your code (assuming that you are still running your python file), hit control + c in your terminal, then run `python main.py` or `python3 main.py` again.

Now, let's deploy it.

# Deployment

Let's use Railway! Once you've logged in, deploy a project using your repository! (When you are selecting new project, simply select Github Repository and select your repo!)

First, go into settings, then type "gunicorn main:app --bind 0.0.0.0:$PORT" under Custom Start Command in the Deploy section.

Next, when it tells you it is done deploying, click on the box inside of your project, go to settings, and click "Generate Domain" under networking. If you're having trouble, a video below shows you how to do this! This is the same section in which you will be able to set the start command.

![Video demonstrating the process to deploy on Railway](https://hc-cdn.hel1.your-objectstorage.com/s/v3/bc78994383b47f18_adobe_express_-_b00184244f371099_screen_recording_2025-12-16_at_01.06.47.gif)

Congratulations! You may now submit [here](https://forms.hackclub.com/haxmas-day-5)! Your playable URL should be the domain that Railway just deployed for you.


## Alternative deployment method

In the event that you're unable to deploy to Railway, you may need to use [PythonAnywhere](https://pythonanywhere.com), another hosting service which is fully free. This is slightly more complicated, so follow along closely. You will need to know the URL which your GitHub repo is located at as well as its name. It should look like `https://github.com/hackclub/hackmas-day-5`. Before we begin this section, remember to create an account.

Follow these steps in order:
1. Under dashboard, click "Open Web tab"
2. Click "Add a new web app"
3. Click Next
4. Click Manual Configuration
5. Select Python 3.13
6. Select Next

Now, you should be set up with a web app. Do not touch anything. Open a new tab of PythonAnywhere, and go to the dashboard. Then, follow these next steps:

1. Under consoles, select `$ Bash` under New Console.
2. Subsitute `YOUR-URL` in the following command with your URL. paste it in the terminal (cmd + v or ctrl + v), and hit enter.
```bash
git clone YOUR-URL
```

The output will look like this:

```bash
Cloning into 'hackmas-day-5-demo'...
remote: Enumerating objects: 25, done.
remote: Counting objects: 100% (25/25), done.
remote: Compressing objects: 100% (17/17), done.
remote: Total 25 (delta 7), reused 22 (delta 4), pack-reused 0 (from 0)
Receiving objects: 100% (25/25), done.
Resolving deltas: 100% (7/7), done.
```

3. Now, there is a new folder which is the name of your repository! You will know based on the output of the previous command, as the name is within the line: `Cloning into 'YOUR-REPO-NAME'`. Run the following command, replacing `YOUR-REPO-NAME` with the name of your folder:

```bash
cd YOUR-REPO-NAME && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

Good, we're almost there! Return to the Web tab, and do the following

1. Next to "Source Code", click the text then enter this (replacing YOUR-USERNAME with your PythonAnywhere username and YOUR-REPO-NAME the same name as in step 3):

`/home/YOUR-USERNAME/YOUR-REPO-NAME`

Example: `/home/nikospancakes/hackmas-day-5-demo`

2. Under virtualenv, click the text that says "Enter path to a virtualenv, if desired", and enter the following (same replacements as step 1)

`/home/YOUR-USERNAME/YOUR-REPO-NAME/venv`

Example: `/home/nikospancakes/hackmas-day-5-demo/venv`

3. Under Code, select the blue text to the right of "WSGI Configuration File".

4. Replace all the text in the file with this (replace YOUR-USERNAME and YOUR-REPO-NAME the same way you did in step 1 of this portion):

```python
import sys

path = '/home/YOUR-USERNAME/YOUR-REPO-NAME'
if path not in sys.path:
    sys.path.append(path)

from src.haxmas_day_9_dragonsenseiguy.main import app as application
```

5. Final step. On the top right, click save, exit back to the web app management page, and click "Reload YOUR-USERNAME.pythonanywhere.com".

Your app is now deployed on PythonAnywhere! Again, you may now submit [here](https://forms.hackclub.com/haxmas-day-5)! The playable URL should be your "YOUR-USERNAME.pythonanywhere.com" URL.