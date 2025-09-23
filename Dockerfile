# Forçar plataforma x86_64 para compatibilidade com Linux host
FROM --platform=linux/amd64 python:3.13-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os arquivos do projeto
COPY . .

# Expor porta interna do FastAPI
EXPOSE 8000

# Rodar Uvicorn em modo produção
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
