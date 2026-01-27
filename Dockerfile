FROM python:3.14-alpine3.23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

# Copy dependency files AND files needed by build backend
COPY pyproject.toml uv.lock README.md ./
COPY mebox/ ./mebox/
COPY wiki/ ./wiki/

RUN uv sync --frozen --no-cache

# Copy the rest
COPY . .

# Expose the port the app runs on
EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=mebox.settings

# Command to run the application in development mode
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
