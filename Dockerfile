# Use the official Python image as the base image
FROM python:alpine

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the program files into the container
COPY bgg.py .
COPY credentials.json .
COPY token.json .

# Set the command to run the program
CMD ["python", "-u", "bgg.py"]
