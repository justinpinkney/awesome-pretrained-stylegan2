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
import sys
import tempfile
import traceback
from pathlib import Path

import gdown
import requests
from mega import Mega
from PIL import Image

model_data_file = 'models.json'

content_dir = Path('content')
models_dir = Path('models')

for directory in (content_dir, models_dir):
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


def run_network(pkl_path, output_dir, start_seed=0, end_seed=11, truncation=0.75):
    seeds = f"{start_seed}-{end_seed}"
    cmd = ['python', 'run_generator.py', 
        'generate-images',
        '--network', working_dir + '/' + str(pkl_path),
        '--seeds', seeds,
        '--truncation-psi', str(truncation),
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
        top_style = int(math.log(resolution[0]/16)/math.log(2))
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
    elements = res.split("x")
    try:
        resolution = [int(el) for el in elements]
    except ValueError:
        resolution = None
    
    return resolution


def download(url, dest_path):
    """Downloads a model file and saves to dest_path.
    Can deal with normal urls and google drive and mega"""
    print(f'Downloading {dest_path} model')
    
    if dest_path.exists():
        print(f'{dest_path} already exists, skipping download')
        return
        
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = Path(tmpdirname)
        if 'drive.google.com' in url:
            downloaded_file = gdown.download(url, output=str(tmpdirname/'model_file'))
        elif 'mega.nz' in url:
            mega = Mega()
            m = mega.login()
            downloaded_file = m.download_url(url, dest_path=str(tmpdirname))
        else:
            r = requests.get(url)
            downloaded_file = 'downloaded.pkl'
            with open(downloaded_file, 'wb') as f:
                f.write(r.content)

        downloaded_file = Path(downloaded_file)

        if downloaded_file.suffix == ".xz":  
            print(f'Downloaded file {downloaded_file} is .xz')
            pkl_file = tmpdirname/downloaded_file.stem
            with lzma.open(downloaded_file, 'rb') as in_file:
                with open(pkl_file, 'wb') as out:
                    out.write(in_file.read())
            downloaded_file.unlink()
            downloaded_file = pkl_file

        shutil.copyfile(downloaded_file, dest_path)

def draw_figure(results_dir, filename, rows=4, cols=3, out_size=256):
    
    canvas = Image.new('RGB', (out_size * cols, out_size*rows), 'white')
    images = Path(results_dir).rglob('*.png')
    images = iter(sorted(images))
    for row in range(rows):
        for col in range(cols):
            image = Image.open(next(images))
            image = image.resize((out_size, out_size), Image.ANTIALIAS)
            canvas.paste(image, (out_size*col, out_size*row))
    
    canvas.save(filename)


def check_resolution(results_dir):
    
    images = Path(results_dir).rglob('*.png')
    image = Image.open(list(images)[0])
    return image.size
    
def main(selected=None):
    
    with open(model_data_file) as model_file:
        reader = json.load(model_file)
        for model in reader:

            if selected and not model["name"] == selected:
                continue

            base_content_dir = content_dir/model["name"]
            base_content_dir.mkdir(exist_ok=True)
            image_name = base_content_dir/"samples.jpg"
            mixing_name = base_content_dir/"mixing.jpg"
            movie_name = base_content_dir/"interpolation.mp4"
            model_location = models_dir/(model["name"] + ".pkl")

            download(model['download_url'], model_location)

            resolution = parse_resolution(model["resolution"])
                
            if not os.path.exists(image_name):
                for idx, trunc in enumerate((0.25, 0.5, 0.75, 1)):
                    run_network(model_location, temp_outputs, 
                                start_seed=0+idx*3, end_seed=2+idx*3, 
                                truncation=trunc)
                draw_figure(temp_outputs, image_name)
                generated_resolution = check_resolution(temp_outputs)
                print(f"Found resolution {generated_resolution}")
                if resolution and any(x != y for x, y in zip(resolution, generated_resolution)):
                    raise ValueError(f"resolution was {generated_resolution} but label is {resolution}")
                clean_up(temp_outputs)
            else:
                print(f'{image_name} already exists.')

            if not os.path.exists(mixing_name):
                run_style_mixing(model_location, temp_outputs, resolution)
                filename = Path(temp_outputs)/"00000-style-mixing-example/grid.png"
                im = Image.open(filename)
                im.resize((5*256, 5*256))
                im.save(mixing_name)
                clean_up(temp_outputs)
            else:
                print(f'{mixing_name} already exists.')

            if not os.path.exists(movie_name):
                temp_movie = temp_outputs.with_suffix(".mp4")
                run_noise_loop(model_location, temp_movie)
                shutil.copyfile(temp_movie, movie_name)
                clean_up(temp_outputs)
            else:
                print(f'{movie_name} already exists.')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        selected = sys.argv[1]
    else:
        selected = None
    try:
        main(selected)
    except Exception as err:
        traceback.print_tb(err.__traceback__)
        clean_up(temp_outputs)
