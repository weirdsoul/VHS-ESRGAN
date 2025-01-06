#!/bin/bash
source ./config.sh
rm /media/bulk_data/superres/interlaced_input/*
ffmpeg -i "${source_video}" -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 -ss "${offset}" -t "${duration}" -vf scale=352:576,field=top /media/bulk_data/superres/interlaced_input/frame%08d_top.png
ffmpeg -i "${source_video}" -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 -ss "${offset}" -t "${duration}" -vf scale=352:576,field=bottom /media/bulk_data/superres/interlaced_input/frame%08d_bottom.png
