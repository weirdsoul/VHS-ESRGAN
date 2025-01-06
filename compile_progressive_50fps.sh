#!/bin/bash
source ./config.sh
ffmpeg -framerate 25 -i /media/bulk_data/superres/results/frame%08d_top_out.png -framerate 25 -i /media/bulk_data/superres/results/frame%08d_bottom_out.png -filter_complex "[1:v] setpts=PTS+TB/2[bottom];[0:v][bottom] interleave" -ss "${offset}" -t "${duration}" -i "${source_video}" -c:v libx265 -r 50 /media/bulk_data/superres/output_videos/interlace_test.mp4

