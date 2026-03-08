from ascii_magic import AsciiArt
my_art = AsciiArt.from_image('sailing.jpg')
my_art.to_terminal(columns=100, monochrome=False)
html = my_art.to_html(columns=200, width_ratio=2)
with open('ascii_img.html', 'w') as f:
    f.write(html)
