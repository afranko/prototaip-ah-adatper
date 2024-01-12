# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12

RUN pip install --upgrade pip

# Install production dependencies
COPY requirements.txt /tmp/requirements.txt
COPY client-library-python /tmp/client-library-python
RUN pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

RUN python -m build /tmp/client-library-python
RUN python -m pip install /tmp/client-library-python/dist/arrowhead-client-0.5.0a0.tar.gz

EXPOSE 9556

# The commands for your application...  