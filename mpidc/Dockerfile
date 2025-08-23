# Use an official Python runtime as a parent image
FROM python:3.11.5-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies before running pip install
RUN apk add --no-cache \
    postgresql-dev \
    python3-dev \
    gcc \
    musl-dev

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME=world

# Run app.py when the container launches
#CMD ["sh", "-c", "python3 manage.py runserver 0.0.0.0:8000 && python3 manage.py migrate"]

# Run the migrate command and then start the server
CMD ["sh", "-c", "python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]

