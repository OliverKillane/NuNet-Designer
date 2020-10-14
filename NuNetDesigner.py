import json
from math import pi, cos, sin
from tkinter import Tk, filedialog
from itertools import chain
from pygame import *
from pickle import dump, load, PickleError
from operator import itemgetter


# Position is used to store coordinates (as well as vectors) in terms of both pixels,
# and as a fraction of the window (worldcoordinates). By storing positions using an object,
# gui elements can simply request the pixel coordinates when drawing and be given the correct
# position regardless of any scaling or window resizing that has occured.
class Position:
    def __init__(self, screen, xcoor, ycoor, *options):

        # By holding the screen object (a pygame surface), the position can directly access the screen's dimensions at all times, this removes
        # The need for a complex position screensize updating procedure, simplifying the code.
        self.__screen = screen

        # Setup of the positions x and y coordinates
        self.__xcoor, self.__ycoor = xcoor, ycoor

        # Default values for options setup:
        # can be: axes (x and y stretch according to window size), mean (scale according to mean of x,y), square (scale according to diagonal).
        self.__scaleType = "axes"

        # RelCoor attribute flag shows whether the stored x and y coordinates are relative (in tems of fraction of the screen), or absolute (pixels)
        self.__relCoor = True

        # Anchor decides which corner of the screen the coordinates are set from, mainly useful for scaling the screen with absolute coordinates, for example
        # the toolbar position stays set to the bottom right of the screen.
        self.__anchor = ["top", "left"]

        # The options parameter contaisn all arguments passed after 'ycoor', and enables the scaletype, relcoor and anchor to be set up and changed from defaults.
        for option in options:
            if option in ["axes", "mean", "square", "xaxis", "yaxis"]:
                self.__scaleType = option
            elif option == "rel":
                self.__relCoor = True
            elif option == "pixel":
                self.__relCoor = False
            elif option in ["top", "bottom"]:
                self.__anchor[0] = option
            elif option in ["left", "right"]:
                self.__anchor[1] = option

    # Scalervalue function returns a set of values for the x and y coordinates of the position, determining a value based on the scaletype
    # and screen size that can be used for determining object sizes, and new positions.
    def __scalervalue(self):
        screensize = self.__screen.get_size()
        if self.__scaleType == "axes":
            return screensize
        elif self.__scaleType == "mean":
            mean = sum(screensize) / 2
            return mean, mean
        elif self.__scaleType == "square":
            # Find the diagonal length of the screen using pythagoras' theorem.
            diagonal = int(math.sqrt(screensize[0] ** 2 + screensize[1] ** 2))
            return diagonal, diagonal
        elif self.__scaleType == "xaxis":
            return screensize[0], screensize[0]
        elif self.__scaleType == "yaxis":
            return screensize[1], screensize[1]

    # pixelx returns the absolute (in pixels) position of the position class, this is useful when using relative coordinates, as even when the screen is
    # resized, the pixelx function still returns the pixel position corresponding to the relative position passed.
    def pixelx(self):
        if self.__relCoor:
            if self.__anchor[1] == "left":
                return int(self.__xcoor * self.__scalervalue()[0])
            else:
                return int((1 - self.__xcoor) * self.__scalervalue()[0])
        else:
            if self.__anchor[1] == "left":
                return self.__xcoor
            else:
                return self.__screen.get_size()[0] - self.__xcoor

    # pixely returns the absolute (in pixels) position of the position class, this is useful when using relative coordinates, as even when the screen is
    # is resized, the pixely function still returns the pixel position corresponding to the relative position passed.
    def pixely(self):
        if self.__relCoor:
            if self.__anchor[0] == "top":
                return int(self.__ycoor * self.__scalervalue()[1])
            else:
                return int((1 - self.__ycoor) * self.__scalervalue()[1])
        else:
            if self.__anchor[0] == "top":
                return self.__ycoor
            else:
                return self.__screen.get_size()[1] - self.__ycoor

    # pixel returns a two item list containing the x, y pixels
    def pixel(self):
        return self.pixelx(), self.pixely()

    # relx returns the relative x-position of the object on the screen
    def relx(self):
        if self.__relCoor:
            if self.__anchor[1] == "left":
                return self.__xcoor
            else:
                return self.__screen.get_size()[0] - self.__xcoor
        else:
            if self.__anchor[1] == "left":
                return self.__xcoor / self.__scalervalue()[0]
            else:
                return (self.__screen.get_size()[0] - self.__xcoor) / self.__scalervalue()[0]

    # rely returns the relative x-position of the object on the screen
    def rely(self):
        if self.__relCoor:
            if self.__anchor[0] == "top":
                return self.__ycoor
            else:
                return self.__screen.get_size()[1] - self.__ycoor
        else:
            if self.__anchor[0] == "top":
                return self.__ycoor / self.__scalervalue()[1]
            else:
                return (self.__screen.get_size()[1] - self.__ycoor) / self.__scalervalue()[1]

    # rel returns a two item list containing the x, y relative positions
    def rel(self):
        return self.relx(), self.rely()


# The worldposition class is used for the grid of the editor interface. It converts the position of the camera (the area of the grid being displayed),
# the screensize and a position in the grid into a position in pixels for a given gui element. As fro getting pixel positions the methods are identical
# to the Position class, this can be used as an alternative to Position for a gui object, placing it at a position in the grid in doing so.
class WorldPosition:
    def __init__(self, screen, camera, xcoor, ycoor, size=False):

        # setup of required attributes:
        # Storing the screen reference (so that screensize can be accessed easily)
        self.__screen = screen

        # Stopring the camera object (contains zoom as well as camera position to be accessed readily)
        self.__camera = camera

        # Setup of the xcoor, ycoor of the grid.
        self.__xcoor, self.__ycoor = xcoor, ycoor

        # Setup of the size flag, true means that the position is a size and hence only needs to be scaled with zoom, not with the camera's position.
        self.__size = size

    # Pixelx returns the x-coordinate of a worldposition in terms of pixels across the screen, and in the case of sizes, the width of the size.
    def pixelx(self):
        # Checking if the worldposition is a size (in which case cameraposition is not considered)
        if self.__size:
            return int(self.__xcoor * self.__camera.getzoom())
        else:
            # If not a size, the cameraposition needs to be considered as the object may be off screen.
            return int((self.__xcoor - self.__camera.getposition()[0]) * self.__camera.getzoom())

    # Pixely returns the y-coordinate of a worldposition in terms of pixels across the screen, and in the case of sizes, the height of the size.
    def pixely(self):
        if self.__size:
            return int(self.__ycoor * self.__camera.getzoom())
        else:
            return int((self.__ycoor - self.__camera.getposition()[1]) * self.__camera.getzoom())

    # Pixel returns the pixely and pixelx results as one list for convenient use.
    def pixel(self):
        return self.pixelx(), self.pixely()

    # Worldx returns the worldposition's x-value.
    def worldx(self):
        return self.__xcoor

    # Worldy returns the worldposition's y-value.
    def worldy(self):
        return self.__ycoor

    # Pixel returns the worldy and worldx results as one list for convenient use.
    def world(self):
        return self.__xcoor, self.__ycoor


# The camera class is used for the implementation of the grid in which the user edits their network design. It contains the camera's position within
# that grid, and the zoom view, this enabled the conversion of worldcoordinates into a pixelposition on the screen, and the translation of the users
# view back and forth across the grid, as well as zooming to a point determined by the mouse.
class Camera:
    def __init__(self, screen, worldposition, zoom):

        # storing of the screen object for easy access to screen dimensions (useful when determining screensize).
        self.__screen = screen

        # worldcoordinates represent the positions of markers on the grid interface the user uses to design networks. Positions are defined in
        # terms of x and y, with both potentially being negative as to allow for an infinitely large grid.
        self.__worldPosition = worldposition

        # Zoom represents the number of pixels per world coordinate, and is used for determining absolute pixel positions from worldpositions.
        self.__zoom = zoom

    # Getposition simply returns the current worldposition of the camera object.
    def getposition(self):
        return self.__worldPosition

    # Getsize returns the size in terms of worldcoordinates of the screen, this is useful for checking if an object needs to be rendered (rather
    # than attempting all), and hence reduce rescource utilisation.
    def getsize(self):
        size = self.__screen.get_size()
        return size[0] / self.__zoom, size[1] / self.__zoom

    # Getzoom returns the zoom, the number of pixels per worldposition.
    def getzoom(self):
        return self.__zoom

    # Move moves the camera to a new position by a distance determined by a 2d vector of worldcoordinates.
    def move(self, moveby):
        self.__worldPosition[0] += moveby[0]
        self.__worldPosition[1] += moveby[1]

    # Setposition sets the position of the camera to a certain point.
    def setposition(self, worldposition):
        self.__worldPosition = worldposition

    # setzoom sets the zoom level to an argument.
    def setzoom(self, zoom):
        self.__zoom = zoom

    # world to pixel converts a worldposition into a opixelposition on the screen.
    def worldtopixel(self, worldposition, size=False):

        # If checking a size's magnitude in pixels, the camera's position does not need to be considered.
        if size:
            return int(worldposition[0] * self.__zoom), int(worldposition[1] * self.__zoom)
        else:
            return int((worldposition[0] - self.__worldPosition[0]) * self.__zoom), int((worldposition[1] - self.__worldPosition[1]) * self.__zoom)

    # Pixeltoworld converts a pixelposition (such as that of the mouse) into a worldposition, this is useful for adding objects to the grid as the
    # program can tell where in the grid the mouse is at a given time.
    def pixeltoworld(self, pixelposition, size=False):
        if size:
            return pixelposition[0] / self.__zoom, pixelposition[1] / self.__zoom
        else:
            return pixelposition[0] / self.__zoom + self.__worldPosition[0], pixelposition[1] / self.__zoom + self.__worldPosition[1]

    # Increasezoom both increases the zoom value (making grid objects larger), but also ensures the zoom is towards the current position of the mouse.
    def increasezoom(self, eventposition):

        # Limit on how far in the user can zoom in the form of an if statement.
        if self.__zoom < 1000:
            # Zoom increased by 10%.
            self.__zoom *= 1.1

            # Conversion of the mouseposition to a worldposition within the grid.
            eventworldposition = self.pixeltoworld(eventposition)

            # Moving the camera to make the zoom centered on the mouse.
            self.__worldPosition[0] += (eventworldposition[0] - self.__worldPosition[0]) * 0.1
            self.__worldPosition[1] += (eventworldposition[1] - self.__worldPosition[1]) * 0.1

    # Increasezoom both decreases the zoom value (making grid objects smaller), but also ensures the zoom is centered on the current position of the mouse.
    def decreasezoom(self, eventposition):

        # Limit on how far the user can zoom out, as at high zooms so many grid crosshairs and network objects are positentially are viewable that
        # the program will slow down due to high rescource utilisation.
        if self.__zoom > 30:
            # Zoom decreased by 10%.
            self.__zoom *= 0.9

            # Conversion of the mouseposition to a worldposition within the grid.
            eventworldposition = self.pixeltoworld(eventposition)

            # Moving the camera to make the zoom centered on the mouse.
            self.__worldPosition[0] -= (eventworldposition[0] - self.__worldPosition[0]) * 0.1
            self.__worldPosition[1] -= (eventworldposition[1] - self.__worldPosition[1]) * 0.1


# A basic GUI element, a coloured rectangle.
class Rectangle:
    def __init__(self, screen, position, size, fillcolour, anchor="topleft"):

        # Storing a reference to the display, so that the rectangle can be easily displayed.
        self.__screen = screen

        # Storing rectangle position.
        self.__position = position

        # Storing a Position/Worldposition object to be used for determining the size of the rectangle.
        self.__size = size

        # Storing fillcolour, using a tuple or RGB values.
        self.__fillColour = fillcolour

        # Storing the anchor, which determines what part of the object the position references.
        self.__anchor = anchor

    # paint is a standard function for GUI objects, it instructs pygame to display the object when the display next updates.
    def paint(self):

        # instructing pygame to draw the rectangle on next display update.
        draw.rect(self.__screen, self.__fillColour, self.__generaterectangle())

    # generaterectangle generates the rectangleobject for both checking if it has been clicked (used in textbutton for example) and for rendering.
    def __generaterectangle(self):

        # create new rectangle of size (size), at the position specified.
        rectangle = Rect(self.__position.pixel(), self.__size.pixel())

        # temporary holding of the rectangle's position for further manipulation
        rectangleposition = self.__position.pixel()

        # using the anchor provided to set the rectangle's position based upon it.
        if self.__anchor == "topleft":
            pass
        elif self.__anchor == "topcenter":
            rectangle.midtop = rectangleposition
        elif self.__anchor == "topright":
            rectangle.topright = rectangleposition
        elif self.__anchor == "midleft":
            rectangle.midleft = rectangleposition
        elif self.__anchor == "midcenter":
            rectangle.center = rectangleposition
        elif self.__anchor == "midright":
            rectangle.midright = rectangleposition
        elif self.__anchor == "bottomleft":
            rectangle.bottomleft = rectangleposition
        elif self.__anchor == "bottomcenter":
            rectangle.midbottom = rectangleposition
        elif self.__anchor == "bottomright":
            rectangle.bottomright = rectangleposition

        return rectangle

    # getposition returns the position of the rectangle.
    def getposition(self):
        return self.__position

    # getsize returns the size of the rectangle
    def getsize(self):
        return self.__size

    # getrectangle returns the pygame Rect of the rectangle, for use in collision detection.
    def getrectangle(self):
        return self.__generaterectangle()

    # getfillcolour returns the current fillcolour of the rectangle.
    def getfillcolour(self):
        return self.__fillColour

    # getalign returns the anchor used for the rectangle's position when drawing to the screen.
    def getalign(self):
        return self.__anchor

    # gettype returns the type of object, in this case 'Rectangle'.
    def gettype(self):
        return "Rectangle"

    # setposition sets the position of the rectangle to the provided argument.
    def setposition(self, position):
        self.__position = position

    # setsize sets the size of the rectangle to the provided argument
    def setsize(self, size):
        self.__size = size

    # setfillcolour sets the colour of the rectangle to a colour provided in the form of a tuple of RGB values.
    def setfillcolour(self, fillcolour):
        self.__fillColour = fillcolour

    # setalign sets the alignment of the rectangle (which part the position is referencing).
    def setalign(self, align):
        self.__anchor = align


# The text class is used for displaying all text in the program, and is used by several other GUI objects for displaying their text.
class Text:
    def __init__(self, screen, text, position, textsize, textcolour, anchor="midcenter"):

        # Screen reference stored so that the textc an be easily drawn to the screen.
        self.__screen = screen

        # Storing the text to be displayed (converted to string as int, and float can be passed to the text attribute but not displayed without conversion).
        self.__text = str(text)

        # Storing the position.
        self.__position = position

        # Storing the text size.
        self.__textSize = textsize

        # storinhg text colour.
        self.__textColour = textcolour

        # Anchor is "midcenter" by default, and determines at what point in the object the position is referencing.
        self.__anchor = anchor

    # A standard method for GUI objects, instructing pygame to display the object when the display is next updated.
    def paint(self):

        # Setup of the textsurface copntaining the text itself.
        textsurface = font.Font("freesansbold.ttf", self.__textSize).render(self.__text, True, self.__textColour)

        # Creating the rectangle in which the text is to be displayed (used by pygame's draw functionality to render the text).
        textrectangle = textsurface.get_rect()

        # Default position of text setup
        textposition = self.__position.pixel()

        # Based on the anchor provided the position is applied to a different point in the textrectangle, this allows for many different
        # arrangements, such as centering text of a given position.
        if self.__anchor == "topleft":
            pass
        elif self.__anchor == "topcenter":
            textrectangle.midtop = textposition
        elif self.__anchor == "topright":
            textrectangle.topright = textposition
        elif self.__anchor == "midleft":
            textrectangle.midleft = textposition
        elif self.__anchor == "midcenter":
            textrectangle.center = textposition
        elif self.__anchor == "midright":
            textrectangle.midright = textposition
        elif self.__anchor == "bottomleft":
            textrectangle.bottomleft = textposition
        elif self.__anchor == "bottomcenter":
            textrectangle.midbottom = textposition
        elif self.__anchor == "bottomright":
            textrectangle.bottomright = textposition

        # Instructing pygame to display the text on next display update.
        self.__screen.blit(textsurface, textrectangle)

    # gettext returns the current text of the text object, this is made use of in the TextEntry class for accessing user input.
    def gettext(self):
        return self.__text

    # getposition returns the current position of the text
    def getposition(self):
        return self.__position

    # gettextsize returns the current font/text size used.
    def gettextsize(self):
        return self.__textSize

    # gettextcolour returns the current colour of the text as a tuple of RGB values.
    def gettextcolour(self):
        return self.__textColour

    # getalign returns the anchor from where the text's position is set.
    def getalign(self):
        return self.__anchor

    # gettype returns the type of object, in this case "Text".
    def gettype(self):
        return "Text"

    # settext sets the text to a given string.
    def settext(self, text):
        self.__text = str(text)

    # setposition sets the position of the text to a new position object
    def setposition(self, position):
        self.__position = position

    # settextsize sets the text size to a new size
    def settextsize(self, textsize):
        self.__textSize = textsize

    # settextcolour sets the text colour to a new colour specified by a tuple of RGB values.
    def settextcolour(self, textcolour):
        self.__textColour = textcolour

    # setalign sets the anchor of the text to a new anchor
    def setalign(self, align):
        self.__anchor = align


