# (PCB) Printed Christmas Board Workshop



![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/ba7b56ae2d400af1_image.png)

**Prize: $10 PCB production grant + 1 snowflake**

## Index
- Setup EasyEDA
- Creating a Project in EasyEDA
- Schematic Editor
- PCB Editor (Setting Up Multicolor Silkscreen)
- Design Your Ornament
- Ordering the Board

---

## Set Up Accounts

Head over to [EasyEDA](https://easyeda.com/) and create an account if you haven’t already. EasyEDA is a web-based PCB design tool that supports multicolor silkscreen printing through JLCPCB and this is why we’ll be using it for our project.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/b77d829a6e6aac9a_image.png)

	You’re free to use your preferred EDA software, though keep in mind that multicolor silkscreen may not be supported in all platforms. (There are some plugins for kicad but I have not tested them myself)


---

## Creating a Project

After creating an account and logging into EasyEDA, go to [https://pro.easyeda.com/](https://pro.easyeda.com/) and click **Use Online**, or directly visit [https://pro.easyeda.com/editor](https://pro.easyeda.com/editor).

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/7422085c5002b520_image.png)


Next, go to `File -> New -> New Project`, name your project, and click **Save**.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/7ed34913b70af7a1_image.png)

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/751c8699f76d2384_image.png)

Once saved, your project will automatically open. On the left sidebar, you’ll find both the schematic and PCB pages.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/1919f6db92d32eb3_image.png)

---

## Schematic Editor

Double-click **Schematic1** to open the schematic view.
![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/a5ce3496f02a0906_image.png)
Here, you can place your symbols and components, which will later appear in the PCB editor when you update the PCB layout.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/2aebe23c3268d5f9_image.png)

For the sake of simplicity in this tutorial, we’ll skip adding any components like LEDs and resistors. Instead, we’ll head straight to the PCB editor to design the ornament itself.

---

## PCB Editor

Double-click **PCB1** to open the PCB editor. You’ll see a blank canvas where you can design your PCB.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/9c91b7321947b8e0_image.png)

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/8c0df8c4b34ce26c_image.png)

On the right sidebar, open the **Layers** panel. There are many layers listed, but for this tutorial, we’ll focus on three main ones:
- Board Outline Layer  
- Top Silkscreen Layer  
- Bottom Silkscreen Layer  

**Board Outline Layer:** Defines the physical shape and size of your PCB, including any cutouts or slots. This layer tells the manufacturer exactly where to cut.

**Top Silkscreen Layer:** Prints component labels, decorations, or logos on the top of the board. For your ornament, this is where most of your visual design will appear.

**Bottom Silkscreen Layer:** Prints labels or designs on the underside of the PCB. Useful for double-sided decorations or additional visual elements.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/d5049e66c88b33c6_image.png)



### Designing the Ornament Shape

1. Select the **Board Outline Layer** from the right sidebar.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/e081c027eea4bcd4_image.png)


2. From the top toolbar, choose the **Line Tool**. Click the dropdown and select **Circle**.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/d2d027236a120172_image.png)

3. Draw a large circle with a radius of **40 mm** to serve as the ornament’s main body. Simply click anywhere and then enter 40 for the radius and press enter.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/110bc9a3b1250268_image.png)


4. Create a smaller circle with a **5 mm** radius, this will form the hole at the top for hanging.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/6851af70ee1e1748_image.png)

5. Select both circles and align them horizontally. 

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/457fb8bf8bd259ef_image.png)

6. It will ask then you to select The Reference Object. Simply click on one of the circles

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/60d77703855f869e_image.png)

7. Move the smaller circle to move it slightly on the top edge of the larger circle. Hold Shift will moving it so that it only moves in one dimension.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/370254842c0d8455_image.png)

Here's how it should look like after you move it

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/2039a9922d4b1595_image.png)

It should NOT be like this

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/9023b3cf9116f546_image.png)
![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/a61947174f8bb252_image.png)



8. Now select both circles, go to `Edit -> Convert To -> Board Outline`.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/235494f0310a774a_image.png)

