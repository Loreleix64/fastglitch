from io import BytesIO, StringIO
from PyQt4 import QtCore, QtGui
import random, sys, PIL.Image, PIL.ImageChops, PIL.ImageDraw, PIL.ImageQt, os
chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

class imgVars(object):
	def __init__(self):
		self.fname = None
		self.img = None
		self.qImg = None
		
# Hold image references so it doesn't get garbage collected
vars = imgVars()

def load_image(scene):
	convert = False
	# This is the code from the Windows build. Directory names are different in Linux, but that's about it.
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	#If it's a png, convert it to RGBA
	if src.endswith(".png"):
		convert = True
	
	image = PIL.Image.open(src)
	if convert:
		image.convert("RGBA")
	qimage = PIL.ImageQt.ImageQt(image)
	
	vars.fname = fname
	vars.img = image
	vars.qImg = qimage
	
	pixmap = QtGui.QPixmap.fromImage(qimage)
	scene.addPixmap(pixmap)	
	scene.update()
	
def update_image(scene):
		scene.clear()
		newimage = PIL.Image.open("temp.png")
		newimage.convert("RGBA")
		vars.img = newimage
		qnewimage = PIL.ImageQt.ImageQt(newimage)
		vars.qImg = qnewimage
		
		pixmap = QtGui.QPixmap.fromImage(qnewimage)
		scene.addPixmap(pixmap)
		scene.update()
		os.remove("temp.png")
		
def save_image():
	fname = QtGui.QFileDialog.getSaveFileName(None, 'Save Image', 'c:\\',"PNG Image (*.png)")
	src = unicode(fname)
	src = src.encode('utf_8')
	with open(src, 'wb') as f:
		vars.img.save(f)
		
def genImg(scene, rba_seed, rgb_seed, pxo_seed, slc_seed, art_seed, rpx_seed):
	proto1 = RandomByteAddition(vars.img, rba_seed)
	proto2 = RGBOffset(proto1, rgb_seed)
	proto3 = PixelOffset(proto2, pxo_seed)
	proto4 = Artifact(proto3, art_seed)
	proto5 = RowSlice(proto4, slc_seed)
	proto6 = Noise(proto5, rpx_seed)
	x = open('temp.png', 'wb')
	proto6.save(x)
	x.close()
	proto1.close()
	proto2.close()
	proto3.close()
	proto4.close()
	proto5.close()
	proto6.close()
	update_image(scene)
	
	
	
	
	
	
# Random Byte Addition
# Opens an image as a bytes object and continually
# breaks it by adding junk. If the image is too
# broken to load, then it breaks out of the loop
# and uses the image from the last iteration.
def RandomByteAddition(image, seed):
	bytesBroken = False
	bytes = BytesIO()
	image.save(bytes, 'jpeg')
	iter = seed
	bytes.seek(1024)
	if seed > 0:
		for x in xrange(0, iter):
			bytes2 = bytes
			bytes.seek(random.randint(0, 32), 1)
			byte = random.choice(chars)
			bytes.write(byte)
			try:
				PIL.Image.open(bytes)
			except:
				bytesBroken = True
				break

	if bytesBroken == True:
		bytes2.seek(0)
		new_img = PIL.Image.open(bytes2)
	else:
		bytes.seek(0)
		new_img = PIL.Image.open(bytes)
	return new_img

# RGB Offset
# Offsets the red, green, and blue channels of the image.
def RGBOffset(image, distance):
	distance = distance * 30
	r, g, b = image.split()
	r = PIL.ImageChops.offset(r, distance * -1, 0)
	b = PIL.ImageChops.offset(b, distance, 0)
	new_img = PIL.Image.merge('RGB', (r, g, b))
	return new_img

# Pixel Offset
# Offsets the image by the entered distance.
def PixelOffset(image, distance):
	new_img = PIL.ImageChops.offset(image, distance)
	return new_img

# Row Slice
# Offsets a random portion of the image on the x axis,
# up to the entered amount of times.
def RowSlice(image, sliceamount):
	cps = 0
	new_img = image
	for x in xrange(sliceamount):
		upbound = cps
		downbound = upbound + random.randint(16, 128)
		if downbound > image.height:
			break
		box = (0,
		 upbound,
		 new_img.width,
		 downbound)
		reigon = new_img.crop(box)
		distance = random.randint(-128, 128)
		reigon = PIL.ImageChops.offset(reigon, distance, 0)
		new_img.paste(reigon, box)
		reigon.close()
		cps = downbound

	return new_img

