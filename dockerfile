# Pull base image
FROM python:3.14-slim

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Accept UID/GID as build-time arguments
ARG UID=1000
ARG GID=1000

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Create a group and user matching the host's UID/GID, then hand over ownership
RUN groupadd -g ${GID} appgroup && \
    useradd -u ${UID} -g appgroup -m -s /bin/bash appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]