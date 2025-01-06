#!/bin/bash
# rm /media/bulk_data/superres/results/*
# python inference_realesrgan.py -n RealESRGAN_x2plus -i /media/bulk_data/superres/interlaced_input -o /media/bulk_data/superres/results --face_enhance
#MODEL=RealESRGAN_x4plus
MODEL=vhs
rm /home/weirdsoul/coding/Real-ESRGAN/weights/net_g_link.pth
mkdir -p /media/bulk_data/superres/results
python inference_realesrgan.py -dn 0 -n "${MODEL}" -i /media/bulk_data/superres/interlaced_input -o /media/bulk_data/superres/results
