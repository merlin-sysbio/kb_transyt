FROM kbase/sdkbase2:python
LABEL maintainer=dlagoa@anl.gov
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

RUN apt-get update
RUN apt-get install wget
RUN apt-get -y install ncbi-blast+ #control version

RUN pip install --upgrade pip
RUN pip install cobrakbase
RUN pip install networkx

# -----------------------------------------

COPY ./ /kb/module

RUN chmod -R a+rw /kb/module

RUN mkdir -p /kb/module/opt
RUN mkdir -p /opt/jdk
RUN mkdir -p /opt/transyt
RUN mkdir -p /opt/neo4j
RUN mkdir /downloads

WORKDIR downloads

# ------------ Downloads ---------------

RUN wget -q http://bioseed.mcs.anl.gov/~fxliu/kbase_build/jdk-11.0.1_linux-x64_bin.tar.gz
RUN tar -xf jdk-11.0.1_linux-x64_bin.tar.gz -C /opt/jdk

RUN wget -q https://neo4j.com/artifact.php?name=neo4j-community-4.0.2-unix.tar.gz -O neo4j-community-4.0.2-unix.tar.gz
RUN tar -xf neo4j-community-4.0.2-unix.tar.gz -C /opt/neo4j

RUN wget -q https://merlin-sysbio.org/data/transyt/scraper/workdir.tar.gz
RUN tar -xf workdir.tar.gz -C /

RUN wget -q https://merlin-sysbio.org/data/transyt/database/data.tar.gz
RUN tar -xf data.tar.gz -C /opt/neo4j/neo4j-community-4.0.2

WORKDIR /opt/transyt

RUN wget -q https://merlin-sysbio.org/data/transyt/transyt.jar

# ---------------------------------------------

RUN rm -r /downloads

RUN mv /kb/module/conf/neo4j.conf /opt/neo4j/neo4j-community-4.0.2/conf/

WORKDIR /kb/module

RUN make all

EXPOSE 7474
EXPOSE 7687

ENV JAVA_HOME=/opt/jdk/jdk-11.0.1

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