# The Image class is used to display images from a relative filename, and allows for transforming the image to different sizes.
class Image:
    def __init__(self, screen, imagesource, position, size, anchor="topleft"):

        # Storing a reference to the screen (for use in 'paint' for displaying the object).
        self._screen = screen

        # Storing the relative file-path of the image file.
        self._imageSource = imagesource

        # Storing the image itself, using the relative file-path and pygame's image functionality.
        self._imageFile = image.load(imagesource)

        # Holding the image surface (used for displaying the image), while initially set to 'None' it is filled by the 'refresh' method.
        self._imageSurface = None

        # Holding the pixel position the image (top left hand corner) for use when displaying. It is updated by the 'refresh' method.
        self._imagePixelPosition = [0, 0]

        # Holding the position of the image.
        self._position = position

        # Holding the size the image will be transformed/stretched to.
        self._size = size

        # Holding the anchor (from where the position references).
        self._anchor = anchor

        # Holding the rectangle of the image (for use in displaying the object, and in the ImageButton for use in click detection).
        self._rectangle = None

        # 'refresh' is run to set up the empty attributes above
        self._refresh()

    # paint is a standard method for displaying the image on the display.
    def paint(self):

        # refreshing the imagesurface, rectangle and pixelposition based on the position, size and anchor .
        self._refresh()

        # instruct pygame to display the object when the screen next updates.
        self._screen.blit(self._imageSurface, (self._imagePixelPosition[0], self._imagePixelPosition[1]))

    # refresh is used for updating the pixelposition, rectangle and image which do not update with scaling, using the position, size and anchor which
    # do. This enables pygame to correctly draw the image.
    def _refresh(self):

        # creating an initial value for the pixelposition.
        self._imagePixelPosition = [0, 0]

        # setting the pixelposition based on the provided anchor, size and position object.
        if self._anchor == "topleft":
            self._imagePixelPosition = [self._position.pixelx(), self._position.pixely()]
        elif self._anchor == "topcenter":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixelx() // 2, self._position.pixely()]
        elif self._anchor == "topright":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixelx(), self._position.pixely()]
        elif self._anchor == "midleft":
            self._imagePixelPosition = [self._position.pixelx(), self._position.pixely() - self._size.pixely() // 2]
        elif self._anchor == "midcenter":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixely() // 2, self._position.pixely() - self._size.pixely() // 2]
        elif self._anchor == "midright":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixely(), self._position.pixely() - self._size.pixely() // 2]
        elif self._anchor == "bottomleft":
            self._imagePixelPosition = [self._position.pixelx(), self._position.pixely() - self._size.pixely()]
        elif self._anchor == "bottomcenter":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixely() // 2, self._position.pixely() - self._size.pixely()]
        elif self._anchor == "bottomright":
            self._imagePixelPosition = [self._position.pixelx() - self._size.pixely(), self._position.pixely() - self._size.pixely()]

        # setup of the image surface (used by pygame to draw the object)
        self._imageSurface = transform.scale(self._imageFile, self._size.pixel())

        # Setup of the rectangle (used for collision detection)
        self._rectangle = Rect((self._imagePixelPosition[0], self._imagePixelPosition[1]), self._size.pixel())

    # getimagesource returns the realtive file-path of the image used.
    def getimagesource(self):
        return self._imageSource

    # getimagefile returns the image being displayed.
    def getimagefile(self):
        return self._imageFile

    # getposition retuirns the position of the object.
    def getposition(self):
        return self._position

    # getrectangle returns the rectangle hitbox of the image for collision detection.
    def getrectangle(self):
        self._refresh()
        return self._rectangle

    # getsize returns the size of the image.
    def getsize(self):
        return self._size

    # gettype returns the type of object, in this case an 'Image'
    def gettype(self):
        return "Image"

    # setimage stes the current image to one defined by a provided relative file-path.
    def setimage(self, imagesource):

        # Changing the imagesource.
        self._imageSource = imagesource

        # Loading the new image file.
        self._imageFile = image.load(imagesource)

    # setposition sets the current position to a new one.
    def setposition(self, position):
        self._position = position

    # setsize sets the current size to a new one.
    def setsize(self, size):
        self._size = size


# The Line class displays a straight line from a start to an end position
class Line:
    def __init__(self, screen, startposition, endposition, width, fillcolour):

        # Store the screen the line is being displayed on for use in the 'paint' methods.
        self.__screen = screen

        # Storing the start position.
        self.__startPosition = startposition

        # Storing the end position.
        self.__endPosition = endposition

        # Storing the value for the width of the line.
        self.__width = width

        # Storing the fill colour for the line.
        self.__fillColour = fillcolour

    # paint is a standard method for GUI Objects and instructs Pygame to display the object when the screen next updates.
    def paint(self):
        draw.line(self.__screen, self.__fillColour, self.__startPosition.pixel(), self.__endPosition.pixel(), self.__width)

    # getcollide determines if a mouseposition is within the hitbox of the line. as collision detection had to be created from scratch (no line
    # collision detection in Pygame) I use the line equation to calculate a hitbox and to check if the mouseposition is in it.
    def getcollide(self, mouseposition):

        # Retrieveing the start and end coordinates in pixels.
        startpos = self.__startPosition.pixel()
        endpos = self.__endPosition.pixel()

        # Determining gradient by dividing change in y over x. This would break for a line with the same x-coordinates, however as this is only used
        # for synapses which cannot be connected vertically such an eventuality cannot occur.
        linegradient = (startpos[1] - endpos[1]) / (startpos[0] - endpos[0])

        # Calculating the y intercept of the line.
        lineintercept = startpos[1] - linegradient * startpos[0]

        # Calculating the y-width of the hitbox using the line graident (if the line was flat, it would be 10 pixels, this is changed for lines at
        # angles using pythagoras.
        ywidth = 10 * abs(startpos[0] - endpos[0]) / ((startpos[0] - endpos[0]) ** 2 + (startpos[1] - endpos[1]) ** 2) ** 0.5

        # Checking if the mouse is within the x bounds of the line (and hence could be touching the line's hitbox).
        if (endpos[0] > mouseposition[0] > startpos[0] or endpos[0] < mouseposition[0] < startpos[0]):

            # Calculating the y-position of the line at the mouse's x-position.
            yposition = linegradient * mouseposition[0] + lineintercept

            # Checking if the mouse y-position is within the hitbox's y-position range, and if so returning 'True' to show the mouse is on the line.
            if (yposition - ywidth) < mouseposition[1] < (yposition + ywidth):
                return True
            else:

                return False
        else:
            return False

    # getstartposition returns the startPosition object for the line.
    def getstartposition(self):
        return self.__startPosition

    # getendposition returns the endPosition object for the line.
    def getendposition(self):
        return self.__endPosition

    # getwidth returns the width value given to the line.
    def getwidth(self):
        return self.__width

    # getfillcolour returns the colour of the line as a tuple of RGB values.
    def getfillcolour(self):
        return self.__fillColour

    # gettype returns the type of object, in this case a 'Line' object.
    def gettype(self):
        return "Line"

    # setstartposition sets the startposition of the line to a new object.
    def setstartposition(self, startposition):
        self.__startPosition = startposition

    # setendposition sets the endposition of the line to a new object.
    def setendposition(self, endposition):
        self.__endPosition = endposition

    # setwidth sets the width of the line.
    def setwidth(self, width):
        self.__width = width

    # setfillcolour sets the fillcolour of the line to a new colour specified by a tuple of RGB values.
    def setfillcolour(self, fillcolour):
        self.__fillColour = fillcolour


# Circle class creates circle objects at the centerposition, with a radius of the magnitude determined by the x-value of radiussize. Its main use is
# for displaying network objects, for example by default neurons are circles.
class Circle:
    def __init__(self, screen, centerposition, radiussize, fillcolour):
        # Storing the screen pygame surface as to ensure
        self._screen = screen

        # Storing the centerposition attribute
        self._centerPosition = centerposition

        # Storing radius size attribute
        self._radiusSize = radiussize
        self._fillColour = fillcolour

    # paint is a standard method for GUI Objects, instructs pygame to display the object when the screen next updates.
    def paint(self):
        draw.circle(self._screen, self._fillColour, self._centerPosition.pixel(), self._radiusSize.pixelx())

    # getcenterposition returns the current center position of the circle.
    def getcenterposition(self):
        return self._centerPosition

    # getradiussize returns the current position defining the radius of the circle.
    def getradiussize(self):
        return self._radiusSize

    # getfillcolour returns the tuple containing the RGB values for the circle's fill colour.
    def getfillcolour(self):
        return self._fillColour

    # getrectangle returns the rectangular hitbox of the circle.
    def getrectangle(self):
        return Rect(self._centerPosition.pixelx() - self._radiusSize.pixelx(),
                    self._centerPosition.pixely() - self._radiusSize.pixely(),
                    2 * self._radiusSize.pixelx(),
                    2 * self._radiusSize.pixely()
                    )

    # gettype returns the type of object.
    def gettype(self):
        return "Circle"

    # setcenterposition sets the centerposition of the circle to a new position provided.
    def setcenterposition(self, centerposition):
        self._centerPosition = centerposition

    # setradiussize sets the object determining circle radius to a new position object.
    def setradiussize(self, radiussize):
        self._radiusSize = radiussize

    # setfillcolouir sets the fillcolour of the object to a new colour described by a tuple of RGB values.
    def setfillcolour(self, fillcolour):
        self._fillColour = fillcolour


# The polygon class is used to create regular shapes of varying number of faces, and is mainly used for displaying network objects in the design
# (e.g be default output neurons are pentagons).
class Polygon:
    def __init__(self, screen, centerposition, radiussize, fillcolour, polygonnumber):
        # Storing a reference to the screen the polygon is to be displayed on.
        self._screen = screen

        # Storing the center position of the polygon.
        self._centerPosition = centerposition

        # Storing the radius size of the polygon (whose x and y dimensions determine the position of the vertices of the shape).
        self._radiusSize = radiussize

        # Storing the colour of the polygon.
        self._fillColour = fillcolour

        # Storing the number of vertices in the polygon.
        self._polygonNumber = polygonnumber

    # 'paint' is a standard method for GUI objects and instructs pygame to display the object when the screen next updates.
    def paint(self):
        # Creating a list to hold the positions of the vertices of the shape
        polypositions = list()
        for index in range(self._polygonNumber):
            # generating the pixel-positions of each vertex based on its number, by moving anticlockwise about the center, the points are placed at regular intervals.
            polypositions.append(
                (int(self._radiusSize.pixelx() * cos(pi * 2 * index / self._polygonNumber)) + self._centerPosition.pixelx(),
                 int(self._radiusSize.pixely() * sin(pi * 2 * index / self._polygonNumber)) + self._centerPosition.pixely()
                 )
            )

        # Instructing Pygame to draw the polygon.
        draw.polygon(self._screen, self._fillColour, polypositions)

    # getcenterposition returns the center position of the polygon.
    def getcenterposition(self):
        return self._centerPosition

    # getradiussize returns the radiussize attribute, which effectively describes how far the object can go from its center-position in the x and y directions.
    def getradiussize(self):
        return self._radiusSize

    # getfillcolour returns the colour of the polygon as a tuple of RGB values.
    def getfillcolour(self):
        return self._fillColour

    # getpolygonnumber returns the number of vertices in the polygon.
    def getpolygonnumber(self):
        return self._polygonNumber

    # getrectangle returns a Pygame Rect of the hitbox of the polygon (for use in Polygon button and network objects for determining if it has been clicked).
    def getrectangle(self):
        # As centerposition is from the center, radiussize must be subtracted to get the position of the top left hand corner. For the dimensions,
        # twice the radiussize is required in the x and y directions to create the hitbox required.
        return Rect(self._centerPosition.pixelx() - self._radiusSize.pixelx(),
                    self._centerPosition.pixely() - self._radiusSize.pixely(),
                    2 * self._radiusSize.pixelx(),
                    2 * self._radiusSize.pixely()
                    )

    # gettype returns the object type, in this case a 'Polygon'
    def gettype(self):
        return "Polygon"

    # setcenterposition sets the center-position of the polygon.
    def setcenterposition(self, centerposition):
        self._centerPosition = centerposition

    # setradiussize sets the radiusSize attribute to a new Position/WorldPosition object.
    def setradiussize(self, radiussize):
        self._radiusSize = radiussize

    # setfillcolour sets the colour of the polygon.
    def setfillcolour(self, fillcolour):
        self._fillColour = fillcolour

    # setpolygonnumber sets the number of vertices of the polygon.
    def setpolygonnumber(self, polygonnumber):
        self._polygonNumber = polygonnumber


# creates a rectangle, containing centered text within a coloured rectangle.
class TextRectangle:
    def __init__(self, screen, position, size, fillcolour, text, textsize, textcolour):
        # Storing a reference to the screen on which the object is to be displayed.
        self._screen = screen

        # Storing position (for text rectangles this is always the top left hand corner).
        self._position = position

        # Storing the dimensions of the rectangle.
        self._size = size

        # Initialisation of the rectangle object.
        self._rectangleObject = Rectangle(self._screen, position, size, fillcolour)

        # Initialisation of the text object at the center opf the rectangle.
        centerposition = Position(self._screen, position.relx() + size.relx() / 2, position.rely() + size.rely() / 2)
        self._textObject = Text(self._screen, text, centerposition, textsize, textcolour, "midcenter")

    # the paint method is standard for GUI objects and instructs pygame to display both the rectangle, and text (on top) when the display next updates.
    def paint(self):
        self._rectangleObject.paint()
        self._textObject.setposition(Position(self._screen, self._rectangleObject.getposition().relx() + self._rectangleObject.getsize().relx() / 2, self._rectangleObject.getposition().rely() + self._rectangleObject.getsize().rely() / 2))
        self._textObject.paint()

    # gettext returns the text of the text object.
    def gettext(self):
        return self._textObject.gettext()

    # getposition returns the center position of the object.
    def getposition(self):
        return self._textObject.getposition()

    # gettextsize returns the font/text size.
    def gettextsize(self):
        return self._textObject.gettextsize()

    # gettextcolour returns the colour of the text.
    def gettextcolour(self):
        return self._textObject.gettextcolour()

    # getsize returns the size of the rectangle.
    def getsize(self):
        return self._rectangleObject.getsize()

    # getrectangle returns the hitbox of the Text Rectangle (for use in buttons)
    def getrectangle(self):
        return self._rectangleObject.getrectangle()

    # getfillcolour returns the colour of the rectangle.
    def getfillcolour(self):
        return self._rectangleObject.getfillcolour()

    # gettype returns the type of object, in this case a 'TextRectangle'
    def gettype(self):
        return "TextRectangle"

    # setposition sets the position of the object.
    def setposition(self, position):
        # setting the rectangle component's position.
        self._position = position
        self._rectangleObject.setposition(position)

        # setting the centerposition of the text to the center of the rectangle.
        centerposition = self._rectangleObject.getrectangle().center
        self._textObject.setposition(Position(self._screen, centerposition[0], centerposition[1], "pixel"))

    # setsize sets the size of the rectangle.
    def setsize(self, size):
        self._rectangleObject.setsize(size)

    # setfillcolour sets the colour of the rectangle
    def setfillcolour(self, fillcolour):
        self._rectangleObject.setfillcolour(fillcolour)

    # settext sets the text of the text component.
    def settext(self, text):
        self._textObject.settext(text)

    # settextsize sets the font/text size of the text component.
    def settextsize(self, size):
        self._textObject.settextsize(size)

    # settextcolour sets the colour of the text.
    def settextcolour(self, textcolour):
        self._textObject.settextcolour(textcolour)


# The TextButton is simply a TextRectangle with an attached function reference to allow it to act as a button.
class TextButton(TextRectangle):
    def __init__(self, screen, function, position, size, fillcolour, text, textsize, textcolour):
        # Inheriting from the TextRectangle class.
        TextRectangle.__init__(self, screen, position, size, fillcolour, text, textsize, textcolour)

        # Holding the function reference.
        self.function = function

    # Overriding the gettype method so that it return the correct object type.
    def gettype(self):
        return "TextButton"


# The TextEntry class is used for user inputting nhumerical values and text, mainly for determining activation constants, synpase initilisation
# values, and the names of input and output neurons.
class TextEntry(TextRectangle):
    # class variables used to ensure that each object has a unique ID and only one is selected/being typed into at once.
    enabledObject = False
    objectID = 0

    def __init__(self, screen, position, size, fillcolours, inputtype, textsize, textcolour, name, defaulttext=""):

        # Inheriting from the TextRectangle class.
        TextRectangle.__init__(self, screen, position, size, fillcolours[1], defaulttext, textsize, textcolour)

        # Setting up the object ID.
        self._thisObjectID = TextEntry.objectID

        # Incrementing the objectID class variable so the next created TextEntry object has an ID one above this one.
        TextEntry.objectID += 1

        # Storing the fillcolours in a list so True, False can be used as indices for selecting colour.
        self._validFillColours = fillcolours

        # Storing the validity of the entry
        self._invalid = False

        # Storing the name, which is to be used to idenitify the object for user input retreival.
        self._name = name

        # Storing the type of input allowed, in the format shown below.
        # {"type" : [numeric, nosymbols, nonumeric, all], "limit" : maxchars, "range" : [min, max]"}
        self._inputType = inputtype

    # A standard method for GUI objects, setting the fillcolour to reflect the validity of the user's input, then displaying the object through an override.
    def paint(self):

        # Re-checking the validity of the user input, and setting the fillcolour accordingly.
        self._refreshvalidity()
        self._rectangleObject.setfillcolour(self._validFillColours[self._invalid])

        # Calling the base function for painting a Text Rectangle.
        TextRectangle.paint(self)

    # refreshvalidity re-checks the validity of the user input based on the input-type
    def _refreshvalidity(self):

        # storing the text as a local variable to avoid frequent calling of text component methods slowing the program.
        currenttext = self._textObject.gettext()

        # Checking if the input type is for numeric.
        if self._inputType["type"] == "numeric":
            if currenttext in ["", "+", "-"]:
                self._invalid = True
            elif float(currenttext) < self._inputType["range"][0] or float(currenttext) > self._inputType["range"][1]:
                self._invalid = True
            else:
                self._invalid = False

        # checking if it is a numericblank input (used for activation constants where it is not always required).
        elif self._inputType["type"] == "numericblank":
            if currenttext in ["+", "-"]:
                self._invalid = True
            else:
                self._invalid = False

        elif self._inputType["type"] == "allnoblank":
            if currenttext == "" or all([character == " " for character in currenttext]):
                self._invalid = True
            else:
                self._invalid = False

        # Checking if the text is numeric but not zero.
        elif self._inputType["type"] == "nonzeronumeric":
            if not currenttext.isnumeric():
                self._invalid = True
            elif float(currenttext) == 0:
                self._invalid = True
            elif float(currenttext) < self._inputType["range"][0] or float(currenttext) > self._inputType["range"][1]:
                self._invalid = True
            else:
                self._invalid = False

    # adding text input to the entry box
    def sendtext(self, inputstring):
        texttoadd = str()

        # If the text is too long then no more characters can be added.
        if len(self._textObject.gettext()) < self._inputType["limit"]:
            for character in inputstring:

                # If a backspace is sent, the last character is removed.
                if inputstring == "\x08":
                    self._textObject.settext(self._textObject.gettext()[:-1])

                # if a numeric input type, only numbers, +, - are can be added.
                elif self._inputType["type"] in ["numeric", "numericblank"]:
                    if character.isnumeric():
                        texttoadd += character
                    elif character in ["-", "+"]:
                        if self._textObject.gettext() == "":
                            texttoadd += character
                    elif character == ".":
                        if not "." in self.gettext():
                            texttoadd += character

                # If nosymbols allowed then only letters and numbers can be added.
                elif self._inputType["type"] == "nosymbols":
                    if character.isnumeric() or character.isalpha():
                        texttoadd += character

                # If not numeric, and no symbols then only letters can be added.
                elif self._inputType["type"] == "nonumeric":
                    if character.isalpha():
                        texttoadd += character

                # If all alowed then character added.
                elif self._inputType["type"] in ["all", "allnoblank"]:
                    texttoadd += character

            # setting the text of the Text component.
            self._textObject.settext(self._textObject.gettext() + texttoadd)
        elif inputstring == "\x08":
            self._textObject.settext(self._textObject.gettext()[:-1])

    # getenabled checks if the object is the single enabled one.
    def getenabled(self):
        if self._thisObjectID == TextEntry.enabledObject:
            return True
        else:
            return False

    # getname returns the name identifier of the object.
    def getname(self):
        return self._name

    # getvalue returns the validity of user input, and the text being held.
    def getvalue(self):
        return not self._invalid, self._textObject.gettext()

    # gettype returns the type of object, in this instance 'TextEntry'.
    def gettype(self):
        return "TextEntry"

    # enable sets the only enabled Text Entry object to this instance.
    def enable(self):
        TextEntry.enabledObject = self._thisObjectID

    # disable disables the Text Entry Box.
    def disable(self):
        if self._thisObjectID == TextEntry.enabledObject:
            TextEntry.enabledObject = None


# The SelectionBox class is used to create interactible selection boxes, where a user can click to edit and then choose from a list of options.
class SelectionBox:
    # The class variables allow the current selection box being used to be tracked, and ensure that only one is active at once.
    enabledObject = None
    objectID = 1

    def __init__(self, screen, position, textboxsize, openselectionimage, fillcolour, textsize, textcolour, selectionoptions, name, initial=None):

        # A reference to the screen is stored for later use in the paint method
        self.__screen = screen

        # Storing the position of the top left hand corner of the object.
        self.__position = position

        # Storing the size of the text box portion of the object.
        self.__textBoxSize = textboxsize

        # Storing the fill colour of the rectangle and the selection options (when enabled)
        self.__fillColour = fillcolour

        # Storing the font/text size.
        self.__textSize = textsize

        # Storing the text colour.
        self.__textColour = textcolour

        # Storing the relative file-path of the image (which enables the selection box).
        self.__openSelectionImageSource = openselectionimage

        # Storing the name (used for retreiving inputs).
        self.__name = name

        # Storing the other text options
        self.__selectionOptions = selectionoptions

        # If an argument for initial is passed, the initial selection is that, otherwise it is the first option of the option list.
        if initial:
            self.__currentSelection = initial
        else:
            self.__currentSelection = self.__selectionOptions[0]

        # Creating the object ID so that objects of this class can be tracked, and hence only one can be activated at once.
        self.__thisObjectID = SelectionBox.objectID
        SelectionBox.objectID += 1

        # Creating on a list to hold the selection box objects (of type TextRectangle).
        self.__selectionBoxes = list()

        # Creation of a holding attribute for the enabling button (an Image).
        self.__upArrowImage = None

        # Creation of a holding attribute for the main selection.
        self.__mainText = None

        # Refresh subroutine run to add objects to the mainText, upArrowImage and selectionBoxes attributes.
        self.__refresh()

    # paint is a standard method for instructing pygame to display the object when the display next updates
    def paint(self):

        # Refreshing the sizes and positions of the option and main Text Rectangles, and the enabling Button (image).
        self.__refresh()

        # Painting the enabling button.
        self.__upArrowImage.paint()

        # Painting the current selection.
        self.__mainText.paint()

        # Painting each of the options in the selectionbox (empty if the selection box is not enabled).
        for selectionbox in self.__selectionBoxes:
            selectionbox.paint()

    # refresh is used to refresh each of the GUI elements that make up the selection box, as between painting attributes may have been changed, or the window rescaled.
    def __refresh(self):

        # Creating the enabling button.
        self.__upArrowImage = Image(self.__screen, self.__openSelectionImageSource,
                                    Position(self.__screen, self.__position.pixelx() + self.__textBoxSize.pixelx(), self.__position.pixely(),
                                             "pixel"),
                                    Position(self.__screen, self.__textBoxSize.pixely(), self.__textBoxSize.pixely(), "pixel"))

        # Creating the current selection Text Rectangle.
        self.__mainText = TextRectangle(self.__screen, self.__position, self.__textBoxSize, self.__fillColour, self.__currentSelection,
                                        self.__textSize, self.__textColour)

        # If the selection box is currently enabled (meaning the user is selecting another option) the other options must be generated.
        if self.getenabled():

            # Resetting the selectionboxes.
            self.__selectionBoxes = []

            # Adding all selectionboxes but the current selection (does not need to be displayed twice)
            otheroptions = [option for option in self.__selectionOptions if option != self.__currentSelection]

            # Creating Text Rectangles for each of the other options.
            for index in range(0, len(otheroptions)):
                # index used to create the position of the option's Text Rectangle.
                self.__selectionBoxes.append(
                    TextRectangle(self.__screen, Position(self.__screen, self.__position.pixelx(),
                                                          self.__position.pixely() - self.__textBoxSize.pixely() * (index + 1), "pixel"),
                                  self.__textBoxSize, self.__fillColour, otheroptions[index], self.__textSize, self.__textColour))
        else:

            # If the selection box is not enabled, bno other options need to be displayed.
            self.__selectionBoxes = []

    # selectoption sets the current selection to a new option.
    def selectoption(self, selectionoption):
        self.__currentSelection = selectionoption

    # getenabled returns True if the user has enabled the selection box (options showing).
    def getenabled(self):
        if self.__thisObjectID == SelectionBox.enabledObject:
            return True
        else:
            return False

    # getposition returns the position of the top left hand corner of the object.
    def getposition(self):
        return self.__position

    # getsize returns the dimensions of the current selection TextRectangle (but not including the enabling button).
    def getsize(self):
        return self.__textBoxSize

    # getrectangle returns the enablebutton's rectangle (as this is used for the click to enable and disable the object).
    def getrectangle(self):
        return self.__upArrowImage.getrectangle()

    # getfillcolour returns the colour of the option's rectangles.
    def getfillcolour(self):
        return self.__fillColour

    # getselectimage returns the relative file-path of the image use for the 'up arrow' / enabling button.
    def getselectimage(self):
        return self.__openSelectionImageSource

    # getcurrentselection returns the current option selected by the user.
    def getcurrentselection(self):
        return self.__currentSelection

    # getselectionoptions returns the options currently available for selection by the user.
    def getselectionoptions(self):
        return self.__selectionOptions

    # gettextsize returns the text/font size.
    def gettextsize(self):
        return self.__textSize

    # gettextcolour returns the text colour.
    def gettextcolour(self):
        return self.__textColour

    # getname returns the name of the object, this is used as an identifier for retreiving user input from the GUI.
    def getname(self):
        return self.__name

    # getvalue returns the current selection and validity of it (always true for a selection box).
    def getvalue(self):
        return True, self.__currentSelection

    # gettype returns the type of object, in this case 'SelectionBox'.
    def gettype(self):
        return "SelectionBox"

    # selectiopnboxes retuirns the objects availble for the user to click when selecting, these are used with the mouseposition by GUI Stage to
    # determine if a new option needs to be selected.
    def getselectionboxes(self):
        self.__refresh()
        return self.__selectionBoxes

    # enable enables the object (displaying options on next paint) while simultaneously disabling any other selection boxes.
    def enable(self):
        SelectionBox.enabledObject = self.__thisObjectID

    # disable disables the selction box.
    def disable(self):
        if self.__thisObjectID == SelectionBox.enabledObject:
            SelectionBox.enabledObject = None

    # toggelenable flips the object form enabled to disabled or vice versa.
    def toggleenable(self):
        if self.getenabled():
            self.disable()
        else:
            self.enable()

    # setposition sets the position of the object.
    def setposition(self, position):
        self.__position = position

    # setsize sets the size of the object.
    def setsize(self, size):
        self.__textBoxSize = size

    # setfillcolour sets the colour of the rectangle of the options.
    def setfillcolour(self, fillcolour):
        self.__fillColour = fillcolour

    # setselectimage sets the image used for enabling the object.
    def setselectimage(self, imagesource):
        self.__openSelectionImageSource = imagesource

    # setselectionoptions sets the options available for the object.
    def setselectionoptions(self, selectionoptions):
        self.__selectionOptions = selectionoptions

        # If the current option is not available it is deselected.
        if not self.__currentSelection in selectionoptions:
            self.__currentSelection = self.__selectionOptions[0]

    # settextsize sets the font/text size.
    def settextsize(self, textsize):
        self.__textSize = textsize

    # settextcolour sets the text's colour.
    def settextcolour(self, textcolour):
        self.__textColour = textcolour


# Creates a clickable image based button by attaching a function reference to be run when the object is clicked.
class ImageButton(Image):
    def __init__(self, screen, function, imagesource, position, size):
        # Inheriting from the Image class.
        Image.__init__(self, screen, imagesource, position, size)

        # Storing the function reference.
        self.function = function

    # Overriding the Image class to return the correct object type.
    def gettype(self):
        return "ImageButton"


# Creates a clickable polygon by adding a function refrence which can be run when the object is clicked.
class PolygonButton(Polygon):
    def __init__(self, screen, function, centerposition, radiussize, colour, polygonnumber):
        # Inheriting from the polygon class.
        Polygon.__init__(self, screen, centerposition, radiussize, colour, polygonnumber)

        # Storing the function refrence.
        self.function = function

    # Overriding the polygon class to return the correct object type.
    def gettype(self):
        return "PolygonButton"


# Creates a clickable circle as a function reference can be attached to run when the object is clicked.
class CircleButton(Circle):
    def __init__(self, screen, function, centerposition, radisusize, fillcolour):
        # Inhertiting from the circle class.
        Circle.__init__(self, screen, centerposition, radisusize, fillcolour)

        # Stroing the function refrence.
        self.function = function

    # Overriding the circle class to return the correct object type.
    def gettype(self):
        return "CircleButton"


# The ToggleBox is a TextRectangle which can be flipped between two states by being clicked.
class ToggleBox(TextRectangle):
    def __init__(self, screen, position, size, validtext, validcolour, invalidtext, invalidcolour, textsize, textcolour, name, initial=True):
        # The text is stored as a list, as in python False = 0 and True = 1, the validity of the button can be used to select the correct text in this fashion.
        self._text = [invalidtext, validtext]

        # Just as with text, the validity of the toggle (if true or false selected) can be used to access the correct colour.
        self._fillColour = [invalidcolour, validcolour]

        # The validity determines which stage it is in (True or False)
        self._validity = initial

        # The name is used as a reference so that the value of a given togglebox can be accessed by searching for a given name.
        self._name = name

        # Inheriting from TextRectangle.
        TextRectangle.__init__(self, screen, position, size, self._fillColour[self._validity], self._text[self._validity], textsize, textcolour)

    # Toggle flips the validity, displaying the other state's colour and text.
    def toggle(self):
        # Toggling validity.
        self._validity = not self._validity

        # setting the and text to display the correct colour and text.
        self._rectangleObject = Rectangle(self._screen, self._position, self._rectangleObject.getsize(), self._fillColour[self._validity])
        self._textObject.settext(self._text[self._validity])

    # getvalue returns the validity of the user's selection (always True as user cannot select an incorrect option), and the user's choice (which state the toggle is in).
    def getvalue(self):
        return True, self._validity

    # gettype is overriden to return the correct object type.
    def gettype(self):
        return "ToggleBox"

    # getname returns the name of the particular object (used to identify it when retreiving inputs from the user).
    def getname(self):
        return self._name


# The gridcrosshair stores the cross hair objects denoting positions in the grid.
class GridCrossHair:
    def __init__(self, screen, position, size, fillcolour):
        # Storing a reference to the screen for use in displaying the object.
        self.__screen = screen

        # Storing the center position of the object.
        self.__position = position

        # Storing the x and y dimensions of the object.
        self.__size = size

        # Storing the fillcolour of the object.
        self.__fillColour = fillcolour

    # A standard method, it instructs pygame to display the two component rectangles when the screen next updates.
    def paint(self):
        vertical = Rect((self.__position.pixelx() - self.__size.pixelx() * 0.05, self.__position.pixely() - self.__size.pixely() * 0.5),
                        (self.__size.pixelx() * 0.1, self.__size.pixely()))
        horizontal = Rect((self.__position.pixelx() - self.__size.pixelx() * 0.5, self.__position.pixely() - self.__size.pixely() * 0.05),
                          (self.__size.pixelx(), self.__size.pixely() * 0.1))

        # 'drawing' the two rectangle components.
        draw.rect(self.__screen, self.__fillColour, vertical)
        draw.rect(self.__screen, self.__fillColour, horizontal)


# The background object contains the backdrop (by default a white background) and the grid cross hairs displayed on the screen.
class Background:
    def __init__(self, screen, camera, backingcolour, gridcolour):

        # Storing a reference to the screen (for use in displaying gui objects).
        self.__screen = screen

        # Storing the camera (for use in worldposition objects).
        self.__camera = camera

        # Storing the backing colour.
        self.__backingColour = backingcolour

        # Storing the colour of the grid cross-hair objects.
        self.__gridColour = gridcolour

        # Creating the backdrop to the grid.
        self.__backdrop = Rectangle(self.__screen, Position(self.__screen, 0, 0), Position(self.__screen, 1, 1), self.__backingColour)

    # A standard method for gui objects, it instructs python to display the object when the screen next updates.
    def paint(self):

        # Displaying the backdrop
        self.__backdrop.paint()

        # Storing camera position and size in order to get the range of grid positions currently viewable.
        cameraposition = self.__camera.getposition()
        camerasize = self.__camera.getsize()

        # A nested loop that goes through each position viewable to the user (and one outside as the user may partially be able to see a grid crosshair).
        for xcoor in range(int(cameraposition[0] - 1), int(cameraposition[0] + camerasize[0] + 2)):
            for ycoor in range(int(cameraposition[1] - 1), int(cameraposition[1] + camerasize[1] + 2)):
                # Painting a grid crosshair to a position being viewed by the user.
                GridCrossHair(self.__screen, WorldPosition(self.__screen, self.__camera, xcoor, ycoor),
                              WorldPosition(self.__screen, self.__camera, 0.1, 0.1, True), self.__gridColour).paint()

    # gettype returns the type of object, in this case 'Background'
    def gettype(self):
        return "Background"


# The Configuration class is used to enable the configuration json file to customsize the GUI by generating GUI objects that make use of the configuration.
class Configuration:
    def __init__(self, screen, camera):

        # Storing the screen (required for position objects).
        self.__screen = screen

        # Storing the camera (required for WorldPosition objects).
        self.__camera = camera

        # Creating the configuration attribute.
        with open('configuration.json') as configurationjson:
            self.__configuration = json.load(configurationjson)

    # getneuron returns the gui object for a neuron at its worldposition.
    def getneuron(self, worldposition, neurontype, lighteffect=False):

        # Creating WorldPosition.
        position = WorldPosition(self.__screen, self.__camera, worldposition[0], worldposition[1])

        # Creating Size argument.
        size = WorldPosition(self.__screen, self.__camera, 0.1, 0.1, True)

        # Getting shape from the configuration dictionary.
        shape = self.__configuration[neurontype]["shape"]

        # Checking if there is a light effect (e.g the colour when moving with the cursor).
        if lighteffect:
            colour = [min(val + 150, 255) for val in self.__configuration[neurontype]["colour"]]
        else:
            colour = self.__configuration[neurontype]["colour"]

        # Deciding gui object based on shape.
        if shape == "circle":
            return Circle(self.__screen, position, size, colour)
        elif shape == "triangle":
            return Polygon(self.__screen, position, size, colour, 3)
        elif shape == "square":
            return Polygon(self.__screen, position, size, colour, 4)
        elif shape == "pentagon":
            return Polygon(self.__screen, position, size, colour, 5)
        elif shape == "hexagon":
            return Polygon(self.__screen, position, size, colour, 6)
        elif shape == "septagon":
            return Polygon(self.__screen, position, size, colour, 7)
        elif shape == "octagon":
            return Polygon(self.__screen, position, size, colour, 8)

    # getsynapse returns the gui object for a synapse.
    def getsynapse(self, startposition, endposition, lighteffect=False):

        # Checking if there is a colour effect (e.g when drawing a synapse).
        if lighteffect:
            colour = [min(val + 150, 255) for val in self.__configuration["Synapse"]["colour"]]
        else:
            colour = self.__configuration["Synapse"]["colour"]

        # Returning the gui object.
        return Line(self.__screen, WorldPosition(self.__screen, self.__camera, startposition[0], startposition[1]),
                    WorldPosition(self.__screen, self.__camera, endposition[0], endposition[1]),
                    self.__configuration["Synapse"]["width"], colour)

    # geterrortext returns the textobject used for the error message text of a given index from the end of the error list.
    def geterrortext(self, index, text):
        return Text(self.__screen, text, Position(self.__screen, 120, 20 + index * self.__configuration["ErrorText"]["spacing"], "pixel", "right"),
                    self.__configuration["ErrorText"]["size"],
                    self.__configuration["ErrorText"]["colour"], "topright")

    # getfilename returns the text object to display the filename of a design.
    def getfilename(self, filename):
        return Text(self.__screen, filename, Position(self.__screen, 0.5, 0.05), self.__configuration["FileNameText"]["size"],
                    self.__configuration["FileNameText"]["colour"], "topcenter")

    # getbacking returns the GUI object for the background of the design area (the 'grid').
    def getbacking(self):
        return Background(self.__screen, self.__camera, self.__configuration["Background"]["fillcolour"],
                          self.__configuration["Background"]["coorcolour"])

    # gettoolbarshapes returns the shapes used on the toolbar for neurons, inputs and outputs, it returns buttons so that they can be placed on top
    # of toolbar buttons without preventing clicks for having an effect.
    def gettoolbarshape(self, neurontype, position, size, function):

        # Storing the shape of the given type of neuron.
        shape = self.__configuration[neurontype]["shape"]

        # Creating an imagebutton based on the shape provided, all are white as that is the colour used for icons on the toolbar.
        if shape == "circle":
            return CircleButton(self.__screen, function, position, size, (255,255,255))
        elif shape == "triangle":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 3)
        elif shape == "square":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 4)
        elif shape == "pentagon":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 5)
        elif shape == "hexagon":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 6)
        elif shape == "septagon":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 7)
        elif shape == "octagon":
            return PolygonButton(self.__screen, function, position, size, (255,255,255), 8)


