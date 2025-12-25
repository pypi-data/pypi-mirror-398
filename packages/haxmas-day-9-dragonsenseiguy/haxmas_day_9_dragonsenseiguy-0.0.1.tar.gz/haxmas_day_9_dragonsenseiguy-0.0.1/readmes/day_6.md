# Let's make a 3D printable ruler together!

Hello, i'm William! 

Ive put together what i hope is a follow-able guide on how to make a ruler in fusion 360

there should also be an onshape guide releasing 

Good luck and have fun!

This will take ~2 hours.

**Prize: Your ruler printed and mailed to you + 2 snowflakes**

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/d0917dbd29c0218a_527321254-671ef482-5fce-4c28-94b9-5f2684285427.jpg" alt="image" />

---
**Note for CAD nerds:**

I know there will people saying [insert-cad-here] is better and whatnot, however fusion is what im most comfortable with, if you’re more familiar with other CAD software you’re more than welcome to use that. I’m not saying fusion is the perfect or the best, because its neither.
But even if you do know other CAD, why not try something new, try fusion :3 


# 1). an introduction

**A quick pic of what we are trying to make**
<img src="https://github.com/user-attachments/assets/671ef482-5fce-4c28-94b9-5f2684285427" alt="image" />

this is just a plain ruler, most rullers will start off looking something like that, however i encourage and expect that you will customise them to your hearts content to make your ruler uniquely yours :3




## Fusion 360 UI

hopefully your fusion360 looks something like this
<img width="2514" height="1208" alt="image" src="https://github.com/user-attachments/assets/3fe5b671-ccde-46fb-a34b-4657f6b16c87" />
all the tools we will be using to draw sketches and turn those sketches into 3D things should all be at the top of the screen

**my favourite key bind**
s - search

<img width="724" height="439" alt="image" src="https://github.com/user-attachments/assets/e948c10d-9b12-437d-89c9-a60ad9c4f8bd" />

if you ever get stuck because i say something and you just can’t find it, this key bind is a life saver.

it’s also cool because if you’re looking for a feature in fusion you can just type in the name and see if it exists


**Key binds for moving around your model:**

pan - hold middle mouse button
zoom - scroll mouse wheel
orbit - hold shift + middle click + mouse button




**IMPORTANT NOTE:**
**unlike onshape, fusion does not auto save, make sure you regularly save to avoid accidents**

and like almost all software
save - ctrl+S 




# 2). beginnings of the ruler

now for making the ruler
the max size of ruler we can print for you is:
### 200mm long, 70mm wide, 4mm tall
(i made it big so you don’t skip past it)
so please keep your maximum dimensions below that







We want to start by drawing out an overhead outline of out ruler
<img alt="_DSC2267" src="https://github.com/user-attachments/assets/ca7f1040-3068-4fc7-ab95-b10ee664e16e" />
<img width="1919" height="1177" alt="image" src="https://github.com/user-attachments/assets/f51ba94f-7f8a-49c0-84e3-379ff05b2cc4" />

then we need to select a plane to start drawing on 
you can click any of the orange squares and it will work

your screen should look something like this
<img width="1919" height="1177" alt="image" src="https://github.com/user-attachments/assets/8f7153ef-34c5-4cc3-8ec0-5ebb261cb168" />

now we can use the 2-point rectangle tool to draw a rectangle that will define how big our ruler is!
<img width="1919" height="1176" alt="image" src="https://github.com/user-attachments/assets/d9e713d4-4cc2-4485-87b7-3345cfa5112b" />

with the 2-point rectangle tool:
- you click on the canvas to start or stop drawing
- you can type in numbers to set the size
  - you press tab to switch between them

your ruler should look something like this
<img width="1919" height="1199" alt="image" src="https://github.com/user-attachments/assets/9d402ac1-5254-4a66-9bc4-6d9b2e94ba19" />

now we can press finish sketch to finish the sketch
<img width="1919" height="1174" alt="image" src="https://github.com/user-attachments/assets/82a551f1-e613-4f66-b2ad-db62b8dc8c3a" />

next we want to make the 2d drawing into the start of our 3d ruler
to do this we use the extrude tool
you can either click the icon
<img width="43" height="59" alt="image" src="https://github.com/user-attachments/assets/67815310-567a-468c-9251-46e1a6b78b27" />

or use the shortcut - e 

because we only have one sketch it has probably auto selected it
but if not

in the extrude pop up, click on profiles
and then click the filled in bit of the ruler we just drew

now we can extrude it the distance we want by setting the distance number in the extrude tab
I’m going to make my ruler 3mm thick

so, you should be here
<img width="1919" height="1176" alt="image" src="https://github.com/user-attachments/assets/0bb1c539-53fb-469e-8aec-1ef5bce51c77" />

and you can press ok now

well done! 
you’ve made the start for our ruler

