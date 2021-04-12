ARG BASE_IMAGE

FROM ${BASE_IMAGE} as dev

WORKDIR /app
COPY . .
# lint check
RUN flake8 --statistics --verbose
# prepare local dev environment, for tests execution
RUN pip install -e .


FROM dev as build

# build egg
RUN python setup.py bdist_wheel


# ideally use ROOT_IMAGE but it's not yet doable in dmake
# => manually force root image here
FROM python:2.7 as runtime-py2

WORKDIR /app
# don't copy egg there: use universal egg from `build-egg` service at runtime
# prepare egg test: demo.py
COPY --from=build /app/demo.py /app/


# ideally use ROOT_IMAGE but it's not yet doable in dmake
# => manually force root image here
FROM python:3.6 as runtime-py3

WORKDIR /app
# don't copy egg there: use universal egg from `build-egg` service at runtime
# prepare egg test: demo.py
COPY --from=build /app/demo.py /app/
