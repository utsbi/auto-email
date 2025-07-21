# Email Automation System

A serverless Python application that automatically processes Google Sheets form responses and sends personalized emails to new signups. Built with Google Cloud Run and Cloud Scheduler for reliable daily automation.

## 📋 Overview

This system monitors a Google Sheets form (SBI General Interest Form) for new responses and automatically sends emails to new signups. It runs daily at 9:00 AM Central Time using Google Cloud's serverless infrastructure.

### Key Features

- **Automated email processing** from Google Sheets form responses
- **Serverless architecture** using Google Cloud Run Jobs
- **Secure credential management** with Google Secret Manager
- **Scheduled execution** via Cloud Scheduler
- **Containerized deployment** with Docker
- **CI/CD pipeline** with GitHub Actions

## 🏗️ Architecture

```
Google Sheets ←→ Python Script ←→ Email Service (SMTP)
     ↓              ↓                    ↓
Secret Manager → Cloud Run Job ← Cloud Scheduler
     ↓              ↓
GitHub Actions → Container Registry
```

### Components

- **Google Sheets API**: Reads form responses and tracks email status
- **Google Cloud Run Jobs**: Hosts the containerized Python script
- **Google Cloud Scheduler**: Triggers daily execution at 9 AM CDT
- **Google Secret Manager**: Securely stores API credentials and email passwords
- **GitHub Actions**: Automated deployment pipeline

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Google Account with access to the target Google Sheet
- SMTP-enabled email account (Gmail with App Password recommended)

### Required APIs

Enable these APIs in your Google Cloud project:

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable drive.googleapis.com
```

## 🛠️ Setup Instructions

### 1. Clone and Configure

```bash
git clone 
cd email-automation-system
```

### 2. Google Cloud Setup

```bash
# Set your project
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Create service accounts
gcloud iam service-accounts create email-automation-sa \
  --display-name="Email Automation Cloud Run Job"

gcloud iam service-accounts create sheets-automation-sa \
  --display-name="Email Automation Sheets Access"

gcloud iam service-accounts create scheduler-sa \
  --display-name="Cloud Scheduler Service Account"
```

### 3. Configure Secrets

Store your credentials securely in Secret Manager:

```bash
# Email credentials
echo "your-email@gmail.com" | gcloud secrets create sender-email --data-file=-
echo "your-app-password" | gcloud secrets create google-app-password --data-file=-

# Google Sheets service account credentials
gcloud iam service-accounts keys create sheets-credentials.json \
  --iam-account=sheets-automation-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud secrets create SERVICE_ACCOUNT_FILE --data-file=sheets-credentials.json
```

### 4. Configure GitHub Repository

Set up repository secrets for automated deployment:

| Secret Name | Description |
|-------------|-------------|
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `GCP_SA_KEY` | GitHub Actions service account JSON key |
| `GCP_REGION` | Deployment region (e.g., us-central1) |
| `JOB_NAME` | Cloud Run job name |

### 5. Grant Permissions

```bash
# Grant necessary permissions
export EMAIL_SA="email-automation-sa@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$EMAIL_SA" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:scheduler-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 6. Share Google Sheet

Share your Google Sheet with the service account:
`sheets-automation-sa@your-project-id.iam.gserviceaccount.com` (Editor permissions)

## 📦 Deployment

### Automatic Deployment

Push changes to the `main` branch to trigger automatic deployment via GitHub Actions.

### Manual Deployment

```bash
# Deploy the Cloud Run job
gcloud run jobs create $JOB_NAME \
  --source . \
  --region us-central1 \
  --service-account $EMAIL_SA

# Create scheduler
gcloud scheduler jobs create http daily-email-automation \
  --location us-central1 \
  --schedule "0 9 * * *" \
  --time-zone "America/Chicago" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
  --http-method POST \
  --oauth-service-account-email "scheduler-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Set automatically |
| `GOOGLE_SHEET_NAME` | Name of the Google Sheet to monitor | "SBI General Interest Form (Responses)" |

### Secrets Required

- `SERVICE_ACCOUNT_FILE`: Google Sheets API credentials (JSON)
- `sender-email`: SMTP sender email address
- `google-app-password`: SMTP authentication password

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
gcloud logging tail "resource.type=cloud_run_job"

# Recent execution logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" --limit=50
```

### Monitor Scheduler

```bash
# Check scheduled jobs
gcloud scheduler jobs list --location us-central1

# View job status
gcloud scheduler jobs describe daily-email-automation --location us-central1
```

## 🧪 Testing

### Manual Testing

```bash
# Execute job manually
gcloud run jobs execute $JOB_NAME --region us-central1 --wait
```

### Test Scheduler

For a one-time test (runs 1 minute from now):

```bash
TARGET_TIME=$(TZ='America/Chicago' date -d '+1 minute' '+%M %H %d %m *')
gcloud scheduler jobs create http test-email-job-1min \
  --location us-central1 \
  --schedule "$TARGET_TIME" \
  --time-zone "America/Chicago" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
  --http-method POST \
  --oauth-service-account-email "scheduler-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

## 🔒 Security

- **Secret Management**: All credentials stored in Google Secret Manager
- **Least Privilege**: Service accounts have minimal required permissions
- **No Hardcoded Secrets**: Credentials never stored in code or containers
- **Audit Trail**: All API calls and job executions are logged

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -e .

# Set up local authentication
gcloud auth application-default login

# Run locally
python main.py
```

### Project Structure

```
├── .github/workflows/     # CI/CD pipeline
├── .gitignore            # Version control exclusions
├── .python-version        # Version of python used
├── Dockerfile             # Container configuration
├── EmailSignature.gif     # Logo gif email signature
├── README.md              # This file
├── main.py                 # Main application logic
├── pyproject.toml         # Python dependencies
└── uv.lock                # Lockfile for reproducible builds
```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `403: Project not found` | Verify project ID and authentication |
| `403: API not enabled` | Enable required Google APIs |
| `invalid_grant: account not found` | Recreate service account credentials |
| `Permission denied` | Check IAM permissions for service accounts |

### Debug Commands

```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$EMAIL_SA"

# Verify secrets exist
gcloud secrets list

# Test secret access
gcloud secrets versions access latest --secret SERVICE_ACCOUNT_FILE
```

## 📈 Maintenance

### Regular Tasks

- **Monitor execution logs** for errors or failures
- **Review email delivery rates** and success metrics
- **Update dependencies** in `pyproject.toml` periodically
- **Rotate service account keys** annually for security
- **Review and clean up** old Cloud Run revisions

### Cost Optimization

- Monitor Cloud Run execution time and memory usage
- Review Cloud Scheduler execution frequency if needed
- Clean up unused secrets and service accounts

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make changes and test thoroughly**
4. **Ensure all secrets and credentials are properly configured**
5. **Submit a pull request with detailed description**

### Code Standards

- Follow Python PEP 8 style guidelines
- Add logging for debugging and monitoring
- Update documentation for any configuration changes
- Test changes with manual job execution before deploying

## 📄 License

This project is internal to the company. All rights reserved.

**⚠️ Important**: This system handles email automation and personal data. Ensure compliance with privacy regulations and company policies when making modifications.

[1] programming.version_control
[2] programming.automation
[3] programming.cloud_integration
[4] programming.security_practices
[5] programming.python
[6] programming.cloud_computing
