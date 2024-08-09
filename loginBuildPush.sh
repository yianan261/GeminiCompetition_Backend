#!/bin/bash
gcloud auth login
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://us-west2-docker.pkg.dev
sh buildPush.sh