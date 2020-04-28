FROM tensorflow/tensorflow:1.15.0-gpu-py3-jupyter

RUN pip install scipy==1.3.3
RUN pip install requests==2.22.0
RUN pip install Pillow==6.2.1

RUN apt-get update --fix-missing && apt-get install -y git wget
RUN mkdir /working
VOLUME /working

RUN mkdir /code
WORKDIR /code
RUN git clone https://github.com/NVlabs/stylegan2.git
WORKDIR /code/stylegan2

CMD /bin/bash