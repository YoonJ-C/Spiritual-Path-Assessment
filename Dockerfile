FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Install Flask and additional dependencies
RUN pip install flask gunicorn pymupdf tiktoken

# Create tmp directory for user data storage
RUN mkdir -p /tmp

# Expose default port
EXPOSE 7860

# Run with Gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:7860", "app:app"]
