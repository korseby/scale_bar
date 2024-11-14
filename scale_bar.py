#!/usr/bin/env python

# Load modules
import errno, sys
import argparse
import pandas
import glob
from PIL import Image, ImageFont, ImageDraw
import PIL
PIL.Image.MAX_IMAGE_PIXELS = 10737418240

if sys.platform.lower() == "win32":
	os.system('color')

# Parse arguments
parser = argparse.ArgumentParser(description='Draw a scale bar on microscopic images.')
parser.add_argument('-v', '--version', action='version', version='Scale Bar Version 0.3',
                   help='show version')
parser.add_argument('-c', '--csv', metavar='distances.csv', dest="input_csv", required=True,
                   help='read input scale bar distances csv')
parser.add_argument('-q', '--quality', metavar='80', dest="jpeg_quality", default=80, type=int, required=False,
                   help='percent quality of resulting JPEG [1-100]')
parser.add_argument('-i', '--input_image', metavar='src.jpg', dest="input_image", required=True,
                   help='input image file')
parser.add_argument('-o', '--output_image', metavar='dst.jpg', dest="output_image", required=True,
                   help='output image file')
parser.add_argument('-s', '--scale', metavar='0.85', dest="scale_multiplier", default=1.0, required=False,
                   help='scale multiplier in the range [0.1-1] when the height of the source image has been cropped, or [0] when the scale multiplier is calculated from the height of the source image')
parser.add_argument('-t', '--type', metavar='1', dest="scale_type", default=1, type=int, required=False,
                   help='type of the scale bar [1: Moose-CH, 2:Korseby]')
parser.add_argument('-fc', '--filter-camera', metavar='\"Canon EOS R6 Mark II\"', dest="filter_camera", default="Canon EOS R6 Mark II", required=False,
                   help='Filtering criterium for the camera, e.g. \ "Canon EOS R6 Mark II\"')
parser.add_argument('-fms', '--filter-microscope', metavar='\"Zeiss Axio Scope A1\"', dest="filter_microscope", default="Zeiss Axio Scope A1", required=False,
                   help='Filtering criterium for the microscope, e.g. \ "Zeiss Axio Scope A1\"')
parser.add_argument('-fo', '--filter-objective', metavar='\"Apochromat 20x\"', dest="filter_objective", default="", required=False,
                   help='Filtering criterium for the used objective (lens), e.g. \ "Apochromat 20x\"')
parser.add_argument('-fmg', '--filter-magnification', metavar='\"20x\"', dest="filter_magnification", default="20x", required=False,
                   help='Filtering criterium for the magnification, e.g. \ "20x\"')

args = parser.parse_args()

# Input CSV with scale bar distances
input_csv = args.input_csv

# Input image file
input_image = args.input_image

# Output image file
output_image = args.output_image

# JPEG Quality
jpeg_quality = args.jpeg_quality

# Scale multiplier
scale_multiplier = float(args.scale_multiplier)

# Scale type
scale_type = args.scale_type

# Filtering criteria
filter_camera = args.filter_camera
filter_microscope = args.filter_microscope
filter_objective = args.filter_objective
filter_magnification = args.filter_magnification

# Read input CSV with scale bar distances
scales = pandas.read_csv(input_csv, delimiter=',')

# Remove whitespace in column names
scales.columns = scales.columns.str.replace(' ', '')

# Select one entry from input CSV according to filtering criteria
entry = scales[ scales.Camera.str.contains(filter_camera) &
#                scales.Microscope.str.contains(filter_microscope) &
                scales.ObjectiveLens.str.contains(filter_objective) &
                scales.Magnification.str.contains(filter_magnification) ]

# Input image
img = Image.open(input_image).convert("RGB")
exif = img.info['exif']
icc_profile = img.info.get('icc_profile')

# Read width and height from image
width, height = img.size

# Make sanity checks
if (len(entry.index) <= 0):
	print("\033[91m{}\033[00m" .format("Warning! No matches from filtering criteria. Writing image without scale."), file=sys.stderr)
	img.save(output_image, format='JPEG', quality=jpeg_quality, optimize=True, progressive=True, exif=exif, icc_profile=icc_profile)
	sys.exit(1)
elif (len(entry.index) > 1):
	print("\033[91m{}\033[00m" .format("Warning! Multiple matches from filtering criteria. Writing image without scale."), file=sys.stderr)
	img.save(output_image, format='JPEG', quality=jpeg_quality, optimize=True, progressive=True, exif=exif, icc_profile=icc_profile)
	sys.exit(2)

