FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Expose port 5003 (matches app.py)
EXPOSE 5003

# Run with Gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5003", "app:app"]