# The Network Neuron class stores the attributes of a neuron object,a s well as its GUI object.
class NetworkNeuron:
    def __init__(self, configuration, worldposition, function, constant, synapses=[]):

        # Stroing the configuration object used to get the GUI object for the neuron.
        self._configuration = configuration

        # Storing thw position of the neuron in the grid.
        self._worldPosition = worldposition

        # Storing the activation of the neuron.
        self._function = function

        # Storing the activation constant of the neuron.
        self._constant = constant

        # Creating a holding attribute for the GUI object of the neuron.
        self._displayObject = None

        # Creating a list of the synapses, the list function is used so that iterables can be passed (e.g list comprehensions) without causing errors.
        self._synapses = list(synapses)

        # The displayObject attribute is filled with a GUI Object based on teh current configuration.
        self._refreshguiobject()

    # paint instructs Pygame to display the GUI object of the neuron when the display next updates.
    def paint(self):
        self._displayObject.paint()

    # refreshguiobject re-generates the GUI object of the neuron.
    def _refreshguiobject(self):
        self._displayObject = self._configuration.getneuron(self._worldPosition, "Neuron")

    # getposition returns the position in the grid of the neuron.
    def getposition(self):
        return self._worldPosition

    # getcollide checks if the neuron has been clicked.
    def getcollide(self, mouseposition):
        if self._displayObject.getrectangle().collidepoint(mouseposition):
            return True
        else:
            return False

    # getfunction returns the activation function used.
    def getfunction(self):
        return self._function

    # getconstant returns the constant for the activation function being used.
    def getconstant(self):
        return self._constant

    # getsynapses returns a list of the synapseIDs of the synapses connected to the neuron.
    def getsynapses(self):
        return list(self._synapses)

    # getinfo returns a dictionary of the values of the attributes of the object.
    def getinfo(self, object=True):
        if object:
            return {"Object": self, "Type": "Neuron", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant}
        else:
            return {"Type": "Neuron", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant}

    # gettype returns the type of object, in this case 'Neuron'.
    def gettype(self):
        return "Neuron"

    # setposition sets the position of the neuron in the grid, while updating the GUI object to reflect this.
    def setposition(self, position):
        self._worldPosition = position
        self._refreshguiobject()

    # setfunction sets the activation function used by the neuron.
    def setfunction(self, function):
        self._function = function

    # setconstant sets the activation function constant used by the neuron.
    def setconstant(self, constant):
        self._constant = constant

    # addsynapse adds a synapseID to the list of synapses connected to the neuron.
    def addsynapse(self, synapseid):
        self._synapses.append(synapseid)

    # removesynapse removes a given synapseID from the list of synapses connected to the neuron.
    def removesynapse(self, synapseid):
        self._synapses.remove(synapseid)


