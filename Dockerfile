FROM alpine:latest

# Install necessary packages and build dependencies
RUN apk update && apk add --no-cache ffmpeg bash python3 py3-pip gcc musl-dev python3-dev libffi-dev openssl-dev

# Create a virtual environment and activate it
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip, setuptools, and wheel within the virtual environment
RUN pip install --upgrade pip setuptools wheel

# Set the working directory
WORKDIR /home/youtube_sampler

# Copy requirements.txt and install dependencies within the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app /home/youtube_sampler

# Command to run the application using gunicorn
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:420", "-t", "90"]
