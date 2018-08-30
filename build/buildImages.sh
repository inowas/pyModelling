#!/usr/bin/env bash

# Build the main image which runs the main services
docker build . --tag inowas/pymodelling:latest

# Build the Optimization Image
docker build ./Optimization/Optimization --tag inowas/pymodelling:optimization

# Build the Simulation Image
docker build ./Optimization/Simulation --tag inowas/pymodelling:simulation

# Build the GeoProcessing Image
docker build ./InowasGeoProcessing --tag inowas/pymodelling:geoprocessing
