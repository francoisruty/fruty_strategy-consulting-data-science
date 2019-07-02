FROM python:2.7

RUN pip install pandas
RUN pip install matplotlib
RUN pip install scipy
RUN pip install psycopg2
RUN pip install xlrd==1.0.0

WORKDIR /workspace
