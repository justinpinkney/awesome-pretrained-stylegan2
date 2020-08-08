# iterate over lines in csv
# download pickle
# setup docker image
# run container to generate 9 images
# Compile images into montage

import json
import os
filename = 'models.json'
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
movies_dir = Path('movies')
models_dir = Path('models')

for directory in (images_dir, models_dir, movies_dir):
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


def run_noise_loop(pkl_path, output_dir, clean_up=False):
    working_dir = '/working'
    image_name = 'awesome-stylegan2-dv'
    seed = '0'


    if clean_up:
        cmd = ['rm', '-rf', working_dir + '/' + str(output_dir),]
    else:
        cmd = ['python', 'run_generator.py', 
                'generate-latent-walk', 
                '--network', working_dir + '/' + str(pkl_path),
                '--walk-type', 'noiseloop',
                '--frames', '300',
                '--seeds', '0',
                '--truncation-psi', '0.5',
                '--diameter', '1.0',
                '--start_seed', seed,
                '--result-dir', working_dir + '/' + str(output_dir),]

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

def make_movie(input_dir, output_file):
   
    cmd = ['ffmpeg',
            '-r', '24',
            '-i',  str(input_dir) + '/00000-generate-latent-walk/frame%05d.png',
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=256:256',
            str(output_file)]

    subprocess.run(cmd)

if __name__ == "__main__":

    temp_outputs = Path('temp_outputs')
    
    with open(filename) as model_file:
        reader = json.load(model_file)
        for model in reader:
            image_name = images_dir/(model["name"] + '.jpg')
            movie_name = movies_dir/(model["name"] + '.mp4')
            model_location = models_dir/model["name"]

            if not os.path.exists(image_name):
                pickle_location = download(model['download_url'], model_location)

                run_network(pickle_location, temp_outputs)
                draw_figure(temp_outputs, image_name)
                run_network(pickle_location, temp_outputs, clean_up=True)
            else:
                print(f'{image_name} already exists.')

            if not os.path.exists(movie_name):
                pickle_location = str(list(model_location.glob('*'))[0])
                run_noise_loop(pickle_location, temp_outputs)
                make_movie(temp_outputs, movie_name)
                run_noise_loop(pickle_location, temp_outputs, clean_up=True)
            else:
                print(f'{movie_name} already exists.')

