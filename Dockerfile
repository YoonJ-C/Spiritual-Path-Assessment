# Use the official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY example.py /app/
COPY index.html /app/templates/index.html

# Copy your dependency file if it exists (optional)
# If not, we’ll create one on the fly
RUN echo "Flask==3.0.3\npython-dotenv\nTogether==0.2.8" > requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Set environment variables
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Start the Flask app
CMD ["python", "example.py"]