# Network Neuron holds the attributes, and GUI object for, an output neuron.
class NetworkInput(NetworkNeuron):
    def __init__(self, configuration, worldposition, function, constant, name, synapses=[]):
        NetworkNeuron.__init__(self, configuration, worldposition, function, constant, synapses)

        # Storing the name (the feature to be input at this neuron in the network)
        self._name = name

    # overriding refreshguiobject so that it displays an input neuron's GUI object.
    def _refreshguiobject(self):
        self._displayObject = self._configuration.getneuron(self._worldPosition, "Input")

    # getname returns the name of the feature to be input at this neuron.
    def getname(self):
        return self._name

    # getinfo returns the attributes of the input neuron as a dictionary.
    def getinfo(self, object=True):

        # If the user wants to object to be returned, it also returns a reference to itself.
        if object:
            return {"Object": self, "Type": "Input", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant,
                    "Name": self._name}
        else:
            return {"Type": "Input", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant, "Name": self._name}

    # gettype returns the type of object, in this case an 'Input'
    def gettype(self):
        return "Input"

    # setname sets the name of the feature to be input.
    def setname(self, name):
        self._name = name


# Network Output stores the required attributes of an output neuron, and the GUI object to display it.
class NetworkOutput(NetworkNeuron):
    def __init__(self, configuration, worldposition, function, constant, name, synapses=[]):
        NetworkNeuron.__init__(self, configuration, worldposition, function, constant, synapses)

        # SToring the name of the label that the network is trying to predict at this neuron.
        self._name = name

    # refreshguiobjects is overriden to set the display object to be one for output neurons.
    def _refreshguiobject(self):
        self._displayObject = self._configuration.getneuron(self._worldPosition, "Output")

    # getname returns the name of the label that is to be predicted at this output neuron.
    def getname(self):
        return self._name

    # getinfo return the attributes of the network as a dictionary.
    def getinfo(self, object=True):

        # If the user wants it to return a reference to itself, it can do so.
        if object:
            return {"Object": self, "Type": "Output", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant,
                    "Name": self._name}
        else:
            return {"Type": "Output", "Position": self._worldPosition, "Activation": self._function, "Constant": self._constant, "Name": self._name}

    # gettype is overriden to return the correct type, in this case 'Output'.
    def gettype(self):
        return "Output"

    # setname sets the name of the label being predicted.
    def setname(self, name):
        self._name = name


# The Network Synapse class holds all the attributes of a given synapse with its display object, as well as a unique identifier.
class NetworkSynapse:
    # class variable used to store the id of the next synapse.
    nextSynapseID = 0

    def __init__(self, configuration, startposition, endposition, interval, min, max, bias):

        # Storing the ID of the synapse
        self.__synapseID = NetworkSynapse.nextSynapseID

        # Incrementing the class variable to the ID of the next synapse to be generated.
        NetworkSynapse.nextSynapseID += 1

        # Storing the configuration object.
        self.__configuration = configuration

        # Storing the start position and end position of the neuron (distinguished as the start of a synapse cannot be connected to an Output, or
        # an Input to the end of one).
        self.__startPosition = startposition
        self.__endPosition = endposition

        # Ensuring the attributes are the correct way around.
        self.__refreshconnections()

        # Storing the interval of the random initialisation of the weight.
        self.__interval = interval

        # Storing the max and min initialisation value of the weight.
        self.__max = max
        self.__min = min

        # Storing if bias enabled, if so then it is initialised by the same configuration as the weights.
        self.__bias = bias

        # Creating a holder attribute for the display object.
        self.__displayObject = None

        # Setting up the display object based on the configuration (which is based on the json configuration file with the program).
        self.__refreshguiobject()

    # refreshguiobject generates a new synapse GUI object based on the configuration provided and the positions of the synapse's ends.
    def __refreshguiobject(self):
        self.__displayObject = self.__configuration.getsynapse(self.__startPosition, self.__endPosition)

    # refreshconnection ensures that the start position  is prior to the end position, and swaps them if this is not the case
    def __refreshconnections(self):

        # Checking the x-position of the start and end.
        if self.__startPosition[0] > self.__endPosition[0]:
            # Swapping the ends.
            holdervar = self.__startPosition[:]
            self.__startPosition = self.__endPosition[:]
            self.__endPosition = holdervar[:]

    # paint instructs pygame to display the GUI object associated with the synapse.
    def paint(self):
        self.__displayObject.paint()

    # getinterval returns the interval for the random initialisation of the neuron's weight.
    def getinterval(self):
        return self.__interval

    # getmin returns the minimum initialisation value for the weight.
    def getmin(self):
        return self.__min

    # getmax returns the maximum initialisation value for the weight.
    def getmax(self):
        return self.__max

    # getbias returns True if the bias is enabled.
    def getbias(self):
        return self.__bias

    # getinfo returns the attributes of the object, and a reference to itself if requested.
    def getinfo(self, object=True):
        if object:
            return {"Object": self, "Type": "Synapse", "Startposition": self.__startPosition, "Endposition": self.__endPosition,
                    "Interval": self.__interval, "Min": self.__min, "Max": self.__max,
                    "Bias": self.__bias}
        else:
            return {"Type": "Synapse", "Startposition": self.__startPosition, "Endposition": self.__endPosition, "Interval": self.__interval,
                    "Min": self.__min, "Max": self.__max,
                    "Bias": self.__bias}

    # getstartposition returns the start position of the synapse.
    def getstartposition(self):
        return self.__startPosition

    # getendposition returns the endposition of the synapse.
    def getendposition(self):
        return self.__endPosition

    # getcollide checks if a given mouse position has collided with the Line object representing the synapse.
    def getcollide(self, mouseposition):
        return self.__displayObject.getcollide(mouseposition)

    # gettype returns the type of object, in this case a 'Synapse'.
    def gettype(self):
        return "Synapse"

    # getsynapseid returns the unique ID associated with the synapse.
    def getsynapseid(self):
        return self.__synapseID

    # refreshattributes passes a new set of attributes to the synapse, this is used for editting synapses - rather tha determine which have changed
    # all are sent to reduce the potential for bugs, and an overuse of system rescources that would be associated with a determining which individual
    # attributes have changed and updating them individually.
    def refreshattributes(self, interval, min, max, bias):
        self.__interval = interval
        self.__min = min
        self.__max = max
        self.__bias = bias

    # setstartpositon sets the start position fo the synapse and updates the GUI object to reflect this.
    def setstartposition(self, startposition):
        self.__startPosition = startposition
        self.__refreshconnections()
        self.__refreshguiobject()

    # setendpositon sets the end position fo the synapse and updates the GUI object to reflect this.
    def setendposition(self, endposition):
        self.__endPosition = endposition
        self.__refreshconnections()
        self.__refreshguiobject()


