from pathlib import Path

import imageio
import numpy as np
from tqdm import tqdm
from PIL import Image

def make_movie(sides=None):
    video_dir = Path("movies")
    videos = list(video_dir.glob("*.mp4"))
    output_file = Path("tiled.mp4")
    n_frames = 300
    tile_size = 128

    num_videos = len(videos)
    if not sides:
        one_side = int(np.ceil(np.sqrt(num_videos)))
        sides = (one_side, one_side)


    w = imageio.get_writer(output_file, 
                        format='FFMPEG', 
                        mode='I', 
                        fps=25,
                        codec='libx264',
                        pixelformat='yuv420p')

    readers = [imageio.get_reader(vid_file) for vid_file in videos]

    for frame in tqdm(range(n_frames)):

        canvas = Image.new('RGB', (tile_size*sides[0], tile_size*sides[1]))

        for idx, reader in enumerate(readers):
            
            im = reader.get_next_data()

            im = Image.fromarray(im)
            im = im.resize((tile_size, tile_size))
            pos = np.unravel_index(idx, sides)
            pixel_pos = [int(np.floor(x*tile_size)) for x in pos]
            canvas.paste(im, pixel_pos)

        w.append_data(np.array(canvas))

    w.close()

if __name__ == "__main__":
    make_movie((4, 5))