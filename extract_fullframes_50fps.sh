#!/bin/bash
source ./config.sh
export LD_LIBRARY_PATH=%LD_LIBRARY_PATH%:/home/weirdsoul/ffmpeg_build/lib
rm -r /media/bulk_data/superres/interlaced_input
mkdir /media/bulk_data/superres/interlaced_input
input_file="devcr.avs"
# input_file=${source_video}
ffmpeg_bin=~/ffmpeg_build/bin/ffmpeg
# ffmpeg_bin=ffmpeg
${ffmpeg_bin} -i "${input_file}" -ss "${offset}" -t "${duration}" -vf "spp=5:10:0:1,crop=704:560:0:0,bwdif" -pix_fmt rgb24 /media/bulk_data/superres/interlaced_input/frame%08d.png