# Data class contains all network objects, their positions in the grid, and a stack of all actions undertaken (so that actions can be undone).
# It is also responsible for saving the nunet files, and generating the python code to run the network.
class Data:
    def __init__(self, configuration):

        # Storing the configuration object (determines network object shapes, colours etc, allowing for program customisation by the user).
        self.__configuration = configuration

        # Storing the synapses and neurons in dedicated dictionaries.
        self.__synapses = dict()
        self.__neurons = dict()

        # Storing the instruction stack for use in the 'undo' method.
        self.__instructionStack = list()

        # Storing the error notifications list, to allow for errors to be displayed in chronological order.
        self.__errorNotifications = list()

        # This flag decides if the error notifications are shown to the user.
        self.__showErrorNotifications = False

        # Storing the name of the file.
        self.__fileName = ""

        # Storing the filename gui object.
        self.__fileNameObject = self.__configuration.getfilename(self.__fileName)

        # Storing the current location of the file (for use in 'save' method).
        self.__fileLocation = None

    # paint displays all of the network objects, as well as the error notifications if the user has opted to.
    def paint(self):

        # Displaying all synapse objects.
        for synapseobject in self.__synapses.values():
            synapseobject.paint()

        # Displaying all neuron objects.
        for neuronobject in self.__neurons.values():
            neuronobject.paint()

        self.__fileNameObject.settext(self.__fileName)
        self.__fileNameObject.paint()

        # Checking if the user wants the error notifications shown.
        if self.__showErrorNotifications:

            # Error index is used to determine how far down for the top of the screen the text is.
            errorindex = 0

            # Going through the reverse of the notifications list, to show most recent at the top.
            for notification in self.__errorNotifications[::-1]:
                # Using configuration to get the text type specified by the configuration json file.
                self.__configuration.geterrortext(errorindex, notification).paint()

                # Incrementing index for the next message.
                errorindex += 1

    # toggleerrornotifications flips the value for showning notifications.
    def toggleerrornotifications(self):
        self.__showErrorNotifications = not self.__showErrorNotifications

    # getneuroninfo returns the information relating to a given neuron, used for displaying attributes when editing a neuron.
    def getneuroninfo(self, position):
        return self.__neurons[tuple(position)].getinfo()

    # getsynapseinfo returns the information relating to a given synapse.
    def getsynapseinfo(self, synapseid):
        return self.__synapses[synapseid].getinfo()

    def getneurons(self):
        return self.__neurons

    def getsynapses(self):
        return self.__synapses

    # removeneuronobject removes a neuron, input or output at a given location.
    def removeneuronobject(self, position, record=True):

        # Creating a tuple from the position of the object (as dictionary keys must be immmutable).
        positionkey = tuple(position)

        # Storing the neuron object so that it may be recovered if the user undoes the action.
        neuronobject = self.__neurons[positionkey]

        # If 'record' the action is recorded, this is used so that the 'undo' method can undo actions without adding to the instruction stack.
        if record:
            self.__instructionStack.append({"type": "removeneuron", "status": "started"})

        # Remove connected synapses.
        for synapseid in self.__neurons[positionkey].getsynapses():
            self.removesynapseobject(synapseid)

        # Remove the reference to the neuron in the neurons dictionary, this also frees up its spot for other neurons.
        del self.__neurons[positionkey]

        # Record the action as complete.
        if record:
            self.__instructionStack.append({"type": "removeneuron", "position": position, "object": neuronobject, "status": "completed"})

    # removesynapseobject removes a given synapse from the design.
    def removesynapseobject(self, synapseid, record=True):

        # Getting a reference to the synapse object, so it can be stored in the instruction stack for potential recovery later.
        synapseobject = self.__synapses[synapseid]

        # removing the synapse reference from the neurons it was connected to.
        self.__neurons[tuple(synapseobject.getstartposition())].removesynapse(synapseid)
        self.__neurons[tuple(synapseobject.getendposition())].removesynapse(synapseid)

        # removing the synapse reference from the synapses dictionary.
        del self.__synapses[synapseid]

        # Recording the deletion of the synapse.
        if record:
            self.__instructionStack.append({"type": "removesynapse", "synapseid": synapseid, "object": synapseobject, "status": "completed"})

    # addneuron creates a new neuron object based on attributes entered by the user.
    def addneuron(self, position, activation, constant, record=True):

        # Creating a position tuple (tuples used instead of lists as dictionary keys must be immutable).
        keyposition = tuple(position)

        # Checking if the position is already filled.
        if keyposition in self.__neurons:

            # Adding an error notification if the position is filled.
            self.__errorNotifications.append("Network Position is already taken.")

        # if the user has not entered an activation constant when it is required, neuron not created.
        elif not constant[0] or (activation.lower() in ["linear", "elu", "leaky relu"] and constant[1] == ""):

            # Adding apprpriate error message.
            self.__errorNotifications.append("Constant value not valid")
        else:

            # Adding the new neuron object to the neurons dictionary.
            self.__neurons[keyposition] = NetworkNeuron(self.__configuration, position, activation, constant[1])

            # Recording the creation of the neuron so it can be undone if the user requests.
            if record:
                self.__instructionStack.append({"type": "addneuron", "position": position, "status": "completed"})

    # addinput is an equivalent to addneuron but for input neurons.
    def addinput(self, position, activation, constant, name, record=True):

        # Getting position tuple.
        keyposition = tuple(position)

        if keyposition in self.__neurons:
            self.__errorNotifications.append("Network Position is already taken.")
        elif not constant[0] or (activation.lower() in ["linear", "elu", "leaky relu"] and constant[1] == ""):
            self.__errorNotifications.append("Constant value not valid")
        else:

            # If the name text is not correct, or already in use,  rejecting the request to create an input
            if name[0] and name[1] not in [neuron.getname() for neuron in self.__neurons.values() if
                                           neuron.gettype() == "Input" or neuron.gettype() == "Output"] and name[1] != '':

                # Creating new input neuron object.
                self.__neurons[keyposition] = NetworkInput(self.__configuration, position, activation, constant[1], name[1])
                if record:
                    self.__instructionStack.append({"type": "addinput", "position": position, "status": "completed"})
            else:
                self.__errorNotifications.append("Neuron Name is already taken.")

    # addoutput is the equivalent of addneuron or addinput but for output neurons.
    def addoutput(self, position, activation, constant, name, record=True):

        # Getting the position tuple.
        keyposition = tuple(position)
        if keyposition in self.__neurons:
            self.__errorNotifications.append("Network Position is already taken.")

        # If the loss function requires a constant (Huber loss), a constant must be added.
        elif not constant[0] or (activation.lower() == "huber loss" and constant[1] == ""):
            self.__errorNotifications.append("Constant value not valid")
        else:

            # Checking name is valid, and is not already taken.
            if name[0] and name[1] not in [neuron.getname() for neuron in self.__neurons.values() if
                                           neuron.gettype() == "Input" or neuron.gettype() == "Output"] and name[1] != '':

                # Creating output neuron.
                self.__neurons[keyposition] = NetworkOutput(self.__configuration, position, activation, constant[1], name[1])

                # recording the output neuron's creation so it can potentially be undone.
                if record:
                    self.__instructionStack.append({"type": "addoutput", "position": position, "status": "completed"})
            else:
                self.__errorNotifications.append("Neuron name is already taken.")

    # addsynapse adds a new synapse object.
    def addsynapse(self, startposition, endposition, interval, min, max, bias, record=True):

        # If user has clicked starting from right to left, swap start and end positions.
        if startposition[0] > endposition[0]:
            holder = startposition[:]
            startposition = endposition[:]
            endposition = holder[:]

        # Checks that the same connection is not already made by a synapse.
        for synapseobject in self.__synapses.values():
            if (synapseobject.getstartposition() == startposition or synapseobject.getstartposition() == endposition) and (
                    synapseobject.getendposition() == startposition or synapseobject.getendposition() == endposition):
                # If position taken, error added to the notification list, and subroutine ends.
                self.__errorNotifications.append("Synapse already present in this location.")
                return

        # If synapse is not connecting two different neurons, reject.
        if endposition == startposition:
            self.__errorNotifications.append("Cannot connect neurons to themselves.")

        # If a synapse connects two neurons in the same layer.
        elif endposition[0] == startposition[0]:
            self.__errorNotifications.append("Cannot connect neurons in the same layer.")

        # If feeding into an input (not allowed), synapse rejected.
        elif self.__neurons[tuple(endposition)].gettype() == "Input":
            self.__errorNotifications.append("Cannot feed into an input.")

        # If feeding from an output (not allowed), synapse rejected.
        elif self.__neurons[tuple(startposition)].gettype() == "Output":
            self.__errorNotifications.append("Cannot feed from an output.")

        else:

            # Checking that the synapse connects two neurons together.
            if tuple(startposition) in self.__neurons and tuple(endposition) in self.__neurons:

                # Checking validity of values taken from input gui objects.
                if not interval[0]:
                    self.__errorNotifications.append("Entered synapse initialisation interval is invalid.")
                elif not min[0]:
                    self.__errorNotifications.append("Entered synapse initialisation minimum value is invalid.")
                elif not max[0]:
                    self.__errorNotifications.append("Entered synapse initialisation maximum value is invalid.")
                else:

                    # Checking that the minimum initialisation value is smaller than the maximum.
                    if float(min[1]) > float(max[1]):
                        self.__errorNotifications.append("Entered synapse initialisation maximum value must be larger than minimum.")
                    else:

                        # Creating the synapseobject.
                        synapseobject = NetworkSynapse(self.__configuration, startposition, endposition, float(interval[1]), float(min[1]),
                                                       float(max[1]), bias[1])

                        # Adding the synapseobject to the sysnapses dictionary.
                        self.__synapses[synapseobject.getsynapseid()] = synapseobject

                        # Adding a reference to the synapse to the connecting neurons.
                        self.__neurons[tuple(startposition)].addsynapse(synapseobject.getsynapseid())
                        self.__neurons[tuple(endposition)].addsynapse(synapseobject.getsynapseid())

                        # Recording the action in the instruction stack.
                        if record:
                            self.__instructionStack.append({"type": "addsynapse", "synapseid": synapseobject.getsynapseid(), "status": "completed"})

            else:
                self.__errorNotifications.append("Created Synapse does not connect two neurons.")

    # editneuron changes the attributes of a neuron.
    def editneuron(self, position, activation, constant, record=True):

        # recording the previous main attributes.
        prevactivation = self.__neurons[tuple(position)].getfunction()
        prevconstant = self.__neurons[tuple(position)].getconstant()

        # Checking that constant value is correct.
        if activation.lower() in ["linear", "elu", "leaky relu"] and constant[1] == "":

            # If constant value incorrect, adding appropriate notification.
            self.__errorNotifications.append("Must have an activation constant for an activation of that type.")
        else:

            # Getting the neuron being edited.
            neuronobject = self.__neurons[tuple(position)]

            # Updating neuron attributes.
            neuronobject.setfunction(activation)
            neuronobject.setconstant(constant[1])

            if record:
                # Recording the edit in the instruction stack.
                self.__instructionStack.append(
                    {"type": "neuronedit", "position": position, "prevactivation": prevactivation, "prevconstant": prevconstant,
                     "status": "completed"})

    # editinput is the input neuron equivalent of the editneuron method.
    def editinput(self, position, activation, constant, name, record=True):

        # recording the previous attributes.
        prevactivation = self.__neurons[tuple(position)].getfunction()
        prevconstant = self.__neurons[tuple(position)].getconstant()
        prevname = self.__neurons[tuple(position)].getname()

        # Checking if constant is valid (if required).
        if activation.lower() in ["linear", "elu", "leaky relu"] and constant[1] == "":
            self.__errorNotifications.append("Must have an activation constant for an activation of that type.")
        elif not (name[0] and name[1] not in [neuron.getname() for neuron in self.__neurons.values() if (neuron.gettype() == "Input" or neuron.gettype() == "Output") and neuron.getname() != prevname] and name[1] != ''):
            self.__errorNotifications.append("Invalid Name entered.")
        else:
            # Getting input object being edited.
            inputobject = self.__neurons[tuple(position)]

            # Updating input attributes.
            inputobject.setname(name[1])
            inputobject.setfunction(activation)
            inputobject.setconstant(constant[1])

            # recording the action in the instruction stack.
            if record:
                self.__instructionStack.append(
                    {"type": "inputedit", "position": position, "prevactivation": prevactivation, "prevconstant": prevconstant, "prevname": prevname,
                     "status": "completed"})

    # editoutput is the equivalent of editneuron or editinput but for output neurons.
    def editoutput(self, position, activation, constant, name, record=True):

        # storing previosu attributes.
        prevactivation = self.__neurons[tuple(position)].getfunction()
        prevconstant = self.__neurons[tuple(position)].getconstant()
        prevname = self.__neurons[tuple(position)].getname()

        # Checkng the constant provided if a constant is required.
        if activation.lower() in ["huber loss"] and constant[1] == "":
            self.__errorNotifications.append("Must have an activation constant for an activation of that type.")
        elif not (name[0] and name[1] not in [neuron.getname() for neuron in self.__neurons.values() if (neuron.gettype() == "Input" or neuron.gettype() == "Output") and neuron.getname != prevname] and name[1] != ''):
            self.__errorNotifications.append("Invalid Name entered.")
        else:
            # Getting output object being edited.
            outputobject = self.__neurons[tuple(position)]

            # Updating output attributes.
            outputobject.setname(name[1])
            outputobject.setfunction(activation)
            outputobject.setconstant(constant[1])

            # Recording the action in the instruction stack.
            if record:
                self.__instructionStack.append(
                    {"type": "outputedit", "position": position, "prevactivation": prevactivation, "prevconstant": prevconstant, "prevname": prevname,
                     "status": "completed"})

    # editsynapse changes the value of a given synapse object's parameters.
    def editsynapse(self, synapseid, interval, min, max, bias, record=True):

        # Checking if the inputs from the input gui objects are valid.
        if not interval[0]:
            self.__errorNotifications.append("Entered synapse initialisation interval is invalid.")
        elif not min[0]:
            self.__errorNotifications.append("Entered synapse initialisation minimum value is invalid.")
        elif not max[0]:
            self.__errorNotifications.append("Entered synapse initialisation maximum value is invalid.")
        else:

            # Checking that the minimum activation value is smaller than the maximum.
            if float(min[1]) > float(max[1]):
                self.__errorNotifications.append("Entered synapse initialisation maximum value must be larger than minimum.")
            else:

                # getting a reference to the synapse object.
                synapseobject = self.__synapses[synapseid]

                # Storing the previous values of the attributes of the synapse (for use by the 'uno' method).
                previnterval, prevmin, prevmax, prevbias = synapseobject.getinterval(), synapseobject.getmin(), synapseobject.getmax(), synapseobject.getbias()

                # Updating the synapse attribute values.
                synapseobject.refreshattributes(interval[1], min[1], max[1], bias[1])

                # Recording the action in the instruction stack.
                if record:
                    self.__instructionStack.append(
                        {"type": "synapseedit", "synapseid": synapseid, "previnterval": previnterval, "prevmin": prevmin, "prevmax": prevmax,
                         "prevbias": prevbias, "status": "completed"})

    # moveneuronobject moves the neuron object from one position to another (specified by the user), moving the synapses with it.
    def moveneuronobject(self, oldposition, newposition, record=True):

        # Create tuples to use as keys for accessing self.neurons and self.synapses dictionaries.
        newpositionkey = tuple(newposition)
        oldpositionkey = tuple(oldposition)

        # Check that new position is not taken, and old position had a neuron in it.
        if newpositionkey not in self.__neurons and oldpositionkey in self.__neurons:

            # Get neuron object being moved.
            neuronobject = self.__neurons[oldpositionkey]

            # Move neuron to new location.
            self.__neurons[newpositionkey] = neuronobject
            del self.__neurons[oldpositionkey]
            neuronobject.setposition(newposition)

            # Add action completed to the instruction stack.
            if record:
                self.__instructionStack.append({"type": "moveneuron", "status": "started"})

            # For each synapse update location.
            for synapse in neuronobject.getsynapses():
                synapseobject = self.__synapses[synapse]

                # setting the new start and end positions of the synapses connected to the neuron.
                if synapseobject.getstartposition() == oldposition:
                    synapseobject.setstartposition(newposition)
                else:
                    synapseobject.setendposition(newposition)

            # Checking that no inputs are being fed into, or outputs fed from (i.e if the user moved an output further left than a connected input).
            # If so, the synapse is removed.
            for synapse in neuronobject.getsynapses():
                synapseobject = self.__synapses[synapse]

                if self.__neurons[tuple(synapseobject.getendposition())].gettype() == "Input":
                    self.removesynapseobject(synapse, record)
                elif self.__neurons[tuple(synapseobject.getstartposition())].gettype() == "Output":
                    self.removesynapseobject(synapse, record)
                elif synapseobject.getstartposition()[0] == synapseobject.getendposition()[0]:
                    self.removesynapseobject(synapse, record)

            # recording the move's finish in the instruction stack.
            if record:
                self.__instructionStack.append(
                    {"type": "moveneuron", "initialposition": oldposition, "finalposition": newposition, "status": "complete"})
        else:
            self.__errorNotifications.append("Cannot move to a filled location.")

    # undo uses the instruction stack to undo the last instruction not undone.
    def undo(self):
        if len(self.__instructionStack) > 0:
            # Poping the instruction to do from the stack.
            self.__undoinstruction(self.__instructionStack.pop(-1))

    # undoinstruction undoes the an instruction based on its recorded dictionary from the instruction stack.
    def __undoinstruction(self, undoinstruction):
        # The methods for moving, adding, editing network objects are reused in this subroutine, but with record as False. This ensures that if undo
        # is clicked again, the undo itself isn't undone, but the next last action done.

        # If neuron object added, remove the object..
        if undoinstruction["type"] in ["addneuron", "addinput", "addoutput"]:
            self.removeneuronobject(undoinstruction["position"], False)

        # If synapse added, remove the synapse.
        elif undoinstruction["type"] == "addsynapse":
            self.removesynapseobject(undoinstruction["synapseid"], False)

        # If neuron has been moved.
        elif undoinstruction["type"] == "moveneuron":

            # Going through all actions done when the neuron was moved (e.g moving synapses back, restoring synapses).
            for instruction in self.__instructionStack[::-1]:

                # when it reaches the start of the action, all intermediary 'undos' have been completed
                if instruction["type"] == "moveneuron" and instruction["status"] == "started":
                    self.__instructionStack.pop(-1)
                    break
                else:

                    # Undo intermediary step.
                    self.__undoinstruction(self.__instructionStack.pop(-1))

            # Finally moving the neuron itself.
            self.moveneuronobject(undoinstruction["finalposition"], undoinstruction["initialposition"], False)

        # If action was to remove a neuron.
        elif undoinstruction["type"] == "removeneuron":

            # Restoring the neuron.
            self.__neurons[tuple(undoinstruction["position"])] = undoinstruction["object"]

            # Undoing intermediary actions, e.g the synapses remopved when the neuron was removed.
            for instruction in self.__instructionStack[::-1]:

                # If the first part of the neuron movement is found, no more steps to undo.
                if instruction["type"] == "removeneuron" and instruction["status"] == "started":
                    self.__instructionStack.pop(-1)
                    break
                else:
                    # Undo intermediary step.
                    self.__undoinstruction(self.__instructionStack.pop(-1))

        # If action was to remove a synapse.
        elif undoinstruction["type"] == "removesynapse":

            # restoring the synapse object.
            synapseobject = undoinstruction["object"]

            # Placing synapse back in the synapses dictionary.
            self.__synapses[synapseobject.getsynapseid()] = synapseobject

            # Adding the synapse reference back into the neurons that it connects.
            self.__neurons[tuple(synapseobject.getstartposition())].addsynapse(synapseobject.getsynapseid())
            self.__neurons[tuple(synapseobject.getendposition())].addsynapse(synapseobject.getsynapseid())

        # If action editted neuron.
        elif undoinstruction["type"] == "neuronedit":

            # Undo edit with stored previous attributes.
            self.editneuron(undoinstruction["position"], undoinstruction["prevactivation"], [True, undoinstruction["prevconstant"]], False)

        # If action was to edit and input neuron.
        elif undoinstruction["type"] == "inputedit":

            # Undoing edit using previous attributes.
            self.editinput(undoinstruction["position"], undoinstruction["prevactivation"], [True, undoinstruction["prevconstant"]],
                           [True, undoinstruction["prevname"]], False)

        # If action was to edit output neuron.
        elif undoinstruction["type"] == "outputedit":

            # Use saved attributes to undo the edit.
            self.editoutput(undoinstruction["position"], undoinstruction["prevactivation"], [True, undoinstruction["prevconstant"]],
                            [True, undoinstruction["prevname"]], False)

        # If action was to edit synapse.
        elif undoinstruction["type"] == "synapseedit":

            # Undo the synapse edit using stored previosu attributes.
            self.editsynapse(self, undoinstruction["synapseid"], [True, undoinstruction["previnterval"]], [True, undoinstruction["prevmin"]],
                             [True, undoinstruction["prevmax"]],
                             [True, undoinstruction["prevbias"]])

    # avedesignas saves the design for the first time, setting the location for future saves.
    def savedesignas(self, filelocation):

        # Creating the filename to be displayed in the interface.
        self.__fileName = filelocation.split(".")[0].split("/")[-1]

        # Saving the path of the filelocation for future saves.
        self.__fileLocation = filelocation

        # Calling savedesign to save the data.
        self.savedesign()

    # savedesign uses pickle to save the network design as a set of attributes in dictionaries.
    def savedesign(self):

        # Check that there is a location to save the design.
        if self.__fileLocation:

            # Generating dictionaries of the attributes of the network objects (as network objects contain gui objects (which cannot be 'pickled')
            # they cannot be saved directly).
            data = dict()
            data["neurons"] = [neuron.getinfo(False) for neuron in self.__neurons.values()]
            data["synapses"] = [synapse.getinfo(False) for synapse in self.__synapses.values()]

            # Attempting to save the binary file.
            try:
                dump(data, open(self.__fileLocation, "wb"))

            # If an error occurs, generating an appropriate error message.
            except PickleError:
                self.__errorNotifications.append("Unable to save design.")
        else:

            # If no file location stored, then file cannot be saved.
            self.__errorNotifications.append("Cannot save as file location not yet specified in 'save as'.")

    # loaddesign extracts a design from a '.nunet' file using pickle.
    def loaddesign(self, filelocation):

        # Use of exception handling as user may select a non .nunet file, or a corrupted file.
        try:

            # Storing data for manipulation.
            data = load(open(filelocation, "rb"))
            self.__fileLocation = filelocation
            self.__fileName = filelocation.split(".")[0].split("/")[-1]

            # Generating neurons from attributes stored in data.
            for neuron in data["neurons"]:
                if neuron["Type"] == "Neuron":
                    self.__neurons[tuple(neuron["Position"])] = NetworkNeuron(self.__configuration, neuron["Position"], neuron["Activation"],
                                                                              neuron["Constant"])
                elif neuron["Type"] == "Input":
                    self.__neurons[tuple(neuron["Position"])] = NetworkInput(self.__configuration, neuron["Position"], neuron["Activation"],
                                                                             neuron["Constant"], neuron["Name"])
                elif neuron["Type"] == "Output":
                    self.__neurons[tuple(neuron["Position"])] = NetworkOutput(self.__configuration, neuron["Position"], neuron["Activation"],
                                                                              neuron["Constant"], neuron["Name"])

            # Generating synapse objects from attributes stored in data.
            for synapse in data["synapses"]:
                synapseobject = NetworkSynapse(self.__configuration, synapse["Startposition"], synapse["Endposition"], synapse["Interval"],
                                               synapse["Min"], synapse["Max"], synapse["Bias"])
                self.__synapses[synapseobject.getsynapseid()] = synapseobject
                self.__neurons[tuple(synapse["Startposition"])].addsynapse(synapseobject.getsynapseid())
                self.__neurons[tuple(synapse["Endposition"])].addsynapse(synapseobject.getsynapseid())
        except:
            self.__errorNotifications.append("File could not be read, may be incorrect file type or corrupted.")

    # getdesignvalidity checks that all neurons are connected together, that inputs are not fed into, or outputs fed from.
    def __getdesignvalidity(self):

        # Iterating through all neurons.
        for neuronobject in self.__neurons.values():

            # If a neuron object, check that it is both fed to, and from by a connecting synapse.
            if neuronobject.gettype() == "Neuron":
                neuronvalid = [False, False]
                for synapseid in neuronobject.getsynapses():
                    if self.__synapses[synapseid].getstartposition() == neuronobject.getposition():
                        neuronvalid[0] = True
                    else:
                        neuronvalid[1] = True
                if neuronvalid[0] == False or neuronvalid[1] == False:
                    return False

            # If an input object, check that there are only synapses feeding from, and at least one of such synapses.
            elif neuronobject.gettype() == "Input":
                if neuronobject.getsynapses == []:
                    return False
                for synapseid in neuronobject.getsynapses():
                    if not self.__synapses[synapseid].getstartposition() == neuronobject.getposition():
                        return False

            # If an output object, check that there are only synapses feeding into it (at least 1).
            elif neuronobject.gettype() == "Output":
                if neuronobject.getsynapses == []:
                    return False
                for synapseid in neuronobject.getsynapses():
                    if not self.__synapses[synapseid].getendposition() == neuronobject.getposition():
                        return False
        return True

    # generate converts the network designed into working python code by setting up a new class for the described network, and importing the Nunet Library to run it.
    def generate(self, networkname, location, learningrate, library):

        # Checking that the design is valid from a connections standpoint.
        if self.__getdesignvalidity():

            # Creating a dictionary of all the layers in the design
            neuronstructure = dict()
            for neuronobject in self.__neurons.values():

                # Creating a dictionary for each neuron containing its layer, position in the layer.
                dataholder = {"layer": neuronobject.getposition()[0], "across": neuronobject.getposition()[1], "object": neuronobject}

                # If a new layer, KeyError occurs, so new layer is created.
                try:
                    neuronstructure[neuronobject.getposition()[0]].append(dataholder)
                except KeyError:
                    neuronstructure[neuronobject.getposition()[0]] = [dataholder]

            # Holding the text to be written in the python file, the name of the network is not the same as the filename, as different versions of a
            # network may be made from the same file.
            generatetext = "from NuNetLibrary import *\n\nclass " + networkname + "(Network):\n\tdef __init__(self):\n\t\tNetwork.__init__(self, ["

            # While there are still neuron to add, cycle through each layer, producing a representation of a list of Neuron, Input and Output objects.
            while bool(neuronstructure):

                # Selecting the first layer available.
                currentlayer = min(neuronstructure.keys())

                # Adding each object's initialisation code.
                generatetext += "["
                for neurondescription in sorted(neuronstructure[currentlayer], key=itemgetter('across')):

                    # Storing the object for reference to attributes.
                    neuronobject = neurondescription["object"]

                    # If a neuron, use the neuron initialisation.
                    if neuronobject.gettype() == "Neuron":
                        generatetext += "Neuron(" + str(neuronobject.getposition()) + ", '" + neuronobject.getfunction() + "'"
                        if neuronobject.getconstant().isnumeric():
                            generatetext += ", " + str(neuronobject.getconstant())
                        generatetext += "), "

                    # If an input neuron, use the input neuron initialisation.
                    elif neuronobject.gettype() == "Input":
                        generatetext += "Input('" + neuronobject.getname() + "', " + str(
                            neuronobject.getposition()) + ", '" + neuronobject.getfunction() + "'"
                        if neuronobject.getconstant().isnumeric():
                            generatetext += ", " + str(neuronobject.getconstant())
                        generatetext += "), "

                    # If an output neuron, use the output neuron initialisation.
                    elif neuronobject.gettype() == "Output":
                        generatetext += "Output('" + neuronobject.getname() + "', " + str(
                            neuronobject.getposition()) + ", '" + neuronobject.getfunction() + "'"
                        if neuronobject.getconstant().isnumeric():
                            generatetext += ", " + str(neuronobject.getconstant())
                        generatetext += "), "

                # Remove the comma and space at end, and close list.
                generatetext = generatetext[:-2] + "],"

                # Remove the layer that has been converted.
                del neuronstructure[currentlayer]

            # Remove the final comma, add the opening of the argument for synapses.
            generatetext = generatetext[:-1] + "], ["

            # Generate code for each synapse.
            for synapseobject in self.__synapses.values():
                generatetext += "Synapse(" + str(synapseobject.getstartposition()) + ", " + str(
                    synapseobject.getendposition()) + ", " + "{'interval' : " + str(
                    synapseobject.getinterval()) + ", 'min' : " + str(synapseobject.getmin()) + ", 'max' : " + str(
                    synapseobject.getmax()) + "}, " + str(synapseobject.getbias()) + "),"
            generatetext = generatetext[:-1] + "], " + str(learningrate) + ")"

            # Write the python file in the location specified.
            file = open(location, "x")
            file.write(generatetext)
            file.close()

            # If the user wants a copy of the library included (if folder does not already contain it), library created.
            if library:
                # Copy of NuNetLibrary is copied.
                library = open("NuNetLibrary.py", "r")
                newlocation = open("/".join(location.split('/')[:-1]) + '/NuNetLibrary.py', "x")
                newlocation.write(''.join(library.readlines()))
                newlocation.close()
                library.close()

        else:

            # If design is invalid, anj appropriate error message is shown.
            self.__errorNotifications.append("Design invalid, some neurons are not properly connected.")

    # gettype returns the object type, in this case 'Data'.
    def gettype(self):
        return "Data"


