# Fusion Exporter

##  An add-in for Fusion 360

### Synopsis
 The add-in implifies the task of exporting Fusion 360 designs for 3D printing. Typically exporting would require selecting the individual component, clicking on Export from the Modify menu, entering a file name, choosing the export file type then pressing the Export button. This would have to be repeated for each component in the design. This add-in cuts that down to two clicks.

### Installation
I just save the add-in on my machine (I'm using a Mac, but a Windows machine should work just as well), the using the Scripts and Add-ins manager - under Utilties. Then I use the + sign and Script or Add-in from device. I navigate to the folder comtaining the add-in and choose Open. The add-in is then loaded (I choose to open it on start-up). It creates an icon below the Utilities menu - it looks like a document with an arrow. Then by clicking on the icon I open the add-in's window.

### Usage
 All 3d print files are saved below a root directory - for example "3D Prints" below your home directory - you can choose what folder to save your files in, though it will be under your home directory

### Simple use
 If you have a design set out with multiple components, (e.g a design named "My Design" having components named "Component 1" and "Component 2"). Choose one file per component, the add-in will save the 3d print files (STL or STEP) in a single folder (named "My Design"). The print files will be named "Component 1.stl" and "Component 2.stl" (or .step)

 If you have a design with no components, or with just one component (e.g a design named "My Simple Design"), the add-in will save a single print file named "My Simple Design.stl" (or .step). This is a bit more logical than creating a folder "My Simple Design" with a single .stl file (potentially just named "body1.stl").

### More complex use
A more complex scenario is where you have a design with multiple components, but you want to save it in a single file. You might do this if you want to print a single plate with multiple parts - maybe you want them to be printed in different colours. (e.g a design named "My Complex Design" having two components named "Part 1" and "Part 2") . In this case you can choose to export one file, multiple bodies. The add-in will create a single file named "My Complex Design.stl" (or .step) which will have two sub-parts named "Part 1" and "Part 2"

### Notes
The add-in removes version numbers when it saves files. This means if you have design named My Design and have saved v1, it will be exported as "My Design.stl". When you save v2 or v3 etc, and export again, the file will still be named "My Design.stl" - it will overwrite the existing stl file. This means in your slicer you just need to reload from disk to get the new version of your design. If you wanted to keep the old stl version you would need to do that manually

The add-in can save files in STL, STEP or 3MF format. I tried saving 3MF format hoping my slicer (Bambu Studio) might be able to use colour or filament data that I might put in the file. So far I have not figured out how that data is saved, so I always save in STEP format - I hve no rational reason for preferring STEP over STL.

### License
    Fusion Exporter © 2025 by Derek Knight is licensed under CC BY-NC-SA 4.0. To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/
