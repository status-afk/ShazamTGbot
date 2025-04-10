# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file (if you have one) and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot's source code to the container
COPY . .

# Command to run your bot
CMD ["python", "bot.py"]