# The GUIStage class is an abstract class (meant to be inherited, overriden), which manages the displaying of GUI objects, user input and reaction (though a single event queue)
# and other miscelaneous effects. It is intended to be used as a template to build stages of a user interface through overriding.
class GUIStage:
    def __init__(self, window):

        # Holding window reference (window contains functions to move to other stages, so without it a multi-stage GUI is impossible).
        self._window = window

        # Storing the screen (the pygame surface where all gui objects are displayed).
        self._screen = window.getscreen()

        # A list containing all objects to be displayed on the screen, with a higher index meaning a layer closer to the screen.
        self._objectLayers = list()

        # Running the mainloop of the stage
        self._mainloop()

    # resetguiobjects is to be overriden so that the GUI objects the user wants in a certain stage are displayed by the mainloop.
    def _resetguiobjects(self):
        pass

    # Mainloop handles the drawing of gui objects, and user input through an event queue.
    def _mainloop(self):

        # The guiobjects are updated to match the current context.
        self._resetguiobjects()

        # previous mouse position is stored (for use in effects reliant on mouse motion).
        prevmouseposition = mouse.get_pos()

        # 'while True' used to create a perpetual loop.
        while True:

            # Dequeuing user input events from the event queue.
            for programevent in event.get():

                # If a mousemotion event, the mousemotion method is called.
                if programevent.type == MOUSEMOTION:
                    self._mousemotionevent(prevmouseposition, programevent.pos)
                    prevmouseposition = programevent.pos

                # If a click event, the clickevent method is called.
                elif programevent.type == MOUSEBUTTONDOWN:
                    self._clickevent(programevent)

                # If a key-press, the keydownevent method is called.
                elif programevent.type == KEYDOWN:
                    self._keydownevent(programevent)

                # If a key-release, the keyupevent method is called.
                elif programevent.type == KEYUP:
                    self._keyupevent(programevent)

                # If the window is resized in any way (manually or fullscreen) the resizevent method is called to re-scale gui objects.
                elif programevent.type == VIDEORESIZE:
                    self._resizeevent(programevent)

                # If the window is closed the quitevent method is called.
                elif programevent.type == QUIT:
                    self._quitevent()

                # The gui objects currently to be displayed are 'drawn' (pygame is instructed to display them when the display next updates).
                self._drawgui()

                # Any extra effects are displayed.
                self._extraeffects()

                # The display is updated to display the 'drawn' gui objects.
                display.update()

    # mousemotionevent is to be overriden in a GUIStage in order to display effects such as a cursor following neuron (when placing neurons).
    def _mousemotionevent(self, previousposition, currentposition):
        pass

    # clickevent goes through each of the layer of objects (starting with the top layer, going down), checking if the user has clicked them.
    def _clickevent(self, programevent):

        # If left-click pressed.
        if programevent.button == 1:

            # Iterating through objects from the top to bottom layers.
            for guiobject in self._objectLayers[::-1]:

                # If the gui object being checked is a button.
                if guiobject.gettype() in ["TextButton", "ImageButton", "PolygonButton", "CircleButton"]:

                    # If the gui object has been clicked, run its function and end the iteration (object clicked found).
                    if guiobject.getrectangle().collidepoint(programevent.pos):
                        guiobject.function()
                        break

                # If the gui object being checked is a text entry box.
                elif guiobject.gettype() == "TextEntry":

                    # If the text entry box has been clicked, enable it so that it receives keyboard input, if not disable it as the user has clicked off it.
                    # Then break iteration as the object being cli8cked has been found.
                    if guiobject.getrectangle().collidepoint(programevent.pos):
                        guiobject.enable()
                        break
                    else:
                        guiobject.disable()

                # If the gui object being checked is a selection box
                elif guiobject.gettype() == "SelectionBox":

                    # If the 'up-arrow' has been clicked, toggle the selection box and end iteration.
                    if guiobject.getrectangle().collidepoint(programevent.pos):
                        guiobject.toggleenable()
                        break

                    # If the selection box is enabled, check each of the options, if a collision has occured, set the selection to that box and
                    # disable the selection box. Then end iteration as the clicked object has been found.
                    if guiobject.getenabled():
                        for index in range(0, len(guiobject.getselectionboxes())):
                            option = guiobject.getselectionboxes()[index]
                            if option.getrectangle().collidepoint(programevent.pos):
                                guiobject.selectoption(option.gettext())
                                guiobject.disable()
                                break
                        guiobject.disable()
                        break

                # If the gui object being checked is a togglebox, toggle if clicked.
                elif guiobject.gettype() == "ToggleBox":
                    if guiobject.getrectangle().collidepoint(programevent.pos):
                        guiobject.toggle()

                # If the gui object being check is not a button, if clicked, end iteration as the user is clicking a non-button object.
                elif guiobject.gettype() in ["Circle", "Text", "Rectangle", "TextRectangle", "Image", "Polygon"]:
                    if guiobject.getrectangle().collidepoint(programevent.pos):
                        break

                # If the grid has been clicked (last layer and covers screen so no need to check mouse position), start the data updating subroutine
                # (so interaction context can be used to decide how the data changes (e.g neurons added, synapses removed, etc).
                elif guiobject.gettype() == "Data":
                    self._updatedata(programevent)

    # keydownevent checks for an enabled text entry box, and enters the text to it if it exists.
    def _keydownevent(self, programevent):
        for guiobject in self._objectLayers:
            if guiobject.gettype() == "TextEntry":
                if guiobject.getenabled():
                    guiobject.sendtext(programevent.unicode)

    # keyupevent is intended to be overriden by a user if a stage requires functionality for keypress timing.
    def _keyupevent(self, programevent):
        pass

    # quitevent quits the display and halts the program.
    def _quitevent(self):
        display.quit()
        quit()

    # resizeevent changes the display size, ensuring that all 'screen' objects reflect the new dimensions and hence object's Position and
    # WorldPosition type attributes scale.
    def _resizeevent(self, programevent):
        self._screen = display.set_mode(programevent.size, RESIZABLE)

    # drawgui instructs pygame to display each of the gui objects in the guiobjectlayers attribute, they are drawn in the order of the list (in layers)
    # so they can overlap.
    def _drawgui(self):
        for guiobject in self._objectLayers:
            guiobject.paint()

    # updatedata is intended to be overridden within the Editor Interface class to decide what action to take when the user clicks the grid.
    def _updatedata(self, programevent):
        pass

    # extraeffects is intended to be overriden within the editor Interface class for temporary neuron objects and synapses displayed on the cursor
    # when moving and placing network objects.
    def _extraeffects(self):
        pass


# contains gui, interaction state, holds inputs for between events
class State:
    def __init__(self):
        self.mode = "none"
        self.gui = "startstate"
        self.contextHolder = None