# Scale of one pixel
scale_pixel = (height / entry.ImageHeight) * (entry.PixelDistance / entry.Scale)

# Width of scale bar
if (scale_multiplier == 0):
	scale_width = round(scale_pixel * entry.Scale * (entry.ImageHeight / height), 0)
elif (scale_multiplier == 1):
	scale_width = round(scale_pixel * entry.Scale, 0)
else:
	scale_width = round(scale_pixel * entry.Scale * scale_multiplier, 0)

# Height of scale bar
scale_height = round((height) / (entry.ImageHeight / 100), 0)

# Label beside the scale base
scale_label = (' ' + entry.Scale.to_string(index=False) + ' ' + entry.Unit.to_string(index=False) + '     ')

# Define font
if (scale_type == 1):
	scale_font_size = int(round(scale_height.iloc[0] * 1.5, 0))
	scale_font = ImageFont.truetype("Arial Bold", scale_font_size)
	scale_label_size = scale_font.getbbox(scale_label)
	scale_label_width = scale_label_size[2] - scale_label_size[0]
	scale_label_height = scale_label_size[3] - scale_label_size[1]
else:
	scale_height = round(scale_height / 6, 0)
	scale_font_size = int(round(height / 25, 0))
	scale_font = ImageFont.truetype("Arial Bold", scale_font_size)
	scale_label_width = scale_label_size[2] - scale_label_size[0]
	scale_label_height = scale_label_size[3] - scale_label_size[1]

# Coordinates of scale bar
if (scale_type == 1):
	scale_bar_x1 = (width - scale_width - scale_label_width)
	scale_bar_y1 = height - scale_height - (scale_font.getbbox('    ')[2] - scale_font.getbbox('    ')[0])
	scale_bar_x2 = scale_bar_x1 + scale_width
	scale_bar_y2 = scale_bar_y1 + scale_height
	scale_bar_y3 = scale_bar_y1 - ((scale_label_height - (scale_bar_y2 - scale_bar_y1)) / 2)
else:
	scale_bar_x1 = (width - scale_width) - round(width / 33, 0)
	scale_bar_y1 = height - scale_height - round(height / 33, 0) - (scale_font.getbbox('    ')[2] - scale_font.getbbox('    ')[0])
	scale_bar_x2 = scale_bar_x1 + scale_width
	scale_bar_y2 = scale_bar_y1 + scale_height
	scale_bar_x4 = scale_bar_x1 + (scale_width / 2) - (scale_label_width / 2.5)
	scale_bar_y4 = scale_bar_y2 + scale_height

# Type 1: Draw box and label beside it
if (scale_type == 1):
	draw = ImageDraw.Draw(img)
	draw.rectangle( ((scale_bar_x1.iloc[0], scale_bar_y1.iloc[0]), (scale_bar_x2.iloc[0], scale_bar_y2.iloc[0])), fill="black")
	draw.text((scale_bar_x2.iloc[0], (scale_bar_y3.iloc[0] - (scale_bar_y2.iloc[0] - scale_bar_y1.iloc[0]) / 8)), scale_label, font=scale_font, fill="black")
else:
	adj = round(height / 600, 1)
	draw = ImageDraw.Draw(img)
	draw.rectangle( ((scale_bar_x1, scale_bar_y1), (scale_bar_x2, scale_bar_y2)), fill="black")
	draw.rectangle( ((scale_bar_x1, scale_bar_y1-(adj*3)), (scale_bar_x1+(adj*2), scale_bar_y2+(adj*3))), fill="black")
	draw.rectangle( ((scale_bar_x2-(adj*2), scale_bar_y1-(adj*3)), (scale_bar_x2, scale_bar_y2+(adj*3))), fill="black")
	draw.text((scale_bar_x4-adj, scale_bar_y4), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4+adj, scale_bar_y4), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4, scale_bar_y4-adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4, scale_bar_y4+adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4-adj, scale_bar_y4+adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4+adj, scale_bar_y4-adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4-adj, scale_bar_y4-adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4+adj, scale_bar_y4+adj), scale_label, font=scale_font, fill="black")
	draw.text((scale_bar_x4, scale_bar_y4), scale_label, font=scale_font, fill="white")

# Save output image
img.save(output_image, format='JPEG', quality=jpeg_quality, optimize=True, progressive=True, exif=exif, icc_profile=icc_profile)

#print("Done.")
