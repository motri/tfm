#!/bin/bash
echo "Starting Munge..."
service munge start

echo "Starting SSH..."
service ssh start

echo "Starting Slurm Daemon (slurmd)..."
service slurmd start

echo "Compute node running. Tailing slurmd log..."
tail -f /var/log/slurmd.log