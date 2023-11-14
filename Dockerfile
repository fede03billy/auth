# Use the latest official Python image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["gunicorn", "--preload", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

