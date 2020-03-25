FROM kbase/sdkbase2:python
LABEL maintainer=dlagoa@anl.gov
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

#RUN apt-get update
#RUN apt-get install wget
#RUN apt-get -y install ncbi-blast+ #control version

#RUN pip install --upgrade pip
#RUN pip install cobrakbase
#RUN pip install networkx

# -----------------------------------------

#COPY ./ /kb/module

#RUN chmod -R a+rw /kb/module
RUN echo "no cache"
RUN mkdir -p /kb/module/opt
RUN mkdir -p /opt/jdk
RUN mkdir -p /opt/transyt
RUN mkdir -p /opt/neo4j
RUN mkdir /workdir

#WORKDIR /kb/module

# ------------ USING GIT LFS ---------------

#RUN tar -xf /kb/module/data/workdir.tar.gz -C /

#RUN mv /kb/module/transyt.jar /opt/transyt

#RUN tar -xf /kb/module/neo4j-community-4.0.1-unix.tar.gz -C /opt/neo4j
#RUN tar -xf /kb/module/data/data.tar.gz -C /opt/neo4j/neo4j-community-4.0.1

#RUN mv /kb/module/data/neo4j.conf /opt/neo4j/neo4j-community-4.0.1/conf/

#RUN tar -xf /kb/module/jdk-11.0.1_linux-x64_bin.tar.gz -C /opt/jdk

# ------------- USING OTHER SYSTEM ----------------

#WORKDIR /kb/module/opt
#RUN wget -q http://bioseed.mcs.anl.gov/~fxliu/kbase_build/jdk-11.0.1_linux-x64_bin.tar.gz
#RUN wget -q  http://bioseed.mcs.anl.gov/~fxliu/kbase_build/transyt_0.0.1.zip

#RUN tar -xf /kb/module/opt/jdk-11.0.1_linux-x64_bin.tar.gz -C /opt/jdk
#RUN tar -xf /kb/module/opt/ncbi-blast-2.8.1+-x64-linux.tar.gz -C /opt/blast
#RUN unzip transyt_0.0.1.zip -d /kb/module/data

# ---------------------------------------------

#WORKDIR /kb/module

RUN make all

EXPOSE 7474
EXPOSE 7687

#ENV JAVA_HOME=/opt/jdk/jdk-11.0.1
#ENV PATH="/opt/blast/ncbi-blast-2.8.1+/bin:${PATH}"

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