# 3). adding the gradations

don’t be scared by the word gradations, it’s not some fancy fusion thing, it’s just the name for the marks on a ruler. 


to do this we are going to draw and make one mark
and then use the "rectangular pattern" tool to copy it across the ruler without drawing it a bunch


### how big to make the gradations?
gradations smaller than 1mm probably won’t print due to the 0.4mm nozzles that are common on 3d printers

the back ruler has 5mm spacings
the closer one has 1mm spacings
personally, i think the 5mm ones are clearer to read 
<img alt="_DSC2270" src="https://github.com/user-attachments/assets/da2270f6-fc01-45d6-b147-9bd4539d4304" />


a closer up pic of the 1mm gradation ruler
<img alt="_DSC2269-2" src="https://github.com/user-attachments/assets/d8f0afbd-0915-424a-b7a4-50ebd5d00f9d" />


for my ruler I want short marks every 5mm
and big marks every 10mm

so let’s start on the smaller ones

we want to start by making 1 mark in the ruler

to do that we now  draw a sketch of what the marks look like
<img width="1919" height="1147" alt="image" src="https://github.com/user-attachments/assets/26fd2715-9ef7-4335-9bcd-d54ae11c7d27" />
so we click the new sketch button
and click the top of our ruler where we want the mark

my prefered method for doing it goes something like this
<img width="1918" height="1147" alt="image" src="https://github.com/user-attachments/assets/018d1652-bd21-467c-96da-f17466deceb9" />
drawing a line how far apart the marks should be from the edge
so, for me 5mm

i want my markings to be 5mm long, and 0.4mm wide
i also want them to be centred on the point we just marked

so, we can draw a two 0.2mm x 5mm rectangle on either side

next we finish the sketch
and then extrude into the ruler to make the marking! :yay:
<img width="1919" height="1178" alt="image" src="https://github.com/user-attachments/assets/7f077ba6-e1b4-49ac-b2a5-36636924a70c" />

<img width="1919" height="1170" alt="image" src="https://github.com/user-attachments/assets/349580c7-5508-4ddd-b30e-bf666dfdab2b" />
like this!

<img width="1917" height="1175" alt="image" src="https://github.com/user-attachments/assets/4654bc43-315d-487d-b4c2-b242da0fc359" />

now we are going to use a pattern to make the pattern continue down the ruler!
<img width="1916" height="1176" alt="image" src="https://github.com/user-attachments/assets/65891933-f245-4e8a-a5f7-a6391c0e7c7e" />

we are trying to pattern the cut we made, which is a feature
so we need to change from bodies to feature
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/a82e4a1bbe391615_527764991-00b7c656-4b8e-4206-8592-651d153c355a.png" alt="image">
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/d64f6fc0837d6ed5_527764533-1b68468f-8836-42f8-9914-62ff2d45e4fa.png" alt="image">


now we need to select the feature
to do this we can either  

try hover over the indent and hope it works
or 
we can click the extrude feature we made in the timeline (I prefer this method)
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/2cb8a7ede3ffb941_527766526-037ade76-efbc-466e-9bb7-172ae4d22c0a.png" alt="image">

next we next to pick the "axis" this is just the direction that fusion makes the pattern in
we can just pick the long edge of the ruler
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/4370005f23eafaaa_527765713-071a856e-ee26-43be-a03d-2377b2be61c3.png" alt="image">


now we also want to change the mode from extent to spacing
and set the distance to how often we want the markings
i want them to be 5mm apart so i put 5mm in

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/2cb8a7ede3ffb941_527766526-037ade76-efbc-466e-9bb7-172ae4d22c0a.png" alt="image">
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/c4d4066edfb9c4d5_527774386-c13902ce-cb05-46e2-b15f-4f1a356d5f94.png" alt="image">

now we can see a preview

we just need to increase the quantity, 
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/329f1b37e9fc9906_527775052-d26f7833-6e5c-4cb4-b8ef-adc377aaa356.png" alt="image">

boop
now we have the markings :yay:
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/329f1b37e9fc9906_527775052-d26f7833-6e5c-4cb4-b8ef-adc377aaa356.png" alt="image">


---
we can repeat that process for centimetre markings 

if you did simple rectangle marking like I did
you could just extrude every other one deeper
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/097b07f9704542ce_527776700-15e55195-83c3-4bdb-951a-1708519fbdb6.png" alt="image">
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/3fe58958d0c70db3_527776953-fe09b1be-66d9-408e-815b-cbfd75a0fa7f.png" alt="image">


the other way would be repeating the process for the first markings, but you make them bigger / a different shape, and set the spacing to 

# 4). adding the numbers (optional)

time to add numbers!
if you want numbers that is.
you don’t need to add numbers, if you want the extra space for customising it the way you want feel free to leave them out.

