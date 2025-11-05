# Use the official Python image as the base image
FROM python:alpine

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the program files into the container
COPY bgg.py .

# Note: credentials.json and token.json should be provided via volume mounts
# or set GOOGLE_CREDENTIALS_FILE and GOOGLE_TOKEN_FILE environment variables
# to point to mounted files

# Set the command to run the program
CMD ["python", "-u", "bgg.py"]
