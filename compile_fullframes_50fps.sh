#!/bin/bash
source ./config.sh
frame_input=/media/bulk_data/superres/results/frame%08d_out.png
#frame_input=/media/bulk_data/superres/interlaced_input/frame%08d.png
ffmpeg -framerate 50 -i "${frame_input}" -ss "${offset}" -t "${duration}" -i "${source_video}" -vf scale=1408:1120 -c:v libx264 -crf 17 -pix_fmt yuv420p -r 50 -map 0:v -map 1:a /media/bulk_data/superres/output_videos/interlace_test.mp4

