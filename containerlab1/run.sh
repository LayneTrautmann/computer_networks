#!/bin/bash
# Deploy ContainerLab 1 
sudo clab deploy -t frrlab.clab.yml
./set-host-ifs.sh
