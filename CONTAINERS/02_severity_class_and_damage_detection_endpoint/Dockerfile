# Use the official Python 3.11 image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
#RUN apt apt-get update && apt-get install libgl1
RUN apt-get update
RUN apt-get -y install libgl1

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python3", "app.py"]