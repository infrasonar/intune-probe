FROM ghcr.io/infrasonar/python:3.12.9
ADD . /code
WORKDIR /code
RUN pip install --no-cache-dir -r requirements.txt
ENV MAX_PACKAGE_SIZE=1500
CMD ["python", "main.py"]
