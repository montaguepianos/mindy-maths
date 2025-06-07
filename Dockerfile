# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app
COPY . .

# Expose the port
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]
