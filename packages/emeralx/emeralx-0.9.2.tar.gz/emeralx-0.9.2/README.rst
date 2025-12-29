Emeralx is a Python package for creating small games, developed based on Pygame, with the aim of changing the loop-refresh method to a multithreaded approach. The Emeralx library is suitable for making 2D games and currently has four modules: display, events, image, and entity, with more modules planned for development. Emeralx is currently in the beta version.


Installation
============

Before downloading the Emeralx library, you must ensure that Python is already installed on your computer, and the Python version should be above 3.7. Version 3.7 is only the minimum requirement, and some advanced functions may not be available when using it. Once you have installed Python, you can use the following command to install the Emeralx library from the command line.

.. code-block:: bash

   pip install emeralx

After installing the Emeralx library, you can use the following command to ensure that the library was installed successfully.

.. code-block:: bash

   pip list

If the Python library 'Emeralx' appears in the list, it means you have successfully installed it.


Help
====

Our documentation is actively being written. To view the basic help documentation, please write the following code in your Python program.

.. code-block:: python

   import emeralx
   help(emeralx)


Quick Start
===========

· Basic framework:

.. code-block:: python

   import emeralx

   window=emeralx.display.Window() # Create a window object.

   room=emeralx.display.Room(window) # Create a room on the window.
   room.set_caption("NewGame") # Set caption for the room, which will show on title bar.
   room.switch() # Switch to the window.

   window.listen() # Window Mainloop.

· Create a Animation of sprite and show it on window

.. code-block:: python

   import emeralx

   window=emeralx.display.Window() # Create a window.

   room=emeralx.display.Room(window) # Create a room.
   room.switch()

   img=emeralx.image.Animation(path="xxx.gif")
   sp=emeralx.entity.Sprite(room,img,position=(0,0)) # Create a sprite object.

   emeralx.events.When(window,emeralx.events.EACH_FRAME_STEP()).do(lambda:sp.next_texture()) # Change to next texture.

   window.listen() # Mainloop.

· Draw a text on the window

.. code-block:: python

   import emeralx

   window=emeralx.display.Window() # Create a window.

   room=emeralx.display.Room(window) # Create a room.
   room.switch()

   text=emeralx.canvas.Text("Hello World!",(0,0))
   room.place(text) # Put the text on the room and display on window.

   window.listen() # Mainloop.


Changelog
=========

· 0.8.0 beta version : Develop the four main Python packages and have the ability to create basic games.

· 0.8.2 beta version : Fixed the bug that prevented packages from being imported.

· 0.8.5 beta version : Added some methods to the Sprite object, and added a Camera object to the display module.

· 0.9.1 beta version : Added the audio module and canvas module, and moved the window coordinate origin to the center.  

· 0.9.2 beta version : Fixed some small bugs.

License
=======
MIT License - Check the LICENSE file for details.