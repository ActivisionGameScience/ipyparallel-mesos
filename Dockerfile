FROM usav1gam02:5000/conda3

RUN apt-get update && apt-get install gcc git supervisor -y

COPY conda.export /opt/conda.export
WORKDIR /opt

RUN conda create -n py3 --file conda.export -y

COPY requirements.txt /opt/requirements.txt
COPY install_req.sh /opt/install_req.sh
RUN chmod +x /opt/install_req.sh
RUN ./install_req.sh
#COPY ./marathon.json /
CMD ["/usr/bin/supervisord", "-c", "./supervisord.conf"]
EXPOSE 9991

ENV IPYTHONDIR=/opt/
COPY . /opt
