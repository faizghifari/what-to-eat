FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir python-dotenv supabase "fastapi[standard]"

COPY src ./

CMD ["fastapi", "run", "./profile.py", "--host", "0.0.0.0", "--port", "5000"]
