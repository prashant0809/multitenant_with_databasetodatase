# multitenant_with_databasetodatase
multitenant Architecture Flow

This project demonstrates a scalable **multi-tenant architecture** where each tenant (Organiations) has its own isolated **PostgreSQL database**, ensuring complete data separation and security. The backend is built using **FastAPI**, a modern, fast web framework for building APIs with Python.

## Key Features

- Multi-tenancy with **database-to-database isolation**
- Dynamic database switching based on tenant
- RESTful API using **FastAPI**
- Organized project structure for scalability
- Uses `uvicorn` for running the development server
- Requirements managed with `requirements.txt`
- Simple onboarding of new tenants

You can clone fromm here
first step:
git clone https://github.com/prashant0809/multitenant_with_databasetodatase.git

then you can create virtual env

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate


# install the Dependencies 
pip install -r requirements.txt

# run the application

uvicorn main:app --reload



![image](https://github.com/user-attachments/assets/f52705c0-467a-4ca7-a19e-cb015a039510)




you can see in the image i have creted more then 10 databases for the organiations with the this application.

Thanks.


I am adding dockor file confugiration here.

# Dockerfile

FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


#### docker-compose.yml


version: "3.9"

services:
  fastapi:
    build: .
    container_name: fastapi-app
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:admin@db:5433/master_db
  db:
    image: postgres:14
    container_name: postgres-db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: admin
      POSTGRES_DB: master_db
    ports:
      - "5433:5433"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:










