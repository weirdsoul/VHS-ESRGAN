#!/bin/bash
SOURCE_DIR="/home/weirdsoul/Videos/Videobearbeitung/SuperRes test data"
TARGET_DIR="/media/bulk_data/superres/training/paired_vcr_val"
CAPTURE_FPS=1
CAPTURE_DURATION=509
PREPROCESSING_HQ=crop=1408:1070:16:10,scale=1408:1152
PREPROCESSING_LQ=scale=352:288

rm -r /media/bulk_data/superres/training/paired_vcr_val/hq
rm -r /media/bulk_data/superres/training/paired_vcr_val/lq
mkdir -p /media/bulk_data/superres/training/paired_vcr_val/hq
mkdir -p /media/bulk_data/superres/training/paired_vcr_val/lq

ffmpeg -t "${CAPTURE_DURATION}" -ss 00:00.2 -i "$SOURCE_DIR/high_quality.mp4" -r "${CAPTURE_FPS}" -vf "${PREPROCESSING_HQ}" "${TARGET_DIR}/hq/image-%3d.png"
ffmpeg -t "${CAPTURE_DURATION}" -ss 00:15.2 -i "$SOURCE_DIR/low_quality.mkv" -r "${CAPTURE_FPS}" -vf "${PREPROCESSING_LQ}" "${TARGET_DIR}/lq/image-%3d.png"


