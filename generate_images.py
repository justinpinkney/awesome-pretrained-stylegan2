# iterate over lines in csv
# download pickle
# setup docker image
# run container to generate 9 images
# Compile images into montage

import json
import lzma
import math
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import gdown
import requests
from mega import Mega
from PIL import Image

model_data_file = 'models.json'

images_dir = Path('images')
movies_dir = Path('movies')
models_dir = Path('models')

for directory in (images_dir, models_dir, movies_dir):
    directory.mkdir(exist_ok=True)

working_dir = '/working'
temp_outputs = Path('temp_outputs')
truncation = str(0.75)

def run_in_container(cmd_to_run):
    """Run the requested command in the docker container"""
    image_name = 'awesome-stylegan2'
    
    base =['docker', 
                    'run',
                    '-t',
                    '--rm',
                    '--net', 'host',
                    '--gpus', 'all',
                    '-v', '/home/justin/code/awesome-pretrained-stylegan2:/working',
                    image_name,
                    ]
    base.extend(cmd_to_run)
    subprocess.run(base)


def run_network(pkl_path, output_dir):
    seeds = '0-11'
    cmd = ['python', 'run_generator.py', 
        'generate-images',
        '--network', working_dir + '/' + str(pkl_path),
        '--seeds', seeds,
        '--truncation-psi', truncation,
        '--result-dir', working_dir + '/' + str(output_dir),
            ]
    run_in_container(cmd)

def run_noise_loop(pkl_path, output_dir):
    cmd = ['python', 'grid_vid.py', 
            working_dir + '/' + str(pkl_path),
            '--truncation-psi', truncation, 
            '--grid-size', '3', '3', 
            '--duration-sec', '10', 
            '--smoothing-sec', '1',
            '--output-width', str(3*256),
            '--mp4', working_dir + '/' + str(output_dir),]
    run_in_container(cmd)


def run_style_mixing(pkl_path, output_dir, resolution):
    row_seeds = '100-103'
    col_seeds = '200-203'
    if resolution:
        top_style = int(math.log(resolution/4)/math.log(2))
    else:
        top_style = 8
    styles = '0-' + str(top_style)
    cmd = ['python', 'run_generator.py', 
        'style-mixing-example',
        '--network', working_dir + '/' + str(pkl_path),
        '--row-seeds', row_seeds,
        '--col-seeds', col_seeds,
        '--col-styles', styles,
        '--truncation-psi', truncation,
        '--result-dir', working_dir + '/' + str(output_dir),
            ]
    run_in_container(cmd)


def clean_up(output_dir):
    """Delete the requested directory in the container"""
    cmd = ['rm', '-rf', working_dir + '/' + str(output_dir),]
    run_in_container(cmd)
    

def parse_resolution(res):
    """parse the resolution from string.
    e.g. either 512x512 or Unknown"""
    first_element = res.split("x")[0]
    try:
        resolution = int(first_element)
    except ValueError:
        resolution = None
    
    return resolution

def download(url, dest_path):
    print(f'Downloading {dest_path} model')
    
    if dest_path.exists():
        print(f'{dest_path} already exists, skipping download')
        pkl_file = list(dest_path.glob('*'))[0]
        return pkl_file

    dest_path.mkdir()
    if 'drive.google.com' in url:
        downloaded_file = gdown.download(url, output=str(dest_path/'model_file'))
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
        downloaded_file.unlink()
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


def check_resolution(results_dir, filename):
    
    images = Path(results_dir).rglob('*.png')
    image = Image.open(list(images)[0])
    return image.size
    
def main(selected=None):
    
    with open(model_data_file) as model_file:
        reader = json.load(model_file)
        for model in reader:

            if selected and not model["name"] == selected:
                continue

            image_name = images_dir/(model["name"] + '.jpg')
            mixing_name = images_dir/(model["name"] + '_mixing.jpg')
            movie_name = movies_dir/(model["name"] + '.mp4')
            model_location = models_dir/model["name"]

            if not os.path.exists(image_name):
                pickle_location = download(model['download_url'], model_location)

                run_network(pickle_location, temp_outputs)
                draw_figure(temp_outputs, image_name)
                clean_up(temp_outputs)
            else:
                print(f'{image_name} already exists.')

            if not os.path.exists(mixing_name):
                pickle_location = str(list(model_location.glob('*'))[0])
                resolution = parse_resolution(model["resolution"])
                run_style_mixing(pickle_location, temp_outputs, resolution)
                filename = Path(temp_outputs)/"00000-style-mixing-example/grid.png"
                im = Image.open(filename)
                im.save(mixing_name)
                clean_up(temp_outputs)
            else:
                print(f'{mixing_name} already exists.')

            if not os.path.exists(movie_name):
                pickle_location = str(list(model_location.glob('*'))[0])
                temp_movie = temp_outputs.with_suffix(".mp4")
                run_noise_loop(pickle_location, temp_movie)
                shutil.copyfile(temp_movie, movie_name)
                clean_up(temp_outputs)
            else:
                print(f'{movie_name} already exists.')

import sys
if __name__ == "__main__":
    if len(sys.argv) > 1:
        selected = sys.argv[1]
    else:
        selected = None
    try:
        main(selected)
    except Exception as e:
        print(e)
        clean_up(temp_outputs)