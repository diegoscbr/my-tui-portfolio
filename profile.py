from PIL import Image, ImageOps
from ascii_magic import AsciiArt, Front, Back

img = Image.open('mog.jpeg')
img = ImageOps.exif_transpose(img)
img.save('diego_fixed.png')

my_art = AsciiArt.from_image('mog.jpeg')
my_art.to_terminal(columns=80, char=" .+*#")
