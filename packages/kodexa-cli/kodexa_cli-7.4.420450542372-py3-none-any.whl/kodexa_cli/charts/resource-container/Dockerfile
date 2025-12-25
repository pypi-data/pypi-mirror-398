# We ship models and indexes with the CLI, this is the Dockerfile
# it will be the image used by the helm chart to load the models
# and indexes into the k8s cluster, so they can be picked up and
# installed by the Kodexa Server

FROM nginxinc/nginx-unprivileged:stable-alpine-slim

# We will copy all the model metadata and the index.json file
# into the Minio instance

ADD . /usr/share/nginx/html/.
