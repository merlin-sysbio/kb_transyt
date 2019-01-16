FROM kbase/sdkbase2:python
LABEL maintainer=fliu@anl.gov
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update


# -----------------------------------------

COPY ./ /kb/module

RUN apt-get install wget
RUN pip install --upgrade pip

RUN mkdir -p /kb/module/opt
WORKDIR /kb/module/opt
RUN wget -q http://bioseed.mcs.anl.gov/~fxliu/kbase_build/jdk-11.0.1_linux-x64_bin.tar.gz
RUN wget -q http://bioseed.mcs.anl.gov/~fxliu/kbase_build/ncbi-blast-2.8.1+-x64-linux.tar.gz
RUN wget -q  http://bioseed.mcs.anl.gov/~fxliu/kbase_build/transyt_0.0.1.zip
RUN mkdir -p /opt/jdk
RUN mkdir -p /opt/blast
RUN tar -xf /kb/module/opt/jdk-11.0.1_linux-x64_bin.tar.gz -C /opt/jdk
RUN tar -xf /kb/module/opt/ncbi-blast-2.8.1+-x64-linux.tar.gz -C /opt/blast
RUN unzip transyt_0.0.1.zip -d /kb/module/data

RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN pip install cobrakbase

WORKDIR /kb/module

RUN rm -Rf /kb/module/opt

RUN make all

ENV PATH="/opt/blast/ncbi-blast-2.8.1+/bin:${PATH}"

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
