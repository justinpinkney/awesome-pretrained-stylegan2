# iterate over lines in csv
# download pickle
# setup docker image
# run container to generate 9 images
# Compile images into montage

import csv
import os
filename = 'models.csv'
import traceback
import requests
import gdown
from mega import Mega
from pathlib import Path
import lzma
import subprocess
from PIL import Image
import shutil

images_dir = Path('images')
models_dir = Path('models')

for directory in (images_dir, models_dir):
    directory.mkdir(exist_ok=True)

def run_network(pkl_path, output_dir, clean_up=False):
    working_dir = '/working'
    image_name = 'awesome-stylegan2'
    seeds = '0-8'
    if clean_up:
        cmd = ['rm', '-rf', working_dir + '/' + str(output_dir),]
    else:
        cmd = ['python', 'run_generator.py', 
            'generate-images',
            '--network', working_dir + '/' + str(pkl_path),
            '--seeds', seeds,
            '--result-dir', working_dir + '/' + str(output_dir),
                ]

    base =['docker', 
                    'run',
                    '-t',
                    '--rm',
                    '--net', 'host',
                    '--gpus', 'all',
                    '-v', '/home/justin/code/awesome-pretrained-stylegan2:/working',
                    image_name,
                    ]
    base.extend(cmd)
    subprocess.run(base)


def download(url, dest_path):
    print(f'Downloading {dest_path} model')
    
    if dest_path.exists():
        print(f'{dest_path} already exists, skipping download')
        pkl_file = list(dest_path.glob('*'))[0]
        return pkl_file

    dest_path.mkdir()
    if 'drive.google.com' in url:
        downloaded_file = gdown.download(url, output=dest_path)
    elif 'mega.nz' in url:
        mega = Mega()
        m = mega.login()
        downloaded_file = m.download_url(url, dest_path=str(dest_path))
    else:
        r = requests.get(url)
        downloaded_file = 'downloaded.pkl'
        with open(downloaded_file, 'wb') as f:
            f.write(r.content)

    downloaded_file = Path(downloaded_file)

    if downloaded_file.suffix == ".xz":  
        print(f'Downloaded file {downloaded_file} is .xz')
        pkl_file = dest_path/downloaded_file.stem
        with lzma.open(downloaded_file, 'rb') as in_file:
            with open(pkl_file, 'wb') as out:
                out.write(in_file.read())
    else:
        pkl_file = dest_path/downloaded_file.name
        downloaded_file.replace(pkl_file)

    return pkl_file

def draw_figure(results_dir, filename, rows=3, out_size=256):
    
    canvas = Image.new('RGB', (out_size * rows, out_size*rows), 'white')
    images = Path(results_dir).rglob('*.png')
    for col in range(rows):
        for row in range(rows):
            image = Image.open(next(images))
            image = image.resize((out_size, out_size), Image.ANTIALIAS)
            canvas.paste(image, (out_size*col, out_size*row))
    
    canvas.save(filename)

if __name__ == "__main__":

    temp_outputs = Path('temp_outputs')
    
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for model in reader:
            image_name = images_dir/(model["name"] + '.jpg')
            model_location = models_dir/model["name"]

            if os.path.exists(image_name):
                print(f'{image_name} already exists.')
                continue

            pickle_location = download(model['download_url'], model_location)

            #temp_outputs.mkdir()
            run_network(pickle_location, temp_outputs)
            draw_figure(temp_outputs, image_name)
            run_network(pickle_location, temp_outputs, clean_up=True)
            #shutil.rmtree(temp_outputs)
            
