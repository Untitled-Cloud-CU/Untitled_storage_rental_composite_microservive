# cloud_composite

This is the repo for team Untitled's Composite Microservice

## Before Starting

### Run Database
```bash
docker-compose up -d 
```

### Run Location Microservice
```bash
docker-compose up --build
```

### Run User Microservice
```bash
uvicorn app.main:app --reload --port 8001
```

## Run Composite Microservice
```bash
uvicorn main:app --reload --port 8002
```