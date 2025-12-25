> # [!WARNING]
> # You are NOT legally allowed to use the Phantom Sans font without a license. Do not use the font unless if you have a license. Not complying with this is violating copyright laws.

# Introduction

Hey everyone! I’m Astra, and I’ll be guiding you through how to make a simple interactive Christmas tree using HTML, CSS, and JavaScript

Before we start, create **three files in the same directory**. The CSS and JavaScript file can be named something else but the HTML file should be named `index.html`:

- `index.html`
- `style.css`
- `script.js`

Throughout this workshop, I’ll be using those file names as an example

If you’re using an IDE or editor, your HTML file might start out looking like this:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Haxmas Day 7</title> <!-- This shows up as the browser tab title -->
</head>
<body>

</body>
</html>
```

This is a great starting template.

HTML elements usually have an **opening tag** and a **closing tag**, like `<title>` and `</title>`. Everything between them is part of that element.

---

## Section 1:  HTML

Before we start styling and scripting anything, we need to make sure we have something to do that with.

We're going to be making some `div`s. The `<div>` tag is a powerful and flexible container used to group elements together. Think of it as an invisible box.

####  IDs and Classes

- IDs are for labelling a unique element (meaning there shouldn't be 2 elements with the same ID)
- Classes label _groups of elements_ that share styles or behavior

  both of these are used to identify, control, and add specific attributes to specific elements.

```html
<body>
    <div id="header">
        <h1 class="important-text">Haxmas Day 7</h1>
        <h2 id="date"></h2>
    </div>

    <div id="tree-container" class="container">
        <div id="star"></div>
        <div id="decorations"></div>
    </div>

    <div id="footer">
    </div>
</body>
```

You can then insert other elements inside the `div`s and attributes put onto said `div` will also be put onto those elements as well! This is called inheritance which will be important in the next section.

Here's how it looks populated!

```html
<!DOCTYPE html>  
<html lang="en">  
<head>  
    <meta charset="UTF-8">  
    <title>Haxmas Day 7</title>  
</head>  
<body>  
    <div id="header">  
        <h1 class="important-text">Haxmas Day 7</h1>  
        <h2 id="date">December 19, 2025</h2>  
    </div>
    <div id="tree-container" class="container">  
	    <img src="img/tree.png" id="tree">  
	        <div id="star">⭐</div>  
		        <div id="decorations">  
					<img src="img/ornaments/1.webp" id="ornament">
			    </div>
	        </div>
        <div id="footer">  
        <h3 class="important-text">workshop made by astra</h3>  
    </div>
</body>  
</html>
```

#### Images (`<img>`)

To insert images, you would utilize the `<img>` tag. Unlike most HTML elements, this does not have a closing tag. To link the image file you want to use, you can use `src="relative/path/to/file.png"` like this:

```html
<img src="img/tree.png" id="tree">
```

It's good practice to put images in their own directory for organization. Here's how my file tree looks!

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/920e44b395755718_screenshot_2025-12-19_at_21.21.20.png">

Now if we try to open this and take a look...

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/9a9659fdeb5fce24_screenshot_2025-12-19_at_21.29.14.png">

... It looks terrible. All the things we want *exists*, but none of it looks good and nothing's in the place we want it to be. That brings us to our next section...

---
## Section 2: CSS

CSS is what actually makes your site looks good, it's what *stylizes* the webpage - colors, sizes, overlays. Those are all CSS! But before you do anything. you'll have to link your CSS file to the HTML file first.

In your `<head>` tag, link your CSS file like this:

```html
<!DOCTYPE html>  
<html lang="en">  
<head>  
    <meta charset="UTF-8">  
    <title>Haxmas Day 7</title>
    <link rel="stylesheet" href="style.css">  
</head>
```


### Text, colors, fonts, backgrounds

First off, let's add some custom fonts and colors!
```css
@font-face {  
    font-family: 'Phantom Sans';  
    src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Regular.woff')  
    format('woff'),  
    url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Regular.woff2')  
    format('woff2');  
    font-weight: normal;  
    font-style: normal;  
    font-display: swap;  
}  
@font-face {  
    font-family: 'Phantom Sans';  
    src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Italic.woff')  
    format('woff'),  
    url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Italic.woff2')  
    format('woff2');  
    font-weight: normal;  
    font-style: italic;  
    font-display: swap;  
}  
@font-face {  
    font-family: 'Phantom Sans';  
    src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Bold.woff')  
    format('woff'),  
    url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Bold.woff2')  
    format('woff2');  
    font-weight: bold;  
    font-style: normal;  
    font-display: swap;  
}

body{  
    font-family: 'Phantom Sans', sans-serif;  
    background-image: url("img/backgroundtile.png");  
    color: azure;  
}  
  
#header, #footer{  
    text-align: center;  
}
```

The `@font-face` sections defines a font that isn't already installed (Hint: check out hackclub.com/branding for some great fonts and colors!).

The bits without a prefix (such as `body{...}`) will apply the attributes to every tag of that type
The ones with a `#` prefix (like `#header{...}`) will apply to the tag with that **id***
The ones with a `.` prefix (like `.decoration{...}`) will apply to all tags with that **class***

Since the `body` tag encompasses the entire visible page, anything you put in there will apply to the entire page, unless overwritten by the attributes of another tag. Here, besides from setting the font using `font-family`, and font color `color`, you can set the background image by using `background-image: url("path/to/image.png")` (Alternatively, you can use `background-color` or `background-image: gradient(...)`).