so first we are going to create a new sketch on the top of the ruler again
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/75a8b825b032a79f_527814032-f9d99d69-9cba-463d-a9a9-d7cff6baa036.png" alt="image">


then we can use the line tool to draw out a box where we want our numbers to be (the number don’t need to fill up the box)
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/c9fbeb76e7f12124_527814832-1df2605f-69a6-4a8d-a71a-b9d40d3d42fc.png" alt="image">


i made the lines into "construction" lines
which just means that, you can snap onto them and use them to construct things. but they won’t affect which parts a filled in i think the term is "non-printing"
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/0c89cdc74975ed65_527815537-0ca73688-7e69-49ec-a535-37c202c3d93a.png" alt="image">


then we can use the pattern tool to put one above each marking where we want a text box
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/f22f5dec2f0a3e2a_527816201-10d61704-4f76-4ad3-80ac-af1e3f820d41.png" alt="image">

you could draw them out by hand
but i don’t think either of us fancy drawing out 15 boxes

so, we select all the lines that we want in the pattern
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/a4962008afc1adcd_527816359-3b18b435-ebf4-45cd-868e-d2e6b33a6a3a.png" alt="image">


we pick a direction
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/a0db0ef798daf364_527816460-eededb1f-0a9a-4806-86bb-9b94cce26292.png" alt="image">


<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/65bafa1903f83ab0_527816647-47dad7ee-e273-470c-9ae7-af66df1d010b.png" alt="image">
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/be475d4406d0dfc8_527816729-ac894583-e52f-4d7f-9a69-c897bd7d207e.png" alt="image">


next we have to add the text

<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/d0a9f849c5586767_527816854-a4d25416-321d-455c-ae96-6937ab312e77.png" alt="image">


so now we have a box which we can click in two places to define the corners
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/3e9e607e3f6b3c2c_527817186-a2994e64-156e-4b38-bebb-49a936b1e528.png" alt="image">


I let it snap onto two opposite corners in the first box

and I type 1 into the window on the right
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/b30335a10ef140fd_527817441-b66f0a51-f40c-4293-9b73-5c9f96ae65d0.png" alt="image">


it’s also worth considering what size you make your font now
because if you have double digit amount of units
make sure you have space for that in the text boxes

I also picked align centre for horizontal and vertical

so, a font size like this will clearly overlap with the next letter
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/f8aa3b7b0c409fa9_527817926-8d4f44bc-5fe5-463c-a50b-61d3e1e6d445.png" alt="image">


but a font like this should be ok
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/4b2ebc755b02f55c_527818120-3998bce9-0040-415a-a900-07a7f586ebb4.png" alt="image">


a bit of clicking later you should have something like this
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/2ea6550925066090_527818816-74c8e5c6-4c41-4ae4-bcb5-3a3c42065a05.png" alt="image">


---
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/b303602093cce918_527783022-805cd3b0-71ed-42bc-9576-3bddbbc1f3ae.png" alt="image">


hopefully you are at a point that looks something like this!

---










# finish adding the rest of ruler


Now you should have a ruler!
however, you’re not quite done yet
for the next part you’re on your own

the last part of this is customising your ruler

**here are some ideas:**
- perhaps make it a cool shape, in the first step we made our ruler a rectangle, why not make one of the sides wavy
- different shaped gradation makes on the ruler
  - instead of the little line i used, perhaps a triangle, or whatever else you can come up with
- crazy units?  Cubit, Smoots, Links, Light nanosecond etc
- add a cool pattern
  - perhaps hexagon cutouts
  - stripes on it cut into it
- perhaps you want to add some text on it with the text tool
- add graphics
  - you can import SVGs into sketches, so you could draw an Orph, convert it to an SVG, and have and Orph ruler
  - **if you add art it has to be yours**
  - **AI "art" is strictly prohibited**

and if you’re struggling to do something, give it a google search, there are plenty of amazing YouTube tutorials and forums out there with guides on how to do everything under the sun!

**Example photos**


example of different shaped tick pattern
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/f080a87a51cc5334_527880615-5d105ce4-b3ec-4c26-b8eb-e56b8297891e.png" alt="image">


neocat ruler, example of being able to add art
fusion has an import SVG function that helps with this 
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/52102b5ecebfc435_527880667-a582d9d7-d8c7-4ab7-9c2a-7a1081d23b07.png" alt="image">


example of some things you could do to the edge of the ruler
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/fb315b6484042851_527880862-6a6183d3-eff7-490d-8be8-0ceab97dde98.png" alt="image">


a cool wavy pattern in the ruler
i just clicked around with "split point spline" in the sketch to make it, looking forward to the cool things you guys come up with!
<img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/3272f934c83b4ca0_527880973-cb6e2c0d-ccba-42cf-b1f9-e4e7ac208e2d.png" alt="image">


**Submit at https://forms.hackclub.com/haxmas-day-6**









