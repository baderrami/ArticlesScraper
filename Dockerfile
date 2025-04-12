# Use the official Python image with the necessary version
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory's files into the container
ADD . /app

# Install system-level dependencies required for Playwright and browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxi6 libxtst6 libcups2 libpangocairo-1.0-0 \
    libpangoft2-1.0-0 fontconfig libatspi2.0-0 libgtk-3-0 libgbm-dev \
    libopenjp2-7 unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright browsers
RUN pip install playwright && playwright install --with-deps

# Expose the Streamlit app's default port
EXPOSE 8501

# Define the default command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
