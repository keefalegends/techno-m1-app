# Techno ML App · 

Mini project Flask + Docker + EKS untuk simulasi **Amazon Rekognition** image label detection.

---

## Struktur Folder

```
techno-ml-app/
├── app.py                          # Flask application (port 2000)
├── Dockerfile                      # Python 3.13-slim base image
├── requirements.txt
├── deployment/
│   ├── deploy.yaml                 # K8s Deployment (2 replicas/pods)
│   └── service.yaml                # K8s Service (LoadBalancer → port 80)
└── .github/
    └── workflows/
        └── lks-technocicd.yml      # GitHub Actions (3 jobs)
```

---

## Quick Start (Lokal / Demo)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run locally (port 2000)
python app.py

# 3. Buka browser → http://localhost:2000
```

---

## Build & Push Docker ke ECR

```bash
# Login ke ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t techno-ecr-city-yourname .

# Tag
docker tag techno-ecr-city-yourname:latest \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/techno-ecr-city-yourname:latest

# Push
docker push \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/techno-ecr-city-yourname:latest
```

---

## Deploy ke EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --name techno-eks-city-yourname --region us-east-1

# Edit deploy.yaml → ganti <ACCOUNT_ID> dengan account ID kamu

# Apply manifests
kubectl apply -f deployment/deploy.yaml
kubectl apply -f deployment/service.yaml

# Cek pod berjalan (harus ada 2 pods)
kubectl get pods

# Ambil URL Load Balancer
kubectl get svc techno-ml-service
```

---

## GitHub Actions (CI/CD)

Set secrets di GitHub repo → Settings → Secrets:

| Secret                  | Value                              |
|-------------------------|------------------------------------|
| `AWS_ACCESS_KEY_ID`     | Dari Learner Lab Academy           |
| `AWS_SECRET_ACCESS_KEY` | Dari Learner Lab Academy           |
| `AWS_SESSION_TOKEN`     | Dari Learner Lab Academy           |

Trigger pipeline:
```bash
git add .
git commit -m "feat: deploy versi baru"
git tag v1.0.0
git push origin main --tags
```

GitHub Actions akan menjalankan **3 jobs**:
1. ✅ **Build and Push to ECR**
2. ✅ **Configure kubeconfig for EKS**
3. ✅ **Deploy to EKS**

---

## Environment Variables (App)

| Variable         | Default                          | Keterangan              |
|------------------|----------------------------------|-------------------------|
| `AWS_REGION`     | `us-east-1`                      | Region AWS              |
| `INPUT_BUCKET`   | `technoinput-city-yourname`      | S3 bucket upload        |
| `OUTPUT_BUCKET`  | `technooutput-city-yourname`     | S3 bucket hasil         |
| `DYNAMODB_TABLE` | `Tokens`                         | Tabel token DynamoDB    |
| `PORT`           | `2000`                           | Port aplikasi           |

---

## Flow Aplikasi

```
User → Load Balancer (port 80)
     → EKS Pod (port 2000)
     → Generate Token → DynamoDB (Tokens table)
     → Upload Image   → S3 (technoinput-...)
     → Rekognition    → detect_labels
     → Save Result    → S3 (technooutput-.../results/)
     → Response       → Frontend (label + confidence bar)
```
