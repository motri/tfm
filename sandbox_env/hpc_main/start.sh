#!/bin/bash
echo "Starting Munge..."
sudo service munge start

echo "Starting SSH..."
service ssh start

echo "Starting Slurm Controller (slurmctld)..."
service slurmctld start

echo "Master node running. Tailing slurmctld log..."
tail -f /var/log/slurmctld.log