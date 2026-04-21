#!/bin/bash
cd "$(dirname "$0")"
sudo clab destroy -t frrlab-backup.clab.yml
