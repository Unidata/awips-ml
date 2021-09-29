#!/bin/bash
source /root/.bashrc
cd scripts
conda activate grpc_env
python edex_container_server.py edex_container
