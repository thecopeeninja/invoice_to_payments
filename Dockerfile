# Step 1: Use an official, lightweight Python base image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy only the requirements file first to leverage Docker's build cache
COPY requirements.txt .

# Step 4: Install the Python dependencies
# Using --no-cache-dir reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of your project's code into the container
# Files listed in .dockerignore (Step 2) will be excluded
COPY . .

# Step 6: Define the default command to run when the container starts
# This command is taken from your README.md
CMD ["python", "-m", "src.matcher", \
     "--invoices", "data/invoices.csv", \
     "--payments", "data/payments.csv", \
     "--out", "out/"]