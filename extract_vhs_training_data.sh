#!/bin/bash
SOURCE_DIR="/home/weirdsoul/Videos/Videobearbeitung/SuperRes test data"
# For direct upscaling
#TARGET_DIR="/media/bulk_data/superres/training/paired_vcr"
# For downscaling.
TARGET_DIR="/media/bulk_data/superres/training/paired_vcr_ds"
CAPTURE_FPS=10
CAPTURE_DURATION=509

# Testing locally
#SOURCE_DIR="/Users/weirdsoul/Movies"
#TARGET_DIR="/Users/weirdsoul/coding/superres/paired_vcr"
#CAPTURE_FPS=1
#CAPTURE_DURATION=10

# For direct upscaling training
#PREPROCESSING_HQ=crop=1408:1080:16:0,scale=1408:1152
# For downscaling
PREPROCESSING_HQ=crop=1408:1080:16:0,scale=352:288
PREPROCESSING_LQ=scale=352:288

# Testing alignment
#PREPROCESSING_LQ=scale=1408:1152

rm -r "${TARGET_DIR}/hq"
rm -r "${TARGET_DIR}/lq"
mkdir -p "${TARGET_DIR}/hq"
mkdir -p "${TARGET_DIR}/lq"

# For direct upscaling
# HQ=hq
# LQ=lq
# For downscaling. We swap hq and lq
HQ=lq
LQ=hq

ffmpeg -t "${CAPTURE_DURATION}" -i "$SOURCE_DIR/high_quality.mp4" -r "${CAPTURE_FPS}" -vf "${PREPROCESSING_HQ}" "${TARGET_DIR}/${HQ}/image-%3d.png"
ffmpeg -t "${CAPTURE_DURATION}" -ss 00:15.0 -i "$SOURCE_DIR/low_quality.mkv" -r "${CAPTURE_FPS}" -vf "${PREPROCESSING_LQ}" "${TARGET_DIR}/${LQ}/image-%3d.png"

# Generate metadata.
python3 ./scripts/generate_meta_info_pairdata.py --input "${TARGET_DIR}/hq" "${TARGET_DIR}/lq" --root "${TARGET_DIR}" "${TARGET_DIR}" --meta_info "${TARGET_DIR}/paired_vcr.txt"