# Artifact
# Puts random colorful rectangles on the image.
# It doesn't look good unless used with other effects.
def Artifact(image, screwamount):
	tnspimg = image.convert('RGBA')
	base = PIL.Image.new('RGBA', tnspimg.size, (255, 255, 255, 0))
	rows = PIL.ImageDraw.Draw(base)
	cps = 0
	for x in xrange(screwamount):
		leftbound = cps
		rightbound = leftbound + random.randint(32, 128)
		if rightbound > image.width:
			break
		y1 = random.randint(0, image.height - int(round(image.height / 2.0, 0)))
		x1 = random.randint(leftbound, rightbound - 1)
		y2 = random.randint(y1, image.height)
		x2 = rightbound
		color = (random.randint(0, 255),
		 random.randint(0, 255),
		 random.randint(0, 255),
		 random.randint(64, 200))
		rows.rectangle((x1,
		 y1,
		 x2,
		 y2), fill=color)
		cps = rightbound

	new_img = PIL.Image.alpha_composite(tnspimg, base)
	return new_img

# Noise
# Adds noise.
# It's just randomly colored pixels, though.
def Noise(image, pixels):
	for x in xrange(1, pixels):
		image.putpixel((random.randint(1, image.width - 1), random.randint(1, image.height - 1)), (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)))

	new_img = image
	return new_img
	
# Color Invert
# Inverts the color.
def colorInvert(scene):
	new_img = vars.img.convert('RGB')
	new_img = PIL.ImageChops.invert(new_img)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	update_image(scene)

# Add
# Performs an addition operation on two images.
def add(scene):
	img1 = vars.img.convert('RGBA')
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	img2 = PIL.Image.open(src)
	img2 = img2.convert('RGBA')
	new_img = PIL.ImageChops.add_modulo(img1, img2)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	img2.close()
	update_image(scene)

# Multiply
# Performs a multiplication option on two images.
def logMult(scene):
	img1 = vars.img.convert('RGBA')
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	img2 = PIL.Image.open(src)
	img2 = img2.convert('RGBA')
	new_img = PIL.ImageChops.multiply(img1, img2)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	img2.close()
	update_image(scene)

# Screen
# Screens two images together.
def screen(scene):
	img1 = vars.img.convert('RGBA')
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	img2 = PIL.Image.open(src)
	img2 = img2.convert('RGBA')
	new_img = PIL.ImageChops.screen(img1, img2)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	img2.close()
	update_image(scene)

# Subtraction
# Performs a subtraction operation on two images.
def logSub(scene):
	img1 = vars.img.convert('RGBA')
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	img2 = PIL.Image.open(src)
	img2 = img2.convert('RGBA')
	new_img = PIL.ImageChops.subtract_modulo(img1, img2)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	img2.close()
	update_image(scene)

# Grain
# Alters the colors of an image randomly.
def Grain(scene):
	image = vars.img.convert('RGB')
	for y in xrange(image.height):
		for x in xrange(image.width):
			r, g, b = image.getpixel((x, y))
			r += random.randint(-16, 16)
			g += random.randint(-16, 16)
			b += random.randint(-16, 16)
			if r > 255:
				r = random.randint(250, 255)
			if b > 255:
				b = random.randint(250, 255)
			if g > 255:
				g = random.randint(250, 255)
			image.putpixel((x, y), (r, g, b))

	new_img = image
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	update_image(scene)

# Quantize
# Reduces an image to the specified number of colors.
def Quantize(scene, number):
	img2 = vars.img.quantize(number)
	new_img = img2.convert('RGB')
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	update_image(scene)

# Differential
# Performs a differential operation on two images.
def differ(scene):
	img1 = vars.img.convert('RGBA')
	fname = QtGui.QFileDialog.getOpenFileName(None, 'Select Image', 'c:\\',"Image files (*.jpg *.jpeg *jpe *.png)")
	scene.clear()
	src = unicode(fname)
	src = src.encode('utf_8')
	img2 = PIL.Image.open(src)
	img2 = img2.convert('RGBA')
	new_img = PIL.ImageChops.difference(img1, img2)
	x = open('temp.png', 'wb')
	new_img.save(x)
	x.close()
	img2.close()
	update_image(scene)
