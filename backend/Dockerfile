# Use the correct, stable Python version for our application
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application's code and templates into the container
COPY ./app /code/app
COPY ./main.py /code/main.py
COPY ./templates /code/templates # <-- THE CRITICAL FIX

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Use gunicorn to run the Uvicorn worker class
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8080"]