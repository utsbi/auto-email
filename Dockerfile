FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml first for better layer caching
COPY pyproject.toml ./

# Install dependencies using pip
RUN pip install --no-cache-dir -e.

# Copy the rest of the application
COPY . .

# Run the application
CMD ["python", "main.py"]