import csv
import jinja2
from PIL import Image
import os

def make_thumbnail(filename):
    image_name = f"images/{filename}.jpg"
    if not os.path.exists(image_name):
        return
    im = Image.open(image_name)
    thumb = im.crop((0,0,256,256))
    thumb = thumb.resize((128,128))
    thumb.save(f"images/thumbs/{filename}.jpg")

model_file = "models.csv"
output_file = "README.md"
env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))
template = env.get_template('template.md')

with open(model_file) as csvfile:
    reader = csv.DictReader(csvfile)
    models = list(reader)

for model in models:
    make_thumbnail(model["name"])

content = template.render(models = models)

with open(output_file, "w") as readme:
    readme.write(content)
