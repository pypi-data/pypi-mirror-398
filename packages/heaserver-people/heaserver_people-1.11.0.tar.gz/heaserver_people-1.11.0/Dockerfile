#
# A simple Dockerfile to quickly build a docker image for testing. It is not at all secure, so never upload a docker
# image built this way to an image repo! Use the Dockerfiles in the HEA Main project to create distribution-worthy
# images.
#
# This Dockerfile accepts one arguments:
#     SOURCE: path to a tarball (tar.gz or tgz file; required).
#
# Run as follows:
#     docker build --build-arg SOURCE="dist/<tarball>" [--build-arg INDEX_URL="<url>"] -t registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-people:latest .
#
# To create a tarball, run the following:
#     python setup.py clean --all sdist bdist_wheel
#
# Run the image from the HEA Main project with the following command (see the top of the docker-compose-dev.yml file
# for instructions):
#     docker-compose -f ./docker-compose-dev.yml up
#

FROM registry.gitlab.com/huntsman-cancer-institute/risr/hea/hea-python-base:3.12.9

ARG SOURCE
ARG INDEX_URL=https://pypi.python.org/simple

RUN apt-get update && \
    apt-get install --no-install-recommends -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home app
WORKDIR /home/app
COPY $SOURCE .
RUN mkdir sdist
RUN tar xvzf $(ls *.tgz *.tar.gz) --directory sdist --strip-components 1
COPY requirements_dev.txt sdist
WORKDIR /home/app/sdist
RUN pip install -i "$INDEX_URL" -r requirements_dev.txt
RUN pytest -n auto
RUN mypy
WORKDIR /home/app
COPY docker-entrypoint.sh .
RUN dos2unix ./docker-entrypoint.sh
USER app
ENTRYPOINT [ "sh", "docker-entrypoint.sh" ]
EXPOSE 8080
