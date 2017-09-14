# SPI LCD Library

import os, sys, time
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image
from lcdfonts import *

# Lib: https://github.com/adafruit/Adafruit_ILI9341

# Hardware GPIO pins
boardPin1 = 17
boardPin2 = 22
boardPin3 = 23
boardPin4 = 27
boardPinDecoderInput = 21

# Constants for interacting with display registers.
TFTWIDTH = 320
TFTHEIGHT = 240

# ILI9340 commands
ILI9340_NOP = 0x00
ILI9340_SWRESET = 0x01
ILI9340_RDDID = 0x04
ILI9340_RDDST = 0x09

ILI9340_SLPIN = 0x10
ILI9340_SLPOUT = 0x11
ILI9340_PTLON = 0x12
ILI9340_NORON = 0x13

ILI9340_RDMODE = 0x0A
ILI9340_RDMADCTL = 0x0B
ILI9340_RDPIXFMT = 0x0C
ILI9340_RDIMGFMT = 0x0A
ILI9340_RDSELFDIAG = 0x0F

ILI9340_INVOFF = 0x20
ILI9340_INVON = 0x21
ILI9340_GAMMASET = 0x26
ILI9340_DISPOFF = 0x28
ILI9340_DISPON = 0x29

ILI9340_CASET = 0x2A
ILI9340_PASET = 0x2B
ILI9340_RAMWR = 0x2C
ILI9340_RAMRD = 0x2E

ILI9340_PTLAR = 0x30
ILI9340_MADCTL = 0x36

ILI9340_MADCTL_MY = 0x80
ILI9340_MADCTL_MX = 0x40
ILI9340_MADCTL_MV = 0x20
ILI9340_MADCTL_ML = 0x10
ILI9340_MADCTL_RGB = 0x00
ILI9340_MADCTL_BGR = 0x08
ILI9340_MADCTL_MH = 0x04

ILI9340_PIXFMT = 0x3A

ILI9340_FRMCTR1 = 0xB1
ILI9340_FRMCTR2 = 0xB2
ILI9340_FRMCTR3 = 0xB3
ILI9340_INVCTR = 0xB4
ILI9340_DFUNCTR = 0xB6

ILI9340_PWCTR1 = 0xC0
ILI9340_PWCTR2 = 0xC1
ILI9340_PWCTR3 = 0xC2
ILI9340_PWCTR4 = 0xC3
ILI9340_PWCTR5 = 0xC4
ILI9340_VMCTR1 = 0xC5
ILI9340_VMCTR2 = 0xC7

ILI9340_RDID1 = 0xDA
ILI9340_RDID2 = 0xDB
ILI9340_RDID3 = 0xDC
ILI9340_RDID4 = 0xDD

ILI9340_GMCTRP1 = 0xE0
ILI9340_GMCTRN1 = 0xE1


