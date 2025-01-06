#!/bin/bash
source ./config.sh
rm -r /media/bulk_data/superres/interlaced_input
mkdir /media/bulk_data/superres/interlaced_input
PREPROCESSING=crop=704:280:0:0,scale=352:280
#PREPROCESSING=crop=704:280:0:0,scale=352:280,colorcorrect=analyze=median
#PREPROCESSING=crop=704:280:0:0,scale=352:280,frei0r=balanc0r:#b1d0fbff
ffmpeg -i "${source_video}" -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 -ss "${offset}" -t "${duration}" -vf "field=top,${PREPROCESSING}" -pix_fmt rgb24 /media/bulk_data/superres/interlaced_input/frame%08d_top.png
ffmpeg -i "${source_video}" -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 -ss "${offset}" -t "${duration}" -vf "field=bottom,${PREPROCESSING}" -pix_fmt rgb24 /media/bulk_data/superres/interlaced_input/frame%08d_bottom.png
