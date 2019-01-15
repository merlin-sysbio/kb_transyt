FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update


# -----------------------------------------

COPY ./ /kb/module

RUN mkdir -p /opt/jdk
RUN mkdir -p /opt/blast
RUN tar -xf /kb/module/opt/jdk-11.0.1_linux-x64_bin.tar.gz -C /opt/jdk
RUN tar -xf /kb/module/opt/ncbi-blast-2.8.1+-x64-linux.tar.gz -C /opt/blast

RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN pip install cobrakbase

WORKDIR /kb/module

RUN make all

ENV PATH="/opt/blast/ncbi-blast-2.8.1+/bin:${PATH}"

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
