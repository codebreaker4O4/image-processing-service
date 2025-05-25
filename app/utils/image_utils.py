from PIL import Image

def resize_image(path, width, height):
    with Image.open(path) as img:
        img = img.resize((width, height))
        img.save(path)
        
def rotate_image(path, angle):
    with Image.open(path) as img:
        img = img.rotate(angle)
        img.save(path)