It should look like this after you do this step

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/d2562d86b0d0f7ee_image.png)

9. Next, create a **Slot Zone** with a **2 mm** radius.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/e86b514dc565e0fe_image.png)

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/7134f0a3096ffca7_image.png)

10. Center the slot vertically by selecting both objects and choosing Horizontally Center.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/0f4217c492a063fc_image.png)


11. Hold **Shift** and drag the slot region up or down as needed until it’s well positioned and looks vertically centered inside the small circle.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/62f2eeb61ab9656d_image.png)

Click the **3D** button to preview your PCB. You should now see the 3D render of your ornament outline.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/433fba75f09d33a8_image.png)

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/6391205ef227ad00_image.png)

---

## Adding Your Own Designs

Now lets head back into the PCB editor and add some cool designs 

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/fdb526ea57f9098b_image.png)

Before importing any artwork, let’s ensure that the **Multicolor Silkscreen** feature is enabled.

1. Go to **Settings -> PCB -> General**.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/f949d9b20a35c8de_image.png)

2. Scroll down to find **Using JLC Color Silkscreen Technology**.  
3. Make sure it’s enabled, then click Confirm.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/d354b2137e0faa35_image.png)

Now you can add your own artwork:

1. Go to `File -> Import -> Image`.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/18d19701b3553c4a_image.png)

2. In the **Insert Image** dialog, check **Place Original Image**.  

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/438cff2b206ff595_image.png)

3. If your image file is large, set the image size to under **90 mm** .you can always scale it later in the editor.  

**Tips:**  
- Use high-quality **300 PPI PNG or JPG** files for best results.  
- Avoid low-resolution images, as they may appear pixelated during printing.

Once imported, position the image wherever you’d like on the board. By default, it will appear on the **Top Silkscreen Layer**. Make sure to scale up your image so that it's background overflows out of the PCB.

Tip: You can hold shift while scaling to ensure it's ratio is consistent


![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/2578993d23d20b50_image.png)

To preview how your PCB looks click on the 3D Preview again , select **Colorful Silkscreen** as the silkscreen technology under the PCB editor settings.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/0695901865bd9d3e_image.png)

This is how it should finally look

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/23fc5218b820cad8_image.png)



If you’d like to add designs on the back of the PCB, simply:
1. Click the image you imported.  
2. In the **Properties** panel, change the **Layer** dropdown to **Bottom Silkscreen Layer**.  
3. Adjust placement as desired.

---
## Ordering the Board

Once you’re happy with your design, it’s time to generate the files and place your order.

1. In the PCB editor, Go on the top bar and click on the order PCB icon

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/55c90eda2deb2d8a_image.png)

You're going to get a bunch of dialogs, just continue and it will then take you over to JLC

2. You will see something like this on the order page 

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/0f8049aa6c935a71_image.png)

3. Change your settings as shown

Under PCB Specifications change PCB Color to White and Surface Finish to ENIG
![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/b1e95ac05f2bea9f_image.png)

Then scroll down and open advanced options dropdown and select EasyEDA multi-color silkscreen as your Silkscreen Technology
![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/8eeb408a8ee6db52_image.png)

After that just add it to your cart and you should be all set!

4. Click [here](https://u.easyeda.com/account/user/coupon/activating?uuid=aaf0cac0bd17447293ccde82d97bed9c) to claim a $10 coupon which you can use towards your board.

Make sure to activate the coupon!

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/ece99086b6505182_image.png)



---

## Submitting your project

1. Export your source files!

Go to file -> Save as -> Project Save as (Local) 
This should give a .epro file.

![img](https://hc-cdn.hel1.your-objectstorage.com/s/v3/98869e79b08836a5_image.png)

2. Create a GitHub repository and upload the .epro file


3. Head over to the [Submit Form](https://forms.hackclub.com/haxmas-day-2) and submit your project. (For the Playable URL you can just use your GitHub URL)


4. Now simply wait for a few days to get your grant! Once you get the grant you can order your PCB :D
