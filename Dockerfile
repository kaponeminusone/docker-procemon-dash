
# Base image
FROM python:3.9

ENV DOCKER_BUILDKIT=1

# Instala Tex Live para pdflatex
RUN apt-get update && apt-get install -y texlive-latex-base
RUN python -m venv .venv

COPY . .

RUN bin/bash -c "source .venv/bin/activate"
RUN pip install -r requirements.txt

ENV PORT=8000
# Exponer el puerto de FastAPI
EXPOSE 8000

# Inicia la aplicación usando uvicorn
CMD ["uvicorn", "app.main:app","--host", "0.0.0.0", "--port", "8000"]