class LCDTFT:
  
    def __init__(self, spidev, dc_pin, rst_pin=0, led_pin=0, spi_speed=16000000):
        # CE is 0 or 1 for RPI, but is actual CE pin for virtGPIO
        # RST pin.  0  means soft reset (but reset pin still needs holding high (3V)
        # LED pin, may be tied to 3V (abt 14mA) or used on a 3V logic pin (abt 7mA)
        # and this object needs to be told the GPIO and SPIDEV objects to talk to
        global GPIO
        self.SPI = spidev
        self.SPI.open(0, 0)
        self.SPI.max_speed_hz = 32000000

        self.BLUE = self.colour565(0, 0, 255)
        self.GREEN = self.colour565(0, 255, 0)
        self.RED = self.colour565(255, 0, 0)
        self.PINK = self.colour565(255, 120, 120)
        self.LIGHTBLUE = self.colour565(120, 120, 255)
        self.LIGHTGREEN = self.colour565(120, 255, 120)
        self.BLACK = self.colour565(0, 0, 0)
        self.WHITE = self.colour565(255, 255, 255)
        self.GREY = self.colour565(120, 120, 120)
        self.YELLOW = self.colour565(255, 255, 0)
        self.MAGENTA = self.colour565(255, 0, 255)
        self.CYAN = self.colour565(0, 255, 255)

        self.RST = rst_pin
        self.DC = dc_pin
        self.LED = led_pin
        GPIO.setup(dc_pin, GPIO.OUT)
        GPIO.output(dc_pin, GPIO.HIGH)
        if rst_pin:
          GPIO.setup(rst_pin, GPIO.OUT)
          GPIO.output(rst_pin, GPIO.HIGH)
        if led_pin:
          GPIO.setup(led_pin, GPIO.OUT)
          self.led_on(True)
        self.SPI.open(0, 0)    # CE is 0 or 1   (means pin CE0 or CE1) or actual CE pin for virtGPIO
        self.SPI.max_speed_hz=spi_speed # Black board may cope with 32000000 Hz. Red board up to 16000000. YMMV.

        time.sleep(0.5)
        self.init_LCD()

    # Pack 3 bytes of rgb value in 2 byte integer, R, G and B 0-255
    def colour565(self, r,g,b):
        return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
    
    # Translate x,y pixel coords. to text column,row
    def textX(self, x, font=3):
        return x*(self.fontDim[font][0])

    def textY(self, y, font=3):
        return y*(self.fontDim[font][1])
  
    def reset_LCD(self):
        if self.RST == 0:
            self.write_command(ILI9340_SWRESET)
        else:
            GPIO.output(self.RST, False)
            time.sleep (0.2)
            GPIO.output(self.RST, True)
        time.sleep(0.2)
    
    def write_command(self, address):
        GPIO.output(self.DC, False)
        self.SPI.writebytes([address])

    def write_data(self, data):
        GPIO.output(self.DC, True)
        if not type(data) == type([]):   # is it already a list?
            data = [data]
        self.SPI.writebytes(data)

    def write_reg(self, data):
        if len(data) > 0:
            self.write_command(data[0])
        if len(data) > 1:
            self.write_data(data[1:])
    
    def init_LCD(self):
        self.write_reg([0x01]) #/* software reset */
        time.sleep(0.1)
        self.write_reg([0x28]) #/* display off */
        #/* --------------------------------------------------------- */
        self.write_reg([0xCF, 0x00, 0x83, 0x30])
        self.write_reg([0xED, 0x64, 0x03, 0x12, 0x81])
        self.write_reg([0xE8, 0x85, 0x01, 0x79])
        self.write_reg([0xCB, 0x39, 0X2C, 0x00, 0x34, 0x02])
        self.write_reg([0xF7, 0x20])
        self.write_reg([0xEA, 0x00, 0x00])
        #/* ------------Power control-------------------------------- */
        self.write_reg([0xC0, 0x26])
        self.write_reg([0xC1, 0x11])
        #/* ------------VCOM --------- */
        self.write_reg([0xC5, 0x35, 0x3E])
        self.write_reg([0xC7, 0xBE])
        #/* ------------memory access control------------------------ */
        self.write_reg([0x3A, 0x55]) #/* 16bit pixel */
        #/* ------------frame rate----------------------------------- */
        self.write_reg([0xB1, 0x00, 0x1B])
        #/* ------------Gamma---------------------------------------- */
        self.write_reg([0x26, 0x01])
        #/* ------------Display-------------------------------------- */
        self.write_reg([0xB7, 0x07]); #/* entry mode set */
        self.write_reg([0xB6, 0x0A, 0x82, 0x27, 0x00])
        self.write_reg([0x11]) #/* sleep out */
        # Rotation
        self.write_reg([ILI9340_MADCTL, ILI9340_MADCTL_MV | ILI9340_MADCTL_MY | ILI9340_MADCTL_MX | ILI9340_MADCTL_RGB])
        # Rotation: 0 - writedata(ILI9340_MADCTL_MX | ILI9340_MADCTL_RGB);
        # Rotation: 1 - writedata(ILI9340_MADCTL_MV | ILI9340_MADCTL_RGB)
        # Rotation: 2 - writedata(ILI9340_MADCTL_MY | ILI9340_MADCTL_RGB)
        # Rotation: 3 - writedata(ILI9340_MADCTL_MV | ILI9340_MADCTL_MY | ILI9340_MADCTL_MX | ILI9340_MADCTL_RGB)
        time.sleep(0.1)
        self.write_reg([0x29]) #/* display on */
        time.sleep(0.05)

    def setAddrWindow(self, xs, ys, xe, ye):
        # /* Column address set */
        self.write_reg([0x2A, (xs >> 8) & 0xFF, xs & 0xFF, (xe >> 8) & 0xFF, xe & 0xFF])
        #/* Row adress set */
        self.write_reg([0x2B, (ys >> 8) & 0xFF, ys & 0xFF, (ye >> 8) & 0xFF, ye & 0xFF])
        #/* Memory write */
        self.write_reg([0x2C])

    # clear display,writes same color pixel in all screen
    def clear_display(self, color):
        color_hi = color>>8
        color_lo = color&(~(65280))
        self.setAddrWindow(0, 0, TFTWIDTH, TFTHEIGHT)
        self.write_command(ILI9340_RAMWR)
        VIRTUALGPIO = 0
        if GPIO.RPI_REVISION == VIRTUALGPIO:
          # For virtGPIO "fill" is MUCH faster, but is a special VirtGPIO function
          GPIO.output(self.DC,True)
          self.SPI.fill(16384, color)
        else:
          # Otherwise (RPI) repetitively push out all those identical pixels
          for row in range(TFTHEIGHT):
            self.write_data([color_hi, color_lo] * TFTWIDTH)

    def draw_dot(self, x, y, color):
        color_hi = color>>8
        color_lo = color&(~(65280))
        self.setAddrWindow(x, y, x+1, y+1)
        self.write_command(ILI9340_RAMWR)
        self.write_data([color_hi, color_lo])
      
    # Bresenham's algorithm to draw a line with integers. x0<=x1, y0<=y1
    def draw_line(self, x0, y0, x1, y1, color):
        dy = y1-y0
        dx = x1-x0
        if dy < 0:
            dy =- dy
            stepy =- 1
        else:
            stepy = 1

        if dx < 0:
            dx =- dx
            stepx =- 1
        else:
            stepx = 1
        
        dx <<= 1
        dy <<= 1
        self.draw_dot(x0, y0, color)
        if dx > dy:
            fraction = dy-(dx>>1)
            while x0 != x1:
                if fraction>=0:
                    y0 += stepy
                    fraction -= dx
                x0 += stepx
                fraction += dy
                self.draw_dot(x0, y0, color)
        else:
            fraction = dx-(dy>>1)
            while y0 != y1:
                if fraction >= 0:
                    x0 += stepx
                    fraction -= dy
                y0 += stepy
                fraction += dx
                self.draw_dot(x0, y0, color)

    def draw_rectangle(self, x0,y0,x1,y1,color):
        self.draw_line(x0,y0,x0,y1,color)
        self.draw_line(x0,y1,x1,y1,color)
        self.draw_line(x1,y0,x1,y1,color)
        self.draw_line(x0,y0,x1,y0,color)
      
    def draw_filled_rectangle(self, x0,y0,x1,y1, color):
        color_hi = color>>8
        color_lo = color&(~(65280))
        self.setAddrWindow(x0, y0, x1, y1)
              
        self.write_command(ILI9340_RAMWR)
        for pixels in range(0, 1+x1-x0):
            dbuf = [color_hi, color_lo] * (y1-y0)
            self.write_data(dbuf)
    
    # Font dimensions for fonts 1-8.  [W, H, Scale]
    fontDim = ([0], [4, 6, 1], [8, 12, 2], [6, 8, 1], [12, 16, 2], [8, 12, 1], [16, 24, 2], [8, 16, 1], [16, 32, 2])

    # writes a character in graphic coordinates x,y, with foreground and background colours
    def put_char(self, character, x, y, fgcolor, bgcolor, font = 3):
        fgcolor_hi = fgcolor>>8
        fgcolor_lo = fgcolor&(~(65280))
        bgcolor_hi = bgcolor>>8
        bgcolor_lo = bgcolor&(~(65280))
        fontW = self.fontDim[font][0]
        fontH = self.fontDim[font][1]
        fontScale  = self.fontDim[font][2]
        character  = ord(character)
        if not (font == 3 or font == 4):   # restricted char set 32-126 for most
            if character < 32 or character > 126: # only strictly ascii chars
                character = 0
            else:
                character -= 32
        self.setAddrWindow(x, y, x+fontW-1, y + fontH-1)
        xx = [0]
        if fontScale == 2:
          xx = [0, 2, 2*fontW, 2 + 2*fontW]   # DOUBLE: every pixel becomes a 2x2 pixel

        self.write_command(ILI9340_RAMWR)
        cbuf = [0] * (fontW * fontH * 2)
        for row in range (0, int(fontH // fontScale)):
            for column in range (0,int(fontW // fontScale)):
                topleft = (column*2*fontScale) + (row*2*fontW*fontScale)
                if font <= 2:
                    pixOn = (font4x6[character][row]) & (1<<column)
                elif font >= 7:
                    pixOn = (font8x16[character][row]) & (1<<column)
                elif font >= 5:
                    pixOn = (font8x12[character][row]) & (1<<column)
                else:
                    pixOn = (font6x8[character][column]) & (1<<row)
                
                for rpt in xx:    # one pixel or a 2x2 "doubled" pixel
                    cbuf[rpt+topleft] = fgcolor_hi if pixOn else bgcolor_hi
                    cbuf[rpt+1+topleft] = fgcolor_lo if pixOn else bgcolor_lo
        self.write_data(cbuf)
      
    # writes a string in graphic x,y coordinates, with
    # foreground and background colours. If edge of screen is reached,
    # it wraps to next text line to same starting x coord.
    def put_string(self, str, originx, y, fgcolor, bgcolor, font = 3):
        x = originx
        fontW = self.fontDim[font][0]
        fontH = self.fontDim[font][1]
        for char_number in range (0,len(str)):
            if x+fontW > TFTWIDTH:
                x = originx
                y += fontH
            if y + fontH > TFTHEIGHT:
                break
            
            self.put_char(str[char_number], x, y, fgcolor, bgcolor, font)
            x += fontW
    
#    def draw_img(self, filename, x0=0, y0=0):
#      if not os.path.exists(filename): return
#      
#      im = Image.open(filename)
#      width, height = im.size
#      rgb_im = im.convert('RGB')
#      self.setAddrWindow(x0, y0, x0+width-1, y0+height-1)
#      self.write_command(ILI9340_RAMWR)
#
#      for y in range(height):
#          dbuf = [0] * (width*2)
#          for x in range(width):
#              r, g, b = rgb_im.getpixel((x, y))
#              RGB = self.colour565(r, g, b)
#              dbuf[2*x] = RGB>>8
#              dbuf[1 + (2*x)] = RGB & (~65280)
#          self.write_data(dbuf)

    def draw_imgFile(self, filename, x0=0, y0=0):
        if not os.path.exists(filename): return
    
        im = Image.open(filename)
        width, height = im.size
        rgb_im = im.convert('RGB')
        self.draw_img(rgb_im, x0, y0, width, height)

    def draw_img(self, imageData, x, y, width, height):
        self.setAddrWindow(x, y, x + width - 1, y + height - 1)
        self.write_command(ILI9340_RAMWR)
      
        # numpi code from https://github.com/adafruit/Adafruit_Python_ILI9341/blob/master/Adafruit_ILI9341/ILI9341.py
        pb = np.array(imageData).astype('uint16')
        color = ((pb[:, :, 2] & 0xF8) << 8) | ((pb[:, :, 1] & 0xFC) << 3) | (pb[:, :, 0] >> 3)
        pixelbytes = np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()
        
        # Maximum SPI block is 4096
        for i in xrange(0, len(pixelbytes), 4096):
            dblock = pixelbytes[i:i+4096]
            self.write_data(dblock)

    def invert_screen(self):
        self.write_command(ILI9340_INVON)
    
    def normal_screen(self):
        self.write_command(ILI9340_INVOFF)

    def led_on(self, onoff):
        if self.LED:
            GPIO.output(self.LED, GPIO.HIGH if onoff else GPIO.LOW)

if __name__ == "__main__":
  
  import spidev

  print("LCD TFT Test")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)

  DC =  25    # GPIO25 (22), Data/Command
  LED = 18    # GPIO18 (12), Led backlight
  RST = 0     # Reset, not used for this board

  # Don't forget the other 2 SPI pins SCK and MOSI (SDA)
  TFT = LCDTFT(spidev.SpiDev(), DC, RST, LED)
  TFT.clear_display(TFT.WHITE)
  TFT.led_on(True)
  
  TFT.draw_imgFile("test1.png", 0, 0)
  TFT.put_string("09:27", 116,4, TFT.BLACK, TFT.colour565(238, 238, 238), 6)
  top = 37
  h = 53
  h1 = 22
  font = 4
  col = TFT.colour565(50, 50, 50)
  TFT.put_string("Capture", 36, top, col, TFT.WHITE, font)
  TFT.put_string("2 active cams", 36,top + h1, col, TFT.WHITE, font)
  TFT.put_string("Uploading", 36, top + h, col, TFT.WHITE, font)
  TFT.put_string("T:550 HD:327 V:0", 36, top + h + h1, col, TFT.WHITE, font)
  TFT.put_string("Event info", 36, top + 2*h, col, TFT.WHITE, font)
  TFT.put_string("ID:1234 Split:5K", 36,top + 2*h + h1, col, TFT.WHITE, font)
  TFT.put_string("Settings", 36,top + 3*h, col, TFT.WHITE, font)
  TFT.put_string("Device ID: 1234", 36,top + 3*h + h1, col, TFT.WHITE, font)
 
  #time.sleep(1.0)
  #TFT.put_string("Hello,World!", 28,28, TFT.RED, TFT.BLUE)  # std font 3 (default)
  
  #TFT.draw_filled_rectangle(0, 0, 320, 240, TFT.WHITE)
  
  #for p in range(0,320/2):
  #  TFT.draw_line(0, 2*p, 320, 2*p, TFT.BLUE)
  
#  TFT.draw_line(0, 0, 320, 240, TFT.GREEN)
#  TFT.draw_line(0, 240, 320, 0, TFT.RED)
#  TFT.draw_line(0, 10, 320, 10, TFT.BLACK)
#  TFT.draw_line(0, 11, 320, 11, TFT.WHITE)
#  
#  TFT.draw_filled_rectangle(200,140,240,160, TFT.BLUE)
#  
#  TFT.draw_dot(4,60, TFT.RED)
#  TFT.draw_dot(6,60, TFT.RED)
#  TFT.draw_dot(8,60, TFT.RED)
#  TFT.draw_dot(10,60, TFT.RED)

#  TFT.put_string("Red", 24,2,  TFT.RED, TFT.WHITE)     # doubled font 4
#  TFT.put_string("Green", 24,22, TFT.GREEN, TFT.WHITE)     # doubled font 4
#  TFT.put_string("Blue", 24,42, TFT.BLUE, TFT.WHITE)     # doubled font 4
#
#  TFT.put_string("Font-2", 24,70, TFT.BLACK, TFT.WHITE, 2)
#  TFT.put_string("Font-3", 124,86, TFT.BLACK, TFT.WHITE, 3)
#  TFT.put_string("Font-4", 24,100, TFT.BLACK, TFT.WHITE, 4)
#  TFT.put_string("Font-5", 124,100, TFT.BLACK, TFT.WHITE, 5)
#  TFT.put_string("Font-6", 24,120, TFT.BLACK, TFT.WHITE, 6)
#  TFT.put_string("Font-7", 124,140, TFT.BLACK, TFT.WHITE, 7)
#  TFT.put_string("Font-8", 24,140, TFT.BLACK, TFT.WHITE, 8)
#
#  TFT.draw_img("logo.png", 220, 20)

  def onRPiButtonPressed1(channel):
      print("PIN1")
      #TFT.put_string("BTN1", 0,220,TFT.RED, TFT.WHITE, 4)     # doubled font 4
      TFT.draw_imgFile("test1.png", 0, 0)
  
  def onRPiButtonPressed2(channel):
      print("PIN2")
      TFT.draw_imgFile("test2.png", 0, 0)
      TFT.put_string("BTN2", 0,220,TFT.RED, TFT.WHITE, 4)     # doubled font 4

  def onRPiButtonPressed3(channel):
      print("PIN3")
      TFT.draw_imgFile("test3.png", 0, 0)

  def onRPiButtonPressed4(channel):
      print("PIN4")
      TFT.put_string("BTN4", 0,220,TFT.RED, TFT.WHITE, 4)     # doubled font 4
  
  # Setup Pins
  GPIO.setup(boardPin1, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.setup(boardPin2, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.setup(boardPin3, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.setup(boardPin4, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.setup(boardPinDecoderInput, GPIO.IN, pull_up_down = GPIO.PUD_UP)
  
  GPIO.add_event_detect(boardPin1, GPIO.FALLING, callback=onRPiButtonPressed1, bouncetime = 200)
  GPIO.add_event_detect(boardPin2, GPIO.FALLING, callback=onRPiButtonPressed2, bouncetime = 200)
  GPIO.add_event_detect(boardPin3, GPIO.FALLING, callback=onRPiButtonPressed3, bouncetime = 200)
  GPIO.add_event_detect(boardPin4, GPIO.FALLING, callback=onRPiButtonPressed4, bouncetime = 200)
  GPIO.add_event_detect(boardPinDecoderInput, GPIO.FALLING, callback=onRPiDecoderEvent, bouncetime = 200)
  
  try:
    while True:
      time.sleep(0.25)
  
  except KeyboardInterrupt:
    pass

  print("Done")
