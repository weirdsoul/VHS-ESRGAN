#!/bin/bash
sudo nvidia-smi -pl $1
nvidia-smi -q -d POWER
