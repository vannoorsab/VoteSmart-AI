# VoteSmart AI - Global Election Education Platform

Simplifying democracy through interactive timelines, guided voting steps, and AI-driven conversations.

## Project Overview

VoteSmart AI is a production-grade educational platform featuring:

- Interactive election timelines for better visualization  
- Step-by-step voting guides for each country  
- Side-by-side election system comparison  
- Quiz mode for learning and engagement  
- AI-powered chat using Google Gemini  
- Multi-language support via Google Cloud Translate  
- Accessibility-focused frontend design  
- Deployed on Cloud Run with CI/CD integration
## Tech Stack

- Backend: Flask 3.1.0 (Python 3.11+)
- AI: Google Gemini 1.5 Flash
- Translation: Google Cloud Translate v2
- Storage: Firebase Admin / Firestore
- Grounding: Vertex AI (service wiring included)
- Deployment: Google Cloud Run
- Testing: pytest

## Project Structure

```text
VoteSmart-AI/
  app.py
  config.py
  requirements.txt
  Dockerfile
  cloudbuild.yaml
  data/
    elections.json
    glossary.json
  routes/
    health.py
    elections.py
    chat.py
    translate.py
  services/
    gemini_service.py
    translate_service.py
    firebase_service.py
    vertex_service.py
  templates/
    index.html
  static/
    css/style.css
    js/app.js
    js/chat.js
    js/timeline.js
    js/translate.js
  tests/
    test_routes.py
    test_services.py
    test_security.py
    test_accessibility.py
    test_data.py
```

## API Endpoints

- GET /health
- GET /api/elections
- GET /api/elections/<country_id>
- GET /api/elections/<country_id>/timeline
- GET /api/elections/<country_id>/voting-steps
- GET /api/glossary
- GET /api/glossary/<term>
- POST /api/chat
- POST /api/chat/grounded
- GET /api/chat/history/<session_id>
- POST /api/translate
- POST /api/translate/detect
- GET /api/languages

## Security

- Input sanitization with bleach
- Rate limiting with Flask-Limiter
- Security headers including CSP, X-Frame-Options, and X-Content-Type-Options
- Configurable limiter backend via RATELIMIT_STORAGE_URI
  - Local default: memory://
  - Production recommendation: Redis URI

## Accessibility

- Proper use of ARIA landmarks and semantic HTML
- Fully keyboard-accessible interactions
- Clear and visible focus indicators
- Skip navigation links for better usability
- High-contrast modern dark theme

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Current status:
- 250+ tests passing (routes, services, security, accessibility, and data validation)

## Deployment

Deploy command:

```bash
gcloud run deploy votesmart-ai \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Local Setup

```bash
pip install -r requirements.txt
python app.py
```

## Environment Variables

- GEMINI_API_KEY
- GOOGLE_CLOUD_PROJECT
- GOOGLE_TRANSLATE_ENABLED
- FIREBASE_ENABLED
- FIREBASE_CREDENTIALS_PATH
- VERTEX_GROUNDING_ENABLED
- RATELIMIT_STORAGE_URI