# The OpenScreen class runs the initial open screen stage of the user interface, with the program logo, and options to either open a design or start a new one.
class OpenScreen(GUIStage):
    def __init__(self, window):
        # Inheriting the GUIStage class.
        GUIStage.__init__(self, window)

    # resetguiobjects is overriden so that it sets objectLayers to the correct objects to display.
    def _resetguiobjects(self):
        self._objectLayers = [Rectangle(self._screen, Position(self._screen, 0, 0), Position(self._screen, 1, 1), (0, 225, 225), "topleft"),
                              TextButton(self._screen, self._navigatenewdesign, Position(self._screen, 0.3, 0.65), Position(self._screen, 0.4, 0.125),
                                         (255, 0, 0), "NEW DESIGN", 30, (255, 255, 255)),
                              TextButton(self._screen, self._openfile, Position(self._screen, 0.3, 0.8), Position(self._screen, 0.4, 0.125),
                                         (0, 255, 0), "OPEN FILE", 30, (255, 255, 255)),
                              Image(self._screen, "IconHighRes.png", Position(self._screen, 0.5, 0.1), Position(self._screen, 0.2, 0.2, "xaxis"),
                                    "topcenter")
                              ]

    # navigatenewdesign opens the EditorInterface with a new design (blank).
    def _navigatenewdesign(self):
        self._window.openEditor()

    # openfile opens a dialog box for thwe user to select a '.nunet' file, then opens the selected file in the editor interface.
    def _openfile(self):
        # Making temporary use of tkinter's file dialog box for my program.
        root = Tk()

        # Setting the main window to be invisible
        root.geometry("0x0")
        root.withdraw()
        root.lift()

        # opening the dialogbox window.
        dialogbox = filedialog.askopenfile(filetypes=(("NuNet Files", ".nunet"), ('all files', '*')))

        # Checking if the user has selected a file
        if dialogbox:
            # Opening the '.nunet' file in the editor.
            self._window.openEditor(dialogbox.name)

        # ending the tkinter instance.
        root.quit()