`text-align: center` puts the text at the center. This is applied to the `header` and `footer` divs!

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/f58d6ed961c20805_screenshot_2025-12-19_at_22.31.00.png">

Now this is how it looks. Slightly better but still not good, no problem, we're gonna fix that in the next step...

#### Layout: display, position, margins

```css
#tree-container {
    max-width: 20rem;
    display: flex;
    margin: auto;
}

#tree {
    width: 20rem;
    margin-top: 4rem;
}

#star {
    position: relative;
    margin: 0 -13rem;
    font-size: 5rem;
    cursor: pointer;
}
```

You can experiment around with the sizes and margins here until it looks right!
Attributes like margin lets you declare the margin size of each direction like this: `margin: up right down left`


#### Layering with z-index

Sometimes you'll have elements that are covered by others. If you don't want that, you can try using `z-index` (it works as long as `position:static`)

```css
#star {
...
z-index: 5;
}

.ornament {
...
z-index: 10;
}

#tree {
...
z-index: 0;
}
```

Higher `z-index` values appear **on top** of lower ones.

---

## Section 3: JavaScript

Just like the CSS file, you need to link your JavaScript file as well.
Add this anywhere in your `<body>`:
```html
<script src="script.js">```

#### Working with dates

```js
const date = new Date();
const days = date.getDate();
const month = date.getMonth() + 1;
const year = date.getFullYear();
```

We use this to:

- show today’s date
- decide how many ornaments to add

### Accessing HTML elements

```js
const decorations = document.getElementById("decorations");
const dateText = document.getElementById("date");
const star = document.getElementById("star");
```

JavaScript can **find and control HTML elements** using their IDs.

### Waiting for the DOM

```js
document.addEventListener('DOMContentLoaded', () => {
    // ...
});
```

This makes sure JavaScript runs **after the HTML has loaded**.
This works by adding an event listener to `document` (which is the entire document) to see when it loads! Only then will it execute

```js
star.addEventListener('click', changeStar);
```

This adds a click event listener to `#star`.

Now to implement everything!


```js
//getting date  
const date = new Date();  
const days = date.getDate();  
const month = date.getMonth() + 1;  
const year = date.getFullYear();  
  
//list of all the images in img/ornaments and a list of emojis the top decoration thing can be  
const ornamentImg = ["1.webp","2.gif","3.png","4.png","5.png","6.png","7.webp","8.png","9.png","10.png","11.png","12.png","13.png","14.jpg", "15.gif","16.png", "17.png", "18.png"];  
const stars = ["⭐", "💫", "💖", "🎄", "🏴‍☠️", "👾"];  
  
function changeStar(){  
    let randomIndex = Math.floor(Math.random() * 6 );  
    document.getElementById("star").innerText = stars[randomIndex];  
}  
  
//checks if the HTML elements have loaded before doing anything  
document.addEventListener('DOMContentLoaded', () => {  
    //sets the elements with the IDs to variables for easy access!  
    const decorations = document.getElementById("decorations");  
    const dateText = document.getElementById("date");  
    const star = document.getElementById("star");  
  
    //sets the text inside dateText to DD/MM/YY (the superior format)  
    dateText.innerText = days + "/" + month + "/" + year;  
  
    //checks if the month is december  
    if(month === 12){  
        let daysTilChristmas = Math.max(25-days,0);  
  
        //for each day til christmas; it adds another ornament to the christmas tree  
        for(let i = 0; i < daysTilChristmas; i++){  
            const randomImg= ornamentImg[Math.floor(Math.random()*18)]  
            decorations.innerHTML += `<img src="img/ornaments/${randomImg}" class="ornament" id="ornament${i}">`;  
            const ornament = document.getElementById("ornament"+i);  
            //sets the margins to a random value between (4,3) and (14,5)  
            ornament.style.marginLeft = (Math.random()*10+4)+"rem";  
            ornament.style.marginTop = (Math.random()*2+3)+"rem";  
        }  
    }  
  
    star.addEventListener('click', changeStar);  
})
```

```css
@font-face {
  font-family: 'Phantom Sans';
  src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Regular.woff')
  format('woff'),
  url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Regular.woff2')
  format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Phantom Sans';
  src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Italic.woff')
  format('woff'),
  url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Italic.woff2')
  format('woff2');
  font-weight: normal;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: 'Phantom Sans';
  src: url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Bold.woff')
  format('woff'),
  url('https://assets.hackclub.com/fonts/Phantom_Sans_0.7/Bold.woff2')
  format('woff2');
  font-weight: bold;
  font-style: normal;
  font-display: swap;
}

body{
  font-family: sans-serif;
  background-image: url("img/backgroundtile.png");
  color: azure;
}

#header, #footer{
  text-align: center;
}

#tree-container{
  max-width: 20rem;
  display: flex;
  margin: auto auto;
}

#star{
  display: inline-block;
  position: relative;
  margin: 0 -13rem;
  font-size: 5rem;
  z-index: 5;

}

#tree{
  width: 20rem;
  display: inline;
  margin: 4rem 0 0 0;
  z-index: 0;
}

#decorations{
  display: inline-block;
}

.ornament{
  height: 2rem;
  position: relative;
  display: inline-block;
  margin-top: 10rem;
  margin-left: 10rem;
  z-index: 10;
}

.important-text{
  color:#5bc0de;
}
```

And we're done!

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/ce4568bc020b052e_screenshot_2025-12-19_at_22.50.29.png">

---

Happy Haxmas hack clubbers!!!
