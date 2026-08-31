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

# Build-time-only dummy values so settings can import for collectstatic.
# Real values are injected by PaaS at container start.
RUN DJANGO_SETTINGS_MODULE=django_project.settings.production \
    SECRET_KEY=build-time-placeholder \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://placeholder:placeholder@localhost:5432/placeholder \
    python manage.py collectstatic --noinput

# Create a group and user matching the host's UID/GID, then hand over ownership
RUN groupadd -g ${GID} appgroup && \
    useradd -u ${UID} -g appgroup -m -s /bin/bash appuser && \
    chown -R appuser:appgroup /app

# Copy entrypoint and make it executable with chmod
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to the non-root user
USER appuser

EXPOSE 8000

CMD ["/entrypoint.sh"]