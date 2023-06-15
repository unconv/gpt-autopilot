# Joke Generator

This is a web application that tells a joke when you press a button.

## Running the service with Docker

1. Build the Docker image
   ```
   docker build -t joke-generator .
   ```
2. Run the Docker container
   ```
   docker run -p 5000:5000 joke-generator
   ```
