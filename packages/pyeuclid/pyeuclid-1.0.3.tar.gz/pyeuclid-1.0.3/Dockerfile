FROM python:3.11
RUN git clone https://github.com/zhaoyu-li/PyEuclid
# RUN mkdir /PyEuclid
# COPY ./ /PyEuclid
WORKDIR /PyEuclid
RUN pip install .
RUN tar -xvzf cache.tar.gz
CMD python test_single.py