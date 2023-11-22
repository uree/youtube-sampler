# Python
FROM alpine:latest
RUN apk update && apk add ffmpeg
RUN apk add --no-cache python3 py3-pip
RUN pip install --upgrade pip setuptools wheel

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install the dependencies
RUN pip install -r requirements.txt

# Run the command to start gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:420", "-t 90"]