# The editorInterface class manages the user interfaction with the design, controlling the toolbar, as well as providing an interface between user
# input and the data object holding the design.
class EditorInterface(GUIStage):
    def __init__(self, window, filename):

        # setting up the filename attribute
        self._filename = filename

        # Setting up the 'State' object - a convenient method of holding user interaction and gui modes.
        self._editorState = State()

        # Inheriting from the GUIStage class.
        GUIStage.__init__(self, window)

    # loaddata creates the Data object to hold the design, and instructs it to load the file (if one is selected).
    def _loaddata(self):

        # Setting up the Data object.
        self._data = Data(self._configuration)

        # If filename given, load the file.
        if self._filename:
            self._data.loaddesign(self._filename)

    # mainloop is overriden to allow for extra initial setup of the required camera, configuration and data objects.
    def _mainloop(self):

        # Setting up the camera at the middle of the grid, with a zoom of 200 (200 pixels per world coordinate).
        self._camera = Camera(self._screen, [0, 0], 200)

        # The configuration is created, loading the 'configuration.json' file.
        self._configuration = Configuration(self._screen, self._camera)

        # The Data object is created, and if a filename has been given, that file is loaded.
        self._loaddata()

        # The base of the method is called.
        GUIStage._mainloop(self)

    # resetguiobjects is overriden to add the required gui objects to the display.
    def _resetguiobjects(self):

        # Adding required objects by order of layer, i.e Background first, then data (the neuron, synapse guiobjects), then the toolbar.
        self._objectLayers = [self._configuration.getbacking(),
                              self._data,
                              ImageButton(self._screen, self._backtomenu, "Toolbar/backtomenu.png", Position(self._screen, 20, 20, "pixel"),
                                          Position(self._screen, 90, 30, "pixel")),
                              ImageButton(self._screen, self._toolbarselect, "Toolbar/selecticon.png",
                                          Position(self._screen, 20, 140, "pixel", "bottom", "left"),
                                          Position(self._screen, 50, 30, "pixel")),
                              ImageButton(self._screen, self._toolbaraddition, "Toolbar/additionicon.png",
                                          Position(self._screen, 20, 110, "pixel", "bottom", "left"),
                                          Position(self._screen, 50, 30, "pixel")),
                              ImageButton(self._screen, self._toolbarremove, "Toolbar/removeicon.png",
                                          Position(self._screen, 20, 80, "pixel", "bottom", "left"),
                                          Position(self._screen, 50, 30, "pixel")),
                              ImageButton(self._screen, self._toolbarsave, "Toolbar/saveicon.png",
                                          Position(self._screen, 20, 50, "pixel", "bottom", "left"),
                                          Position(self._screen, 50, 30, "pixel")),
                              ImageButton(self._screen, self._errornotifications, "Toolbar/showerrors.png",
                                          Position(self._screen, 110, 20, "pixel", "right"), Position(self._screen, 90, 30, "pixel"))
                              ]

        # Determining the toolbar's extra gui objects based on the current gui state:
        if self._editorState.gui == "startstate":
            self._objectLayers += [Image(self._screen, "Toolbar/welcomemessage.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 270, 120, "pixel"))]
        elif self._editorState.gui == "selectmodeinitial":
            self._objectLayers += [
                ImageButton(self._screen, self._movemode, "Toolbar/selectmove.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                ImageButton(self._screen, self._editmode, "Toolbar/selectedit.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))]
        elif self._editorState.gui == "selectmodemoveprompt":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selectmoveprompt.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                ]
        elif self._editorState.gui == "selectmodeeditprompt":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selecteditprompt.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                ]
        elif self._editorState.gui == "selectmodeneuron":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selectactivation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"), Position(self._screen, 130, 30, "pixel"),
                             "Toolbar/selectuparrow.png",
                             (255, 255, 255), 20, (237, 125, 49),
                             ["BINARY STEP", "LINEAR", "eLU", "SOFTPLUS", "ReLU", "LEAKY ReLU", "SIGMOID", "TANH"], "NeuronActivation",
                             self._editorState.contextHolder["Activation"]),
                Image(self._screen, "Toolbar/selectactivationconstant.png", Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"), Position(self._screen, 160, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numericblank", "limit": 8},
                          20, (237, 125, 49), "NeuronConstant", self._editorState.contextHolder["Constant"]),
                ImageButton(self._screen, self._editsave, "Toolbar/selecteditsave.png", Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))
                ]
        elif self._editorState.gui == "selectmodeinput":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selectactivation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"), Position(self._screen, 130, 30, "pixel"),
                             "Toolbar/selectuparrow.png",
                             (255, 255, 255), 20, (237, 125, 49),
                             ["NONE", "BINARY STEP", "LINEAR", "eLU", "SOFTPLUS", "ReLU", "LEAKY ReLU", "SIGMOID", "TANH"], "InputActivation",
                             self._editorState.contextHolder["Activation"]),
                Image(self._screen, "Toolbar/selectname.png", Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"), Position(self._screen, 160, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "all", "limit": 8},
                          20, (237, 125, 49), "InputName", self._editorState.contextHolder["Name"]),
                Image(self._screen, "Toolbar/selectactivationconstant.png", Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 530, 110, "pixel", "bottom", "left"), Position(self._screen, 160, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numericblank", "limit": 8},
                          20, (237, 125, 49), "InputConstant", self._editorState.contextHolder["Constant"]),
                ImageButton(self._screen, self._editsave, "Toolbar/selecteditsave.png", Position(self._screen, 700, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))
                ]
        elif self._editorState.gui == "selectmodeoutput":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selectactivation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"), Position(self._screen, 130, 30, "pixel"),
                             "Toolbar/selectuparrow.png",
                             (255, 255, 255), 20, (237, 125, 49), ["MSE", "L1-LOSS", "LOG LOSS", "HINGE LOSS", "HUBER LOSS", "LOG-COSH"],
                             "OutputError",
                             self._editorState.contextHolder["Activation"]),
                Image(self._screen, "Toolbar/selectname.png", Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"), Position(self._screen, 160, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "all", "limit": 8},
                          20, (237, 125, 49), "OutputName", self._editorState.contextHolder["Name"]),
                Image(self._screen, "Toolbar/selectactivationconstant.png", Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 530, 110, "pixel", "bottom", "left"), Position(self._screen, 160, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numericblank", "limit": 8},
                          20, (237, 125, 49), "OutputConstant", self._editorState.contextHolder["Constant"]),
                ImageButton(self._screen, self._editsave, "Toolbar/selecteditsave.png", Position(self._screen, 700, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))
                ]
        elif self._editorState.gui == "selectmodesynapse":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarselect, "Toolbar/selectback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/selectweightinitialisation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 270, 120, "pixel")),
                Image(self._screen, "Toolbar/selectbias.png", Position(self._screen, 430, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 90, 120, "pixel")),
                TextEntry(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"), Position(self._screen, 70, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                          20, (133, 174, 72), "SynapseInterval", self._editorState.contextHolder["Interval"]),
                TextEntry(self._screen, Position(self._screen, 260, 110, "pixel", "bottom", "left"), Position(self._screen, 70, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                          20, (133, 174, 72), "SynapseMin", self._editorState.contextHolder["Min"]),
                TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"), Position(self._screen, 70, 30, "pixel"),
                          [(255, 255, 255), (255, 0, 0)],
                          {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                          20, (133, 174, 72), "SynapseMax", self._editorState.contextHolder["Max"]),
                ToggleBox(self._screen, Position(self._screen, 440, 110, "pixel", "bottom", "left"), Position(self._screen, 70, 30, "pixel"), "ON",
                          [0, 255, 0], "OFF", [255, 0, 0], 20,
                          [255, 255, 255], "SynapseBias", self._editorState.contextHolder["Bias"]),
                ImageButton(self._screen, self._editsave, "Toolbar/selecteditsave.png", Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))
                ]
        elif self._editorState.gui == "additionmodeinitial":
            self._objectLayers += [ImageButton(self._screen, self._additionneuronmode, "Toolbar/additionneuron.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   self._configuration.gettoolbarshape("Neuron", Position(self._screen, 115, 92, "pixel", "bottom", "left"),
                                                                       Position(self._screen, 27, 27, "pixel"), self._additionneuronmode),
                                   ImageButton(self._screen, self._additioninputmode, "Toolbar/additioninput.png",
                                               Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   self._configuration.gettoolbarshape("Input", Position(self._screen, 205, 92, "pixel", "bottom", "left"),
                                                                       Position(self._screen, 27, 27, "pixel"),self._additioninputmode),
                                   ImageButton(self._screen, self._additionoutputmode, "Toolbar/additionoutput.png",
                                               Position(self._screen, 250, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   self._configuration.gettoolbarshape("Output", Position(self._screen, 295, 92, "pixel", "bottom", "left"),
                                                                       Position(self._screen, 27, 27, "pixel"), self._additionoutputmode),
                                   ImageButton(self._screen, self._additionsynapsemode, "Toolbar/additionsynapse.png",
                                               Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel"))
                                   ]
        elif self._editorState.gui == "removemodeinitial":
            self._objectLayers += [
                ImageButton(self._screen, self._removemode, "Toolbar/removeremove.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))]
        elif self._editorState.gui == "removemodeprompt":
            self._objectLayers += [
                ImageButton(self._screen, self._toolbarremove, "Toolbar/removeback.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                Image(self._screen, "Toolbar/removeremoveprompt.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                      Position(self._screen, 180, 120, "pixel")),
                ]
        elif self._editorState.gui == "savemodeinitial":
            self._objectLayers += [
                ImageButton(self._screen, self._savedesignas, "Toolbar/savesaveas.png", Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                ImageButton(self._screen, self._savedesign, "Toolbar/savesave.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                ImageButton(self._screen, self._undoaction, "Toolbar/saveundo.png", Position(self._screen, 250, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel")),
                ImageButton(self._screen, self._generatecodemode, "Toolbar/savegenerate.png",
                            Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                            Position(self._screen, 90, 120, "pixel"))
                ]
        elif self._editorState.gui == "additionmodeneuron":
            self._objectLayers += [ImageButton(self._screen, self._toolbaraddition, "Toolbar/additionback.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   Image(self._screen, "Toolbar/additionactivation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"),
                                                Position(self._screen, 130, 30, "pixel"), "Toolbar/additionuparrow.png",
                                                (255, 255, 255), 20, (133, 174, 72),
                                                ["BINARY STEP", "LINEAR", "eLU", "SOFTPLUS", "ReLU", "LEAKY ReLU", "SIGMOID", "TANH"],
                                                "NeuronActivation"),
                                   Image(self._screen, "Toolbar/additionactivationconstant.png",
                                         Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numericblank", "limit": 8},
                                             20, (133, 174, 72), "NeuronConstant")
                                   ]
        elif self._editorState.gui == "additionmodeoutput":
            self._objectLayers += [ImageButton(self._screen, self._toolbaraddition, "Toolbar/additionback.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   Image(self._screen, "Toolbar/additionerror.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"),
                                                Position(self._screen, 130, 30, "pixel"), "Toolbar/additionuparrow.png",
                                                (255, 255, 255), 20, (133, 174, 72),
                                                ["MSE", "L1-LOSS", "LOG LOSS", "HINGE LOSS", "HUBER LOSS", "LOG-COSH"], "OutputError"),
                                   Image(self._screen, "Toolbar/additionname.png", Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "all", "limit": 8},
                                             20, (133, 174, 72), "OutputName"),
                                   Image(self._screen, "Toolbar/additionactivationconstant.png",
                                         Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 530, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numericblank", "limit": 8},
                                             20, (133, 174, 72), "OutputConstant")
                                   ]
        elif self._editorState.gui == "additionmodeinput":
            self._objectLayers += [ImageButton(self._screen, self._toolbaraddition, "Toolbar/additionback.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   Image(self._screen, "Toolbar/additionactivation.png", Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   SelectionBox(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"),
                                                Position(self._screen, 130, 30, "pixel"), "Toolbar/additionuparrow.png",
                                                (255, 255, 255), 20, (133, 174, 72),
                                                ["NONE", "BINARY STEP", "LINEAR", "eLU", "SOFTPLUS", "ReLU", "LEAKY ReLU", "SIGMOID", "TANH"],
                                                "InputActivation"),
                                   Image(self._screen, "Toolbar/additionname.png", Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "all", "limit": 8},
                                             20, (133, 174, 72), "InputName"),
                                   Image(self._screen, "Toolbar/additionactivationconstant.png",
                                         Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 530, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numericblank", "limit": 8},
                                             20, (133, 174, 72), "InputConstant")
                                   ]
        elif self._editorState.gui == "additionmodesynapse":
            self._objectLayers += [ImageButton(self._screen, self._toolbaraddition, "Toolbar/additionback.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   Image(self._screen, "Toolbar/additionweightinitialisation.png",
                                         Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 270, 120, "pixel")),
                                   Image(self._screen, "Toolbar/additionbias.png", Position(self._screen, 430, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 90, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 70, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                                             20, (133, 174, 72), "SynapseInterval"),
                                   TextEntry(self._screen, Position(self._screen, 260, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 70, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                                             20, (133, 174, 72), "SynapseMin"),
                                   TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 70, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                                             20, (133, 174, 72), "SynapseMax"),
                                   ToggleBox(self._screen, Position(self._screen, 440, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 70, 30, "pixel"), "ON", [0, 255, 0], "OFF", [255, 0, 0], 20,
                                             [255, 255, 255], "SynapseBias")
                                   ]
        elif self._editorState.gui == "savemodegenerate":
            self._objectLayers += [ImageButton(self._screen, self._toolbarsave, "Toolbar/savegenerateback.png",
                                               Position(self._screen, 70, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel")),
                                   Image(self._screen, "Toolbar/savegeneratenetworkname.png",
                                         Position(self._screen, 160, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 170, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "allnoblank", "limit": 8},
                                             20, (1, 177, 241), "NetworkName"),
                                   Image(self._screen, "Toolbar/savegenerategeneratelearningrate.png",
                                         Position(self._screen, 340, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   TextEntry(self._screen, Position(self._screen, 350, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), [(255, 255, 255), (255, 0, 0)],
                                             {"type": "numeric", "limit": 6, "range": [-1000, 1000]},
                                             20, (1, 177, 241), "LearningRate"),
                                   Image(self._screen, "Toolbar/savegeneratelibraryfile.png",
                                         Position(self._screen, 520, 140, "pixel", "bottom", "left"),
                                         Position(self._screen, 180, 120, "pixel")),
                                   ToggleBox(self._screen, Position(self._screen, 530, 110, "pixel", "bottom", "left"),
                                             Position(self._screen, 160, 30, "pixel"), "INCLUDED", [0, 255, 0], "NOT INCLUDED",
                                             [255, 0, 0], 20,
                                             [255, 255, 255], "IncludeLibrary"),
                                   ImageButton(self._screen, self._generatedesign, "Toolbar/savegenerate.png",
                                               Position(self._screen, 700, 140, "pixel", "bottom", "left"),
                                               Position(self._screen, 90, 120, "pixel"))
                                   ]

    # mousemotionevent is overriden from GUIStage and is used to determine how far the user has translated across the editor grid, changing the camera object to represent this.
    def _mousemotionevent(self, previousposition, currentposition):
        if mouse.get_pressed()[2]:
            self._camera.move(self._camera.pixeltoworld((previousposition[0] - currentposition[0], previousposition[1] - currentposition[1]), True))

    # extraeffects is overriden from GUIStage and is used to display the 'temporary' icons for neurons, inputs, outputs and synapses when they are moved, or created.
    def _extraeffects(self):

        # Getting the current mouse position (this is the only user input not dependent on the event queue).
        mouseposition = mouse.get_pos()

        # If in the final stage of adding the synapse, draw a Line (representing a synapse) from the selected start position, to the mouse.
        if self._editorState.mode == "additionsynapsefinal":
            self._configuration.getsynapse(self._editorState.contextHolder["position"], self._camera.pixeltoworld(mouseposition), True).paint()

        # If in the final stage of moving a nouron object, display the object at the mouse's position.
        elif self._editorState.mode == "movefinal":
            self._configuration.getneuron(self._camera.pixeltoworld(mouseposition), self._editorState.contextHolder["type"], True).paint()

        # If adding a neuron, display a neuron at the mouse's position.
        elif self._editorState.mode == "additionneuron":
            self._configuration.getneuron(self._camera.pixeltoworld(mouseposition), "Neuron", True).paint()

        # If adding a neuron, display an input at the mouse's position.
        elif self._editorState.mode == "additioninput":
            self._configuration.getneuron(self._camera.pixeltoworld(mouseposition), "Input", True).paint()

        # If adding a neuron, display an output at the mouse's position.
        elif self._editorState.mode == "additionoutput":
            self._configuration.getneuron(self._camera.pixeltoworld(mouseposition), "Output", True).paint()

    # overriden from GUIStage, it runs the base method, but also checks for scrolling (which is used for zooming in and out of the grid).
    def _clickevent(self, programevent):

        # Calling base method.
        GUIStage._clickevent(self, programevent)

        # If scrolling out, decrease the zoom (network objects appear smaller) by changing the camera object's zoom attribute.
        if programevent.button == 4:
            self._camera.decreasezoom(programevent.pos)

        # If scrolling in, increase the zoom (network objects appear larger) by changing the camera object's zoom attribute.
        elif programevent.button == 5:
            self._camera.increasezoom(programevent.pos)

    # updatedata is overriden from GUIStage, it is run when the grid is clicked, and checks if the user has clicked a network object, or the grid itself.
    def _updatedata(self, programevent):

        # checks through the network objects in data, checking if they have been clicked.
        for designobject in chain(self._data.getneurons().values(), self._data.getsynapses().values(), [None]):

            # If at the end of the list, no objects have been clicked.
            if designobject is None:
                self._nothingclicked(programevent)
                break

            # If the object has been clicked, determine type and run relevant method, breaking the loop (as to not search unecessarily).
            if designobject.getcollide(programevent.pos):

                # If object is a Neuron, Input or Output.
                if designobject.gettype() in ["Neuron", "Input", "Output"]:
                    self._neuronobjectclicked(designobject)
                    break

                # If object is a synapse.
                elif designobject.gettype() == "Synapse":
                    self._synapseclicked(designobject)
                    break

    # nothingclicked is used to determine the action taken on data when the grid is clicked,
    def _nothingclicked(self, programevent):

        # Converting the position of the mouse into worldcoordinates.
        clickworldpos = self._camera.pixeltoworld(programevent.pos)

        # Rounding to find the nearest cross in the grid.
        clickworldpos = [int(round(clickworldpos[0], 0)), int(round(clickworldpos[1], 0))]

        # If mode is to add a neuron on lick.
        if self._editorState.mode == "additionneuron":

            # Add a neuron of the attributes entered, at the closest crosshair to the click.
            self._data.addneuron(clickworldpos, self._getinputobject("NeuronActivation").getvalue()[1],
                                 self._getinputobject("NeuronConstant").getvalue())

        # If mode is to add an input on click.
        elif self._editorState.mode == "additioninput":

            # Add an input of the attributes entered, at the closest crosshair to the click.
            self._data.addinput(clickworldpos, self._getinputobject("InputActivation").getvalue()[1],
                                self._getinputobject("InputConstant").getvalue(), self._getinputobject("InputName").getvalue())

            # Set the name text entry box to empty (as name has been taken).
            self._getinputobject("InputName").settext("")

        # If mode is to add an output on click.
        elif self._editorState.mode == "additionoutput":

            # Add an output of the attributes entered, at the closest crosshair to the click.
            self._data.addoutput(clickworldpos, self._getinputobject("OutputError").getvalue()[1], self._getinputobject("OutputConstant").getvalue(),
                                 self._getinputobject("OutputName").getvalue())

            # Set the name text entry box to empty, as the name has been taken.
            self._getinputobject("OutputName").settext("")

        # If neuron being moved, the click to to place the neuron being moved.
        elif self._editorState.mode == "movefinal":

            # Move the neuron from the initial position to the position clicked.
            self._data.moveneuronobject(self._editorState.contextHolder["position"], clickworldpos)

            # Set the mode such that a new neuron must be clicked to restart the moving process.
            self._editorState.mode = "moveinitial"

        # If a synapse is being placed, and nothing is clicked, the synapse attempt is abandoned.
        elif self._editorState.mode == "additionsynapsefinal":
            self._editorState.mode = "additionsynapseinitial"

    # neuronobjectclicked deals with an event where a neuron object is clicked.
    def _neuronobjectclicked(self, neuronobject):

        # If in move mode, and no neuron yet selected.
        if self._editorState.mode == "moveinitial":

            # Store the neuron clicked in the state context holder.
            self._editorState.contextHolder = {"action": "moveneuron", "position": neuronobject.getposition(), "type": neuronobject.gettype()}

            # Move to the final stage of neuron moving (so next click places the neuron).
            self._editorState.mode = "movefinal"

        # If in edit mode (attributes need to be displayed).
        elif self._editorState.mode == "edit":

            # Store the attributes of the neuron in the context holder.
            self._editorState.contextHolder = self._data.getneuroninfo(neuronobject.getposition())

            # Update the gui to the correct toolobar state, depending on the neuronobject type.
            if neuronobject.gettype() == "Neuron":
                self._editorState.gui = "selectmodeneuron"

            elif neuronobject.gettype() == "Input":
                self._editorState.gui = "selectmodeinput"

            elif neuronobject.gettype() == "Output":
                self._editorState.gui = "selectmodeoutput"

            # Update the gui to reflect the change in toolbar.
            self._resetguiobjects()

        # If in remove state (clicking an object removes it).
        elif self._editorState.mode == "remove":

            # Remove the object.
            self._data.removeneuronobject(neuronobject.getposition())

        # If adding a synapse (clicking the first neuron it is connected to).
        elif self._editorState.mode == "additionsynapseinitial":

            # Store position clicked.
            self._editorState.contextHolder = {"action": "additionsynapse", "position": neuronobject.getposition()}

            # Move onto next stage of synapse creation (clicking the other neuron it connects to).
            self._editorState.mode = "additionsynapsefinal"

        # If in the final stage of synapse creation, create the synapse.
        elif self._editorState.mode == "additionsynapsefinal":

            # Creating the synapse form the attributes entered by the user.
            self._data.addsynapse(self._editorState.contextHolder["position"], neuronobject.getposition(),
                                  self._getinputobject("SynapseInterval").getvalue(),
                                  self._getinputobject("SynapseMin").getvalue(),
                                  self._getinputobject("SynapseMax").getvalue(), self._getinputobject("SynapseBias").getvalue())

            # Returning to the initial stage so another synapse can be drawn.
            self._editorState.mode = "additionsynapseinitial"

    # synapseclicked manages the results of a synapse object being clicked.
    def _synapseclicked(self, synapseobject):

        # If editor state is edit.
        if self._editorState.mode == "edit":

            # Store attributes of the synapse in the context holder.
            self._editorState.contextHolder = self._data.getsynapseinfo(synapseobject.getsynapseid())

            # Changes gui state to display the neuron attributes on the toolbar.
            self._editorState.gui = "selectmodesynapse"

            # Updating the gui to relect the change of state.
            self._resetguiobjects()

        # If in remove mode.
        elif self._editorState.mode == "remove":

            # Remove the synapse clicked.
            self._data.removesynapseobject(synapseobject.getsynapseid())

    # getinputobject is a utility method which searches through the gui objects, finding the one with the name attribute provided as an argument.
    # This is mainly used for finding the objects taking input from the user, so that their value can be taken.
    def _getinputobject(self, name):

        # Searching through all gui objects.
        for guiobject in self._objectLayers:

            # If a type of gui object that has a name.
            if guiobject.gettype() in ["SelectionBox", "TextEntry", "ToggleBox"]:

                # If guiobject name matchs name being searched for, return a reference to the object.
                if guiobject.getname() == name:
                    return guiobject

    # editsave saves the chyanges made to an object attribute in the edit mode.
    def _editsave(self):

        # getting the object being edited.
        networkobject = self._editorState.contextHolder["Object"]

        # If editing a neuron, update neuron attributes.
        if self._editorState.gui == "selectmodeneuron":
            self._data.editneuron(networkobject.getposition(), self._getinputobject("NeuronActivation").getvalue()[1],
                                  self._getinputobject("NeuronConstant").getvalue())

        # If updating an input, update attributes.
        elif self._editorState.gui == "selectmodeinput":
            self._data.editinput(networkobject.getposition(), self._getinputobject("InputActivation").getvalue()[1],
                                 self._getinputobject("InputConstant").getvalue(),
                                 self._getinputobject("InputName").getvalue())

        # If updating an output, update attributes.
        elif self._editorState.gui == "selectmodeoutput":
            self._data.editoutput(networkobject.getposition(), self._getinputobject("OutputError").getvalue()[1],
                                  self._getinputobject("OutputConstant").getvalue(),
                                  self._getinputobject("OutputName").getvalue())

        # If updating a synapse, update attributes.
        elif self._editorState.gui == "selectmodesynapse":
            self._data.editsynapse(self._getinputobject("SynapseInterval").getvalue(), self._getinputobject("SynapseMin").getvalue(),
                                   self._getinputobject("SynapseMax").getvalue(),
                                   self._getinputobject("SynapseBias").getvalue())

        # Return the toolbar to prompting the user to select an object.
        self._editorState.gui = "selectmodeeditprompt"

        # Update the gui objects list to reflect the change of state.
        self._resetguiobjects()

    # errornotifications shows error notifications if hidden, or vice versa.
    def _errornotifications(self):
        self._data.toggleerrornotifications()

    # toolbar select changes the gui mode to the initial select mode.
    def _toolbarselect(self):

        # Changing gui state.
        self._editorState.gui = "selectmodeinitial"

        # Setting the editor mode to None (so user left-clicks do nothing).
        self._editorState.mode = None

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # toolbaraddition returns the user to the initial addition toolbar (so they can select neuron, input, output or synapse).
    def _toolbaraddition(self):

        # Changing gui state.
        self._editorState.gui = "additionmodeinitial"

        # Setting the editor mode to None (so user left-clicks do nothing).
        self._editorState.mode = None

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # toolbarremove sets the toolbar to the initial remove option.
    def _toolbarremove(self):

        # Changing gui state.
        self._editorState.gui = "removemodeinitial"

        # Setting the editor mode to None (so user left-clicks do nothing).
        self._editorState.mode = None

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # toolbarsave changes the toolbar to show the save options ('Save As', 'Save', 'Undo', 'Generate')
    def _toolbarsave(self):

        # Changing gui state.
        self._editorState.gui = "savemodeinitial"

        # Setting the editor mode to None (so user left-clicks do nothing).
        self._editorState.mode = None

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # editmode sets the toolbar to prompt the user to click an object to edit it.
    def _editmode(self):

        # Changing gui state.
        self._editorState.gui = "selectmodeeditprompt"

        # Changing the itneraction state so the user can click to select network objects.
        self._editorState.mode = "edit"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # movemode sets the toolbar state to prompt the user to click network neuron type objects to move them.
    def _movemode(self):

        # Changing gui state.
        self._editorState.gui = "selectmodemoveprompt"

        # Changing the interaction state so that any neuron clicked can then be moved.
        self._editorState.mode = "moveinitial"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # removemode sets the toolbar to prompt the user to click objects to remove them.
    def _removemode(self):

        # Changing gui state.
        self._editorState.gui = "removemodeprompt"

        # Changing the interaction state so that clicking a network object removes it.
        self._editorState.mode = "remove"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # additionneuronmode changes the editor state so that options for creating a neuron are shown.
    def _additionneuronmode(self):

        # Changing gui state.
        self._editorState.gui = "additionmodeneuron"

        # Changing the interaction state so clicking places the neuron of attributes entered by the user.
        self._editorState.mode = "additionneuron"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # additionmodeinput changes the editor state to adding inputs where the grid is clicked.
    def _additioninputmode(self):

        # Changing gui state.
        self._editorState.gui = "additionmodeinput"

        # changing the interaction mode to create a neuron of attributes entered where the user clicks.
        self._editorState.mode = "additioninput"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # additionoutputmode sets the editor to add an output on user click.
    def _additionoutputmode(self):

        # Changing gui state.
        self._editorState.gui = "additionmodeoutput"

        # Changing the interaction mode to add an output where the user clicks, of the attributes the user has entered.
        self._editorState.mode = "additionoutput"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # additionmodesynapse sets the editor to start creating a synapse.
    def _additionsynapsemode(self):

        # Changing gui state.
        self._editorState.gui = "additionmodesynapse"

        # Changing the interaction mode so that where the user clicks (if a neuron type object is present) a synapse is started.
        self._editorState.mode = "additionsynapseinitial"

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # generatecodemode sets the gui to the generate submenu, where the user can decide how to generate their python file of the network designed.
    def _generatecodemode(self):

        # Changing gui state.
        self._editorState.gui = "savemodegenerate"

        # setting editor interaction mode to None so clicking the grid has no effect.
        self._editorState.mode = None

        # Updating the gui object list to reflect the change of state.
        self._resetguiobjects()

    # savdesignas opens a tkinter window where the user can decide the file name, and location.
    def _savedesignas(self):

        # Creating the tkinter window
        root = Tk()

        # Hiding the main tkinter window.
        root.geometry("0x0")
        root.withdraw()
        root.lift()

        # Creating a file save as dialog box.
        dialogbox = filedialog.asksaveasfilename(defaultextension=".nunet", title="Save Neural Network Design")

        # If user selects a valid location.
        if dialogbox:
            # Instruct the Data object to save at the selected location.
            self._data.savedesignas(dialogbox)

        # Close the tkinter window.
        root.quit()

    # savedesign instructs data to save the design at the location previously decided in the 'Save As' option.
    def _savedesign(self):
        self._data.savedesign()

    # undoaction instructs the data object to undo the last action made on the data.
    def _undoaction(self):
        self._data.undo()

    # generatedesign takes the user's options for code generation, and passes them to the data object, as well as creating a tkinter file
    # save as dialog to decide file location.
    def _generatedesign(self):

        # Storing the entered attributes for name, learning rate, and if the user wants the library file to be included.
        networkname = self._getinputobject("NetworkName").getvalue()
        learningrate = self._getinputobject("LearningRate").getvalue()
        includelibrary = self._getinputobject("IncludeLibrary").getvalue()

        # If the name and learning rate are valid.
        if networkname[0] and learningrate[0]:

            # Create a tkinter window for the file dialog.
            root = Tk()

            # Hide the tkinter window.
            root.geometry("0x0")
            root.withdraw()
            root.lift()

            # Create a file dialog box.
            dialogbox = filedialog.asksaveasfilename(defaultextension=".py", title="Choose Code Location")

            # If user selects a valid location.
            if dialogbox:
                # Instruct data to generate the object (note that spaces are replaced with underscores in the name to adhere to python syntax).
                self._data.generate(networkname[1].replace(' ', '_'), dialogbox, learningrate[1], includelibrary[1])

            # Close tkinter window.
            root.quit()

    # backtomenu is used when the user clicks the menu button, it saves the design, and returns them to the open screen.
    def _backtomenu(self):
        self._data.savedesign()
        self._window.openScreen()


# Window class manages the stages of the gui, and creates the pygame display that the program uses.
class Window:
    def __init__(self):
        # Initialising pygame.
        init()

        # Setting the initial window size.
        self.__defaultWindowSize = (1000, 500)

        # Setting up the screen pygame surface.
        self.__screen = display.set_mode(self.__defaultWindowSize, RESIZABLE)

        # Setting up the window icon.
        display.set_icon(image.load("IconHighRes.png"))

        # Displaying an appropriate caption on the window's top bar.
        display.set_caption("NuNet Designer")

        # running the openscreen stage.
        self.openScreen()

    # Changing the gui stage to the open screen, passing control to it.
    def openScreen(self):
        OpenScreen(self)

    # Changing the gui stage to the editor interface, passing control to it.
    def openEditor(self, filename=None):
        EditorInterface(self, filename)

    # getscreen returns the screen being used by the window, and its constituent stages.
    def getscreen(self):
        return self.__screen


# Starting the application.
app = Window()
