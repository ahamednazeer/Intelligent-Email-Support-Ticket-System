# Intelligent Email Support Ticket System

## System Overview (High Level Flow)
Customer → Email/Portal → Ingestion Module → NLP Processing → Classification & Priority Engine → Routing Engine → Ticket Database → Agent Dashboard → Resolution → Feedback → Model Retraining → Analytics

## Module-Wise End-to-End Flow

### 1) Input Module (Email & Ticket Submission)
- WHO: Customer
- WHAT they input: Email message or portal form submission
- Fields: Subject, message body, attachments (optional), contact information
- WHERE it goes: Email Server (IMAP/SMTP) or Web Portal API endpoint
- HOW it is processed: Email listener monitors inbox continuously; portal API receives form submission; raw message captured; metadata extracted (sender email, timestamp, subject, body, attachments); unique ticket ID generated; raw ticket stored in raw ticket storage
- WHAT comes out: Structured Ticket Object with `ticket_id`, `sender`, `subject`, `body`, `attachments`, `created_at`, `status = "NEW"`
- Next module: Preprocessing Module

### 2) Preprocessing Module (Text Cleaning & Preparation)
- WHO: System (automated)
- WHAT it receives: Structured Ticket Object (raw text)
- WHERE it goes: NLP Preprocessing Engine
- HOW it is processed: Remove HTML tags; remove email signatures; remove reply chains; normalize text (lowercase, remove special characters); tokenization; stopword removal; lemmatization or stemming; attachment scanning (if needed); language detection; convert cleaned text into numerical features (embeddings)
- WHAT comes out: Cleaned text, extracted entities (names, dates, order IDs, etc.), feature vector or embedding, language tag
- Next module: Intent Detection & Classification Module

### 3) Intent Detection & Classification Module
- WHO: Machine Learning Model
- WHAT it receives: Cleaned text, feature vector, extracted entities
- WHERE it goes: Classification Model API
- HOW it is processed: Intent detection model predicts intent; category classification model assigns primary category and subcategory; confidence score calculated; if confidence < threshold then flag for manual review
- WHAT comes out: `ticket_category`, `subcategory`, `intent_label`, `confidence_score`
- Next module: Priority & Urgency Prediction Module

### 4) Priority & Urgency Prediction Module
- WHO: ML Model + Rule Engine
- WHAT it receives: Category, ticket text, sentiment score, keywords, customer profile, SLA rules
- WHERE it goes: Priority Engine
- HOW it is processed: Sentiment analysis performed; urgency keywords checked ("urgent", "not working", "down"); SLA lookup (VIP customer, enterprise account); historical behavior check; ML model predicts priority (Low, Medium, High, Critical)
- WHAT comes out: `priority_level`, `urgency_score`, `sla_deadline`
- Next module: Routing & Assignment Module

### 5) Routing & Assignment Module
- WHO: Routing Engine
- WHAT it receives: `ticket_category`, `priority_level`, workload data, agent skills database
- WHERE it goes: Assignment Service
- HOW it is processed: Match ticket category with team; check available agents; check agent skill mapping; check workload balancing; assign to best-fit agent; if Critical then immediate escalation; if no agent available then queue in department pool
- WHAT comes out: `assigned_agent_id`, `department`, `updated_status = "ASSIGNED"`
- Next module: Ticket Management Module

### 6) Ticket Management Module (Agent Side)
- WHO: Support Agent
- WHAT they receive: Assigned ticket in dashboard
- WHERE it appears: Agent Dashboard
- HOW it is processed: Agent views ticket details; agent reviews category, priority, entities, suggested response; agent communicates with customer; agent updates ticket status (In Progress, Waiting for Customer, Resolved)
- WHAT comes out: Resolution notes, status updates, response timestamps
- Next module: Closure & Feedback Module

### 7) Closure & Feedback Module
- WHO: Support Agent and Customer
- WHAT happens: Ticket marked "Resolved"; customer receives resolution email
- WHERE it goes: Feedback System
- HOW it is processed: Customer feedback collected (rating, comments); feedback stored; resolution time logged; SLA compliance checked
- WHAT comes out: Final ticket record, customer satisfaction score, performance metrics
- Next module: Continuous Learning Module

### 8) Continuous Learning Module
- WHO: Data Scientist (model updates), System (automated retraining)
- WHAT it receives: Resolved tickets, feedback data, manual corrections
- WHERE it goes: Training Dataset
- HOW it is processed: Incorrect classifications identified; labeled dataset updated; retraining scheduled; model performance evaluated; updated model deployed
- WHAT comes out: Improved accuracy, updated classification model
- Next module: Analytics & Monitoring Module

### 9) Analytics & Monitoring Module
- WHO: Team Leads and Management
- WHAT they view: Dashboard metrics
- WHERE it appears: Admin Dashboard
- HOW it is processed: Ticket data aggregated; KPIs calculated (average resolution time, SLA compliance rate, agent performance, category distribution); trend analysis performed; alerts generated for SLA risk
- WHAT comes out: Reports, insights, performance charts, operational alerts

## Data Flow Simplified
Input → Processing → Classification → Priority → Routing → Agent Action → Feedback → Learning → Analytics

## What Enters vs What Leaves (Clear Input/Output)
- Input: Email text → Structured Ticket
- Preprocessing: Raw text → Cleaned features
- Classification: Features → Category + Intent
- Priority: Category + text → Priority Level
- Routing: Category + Priority → Assigned Agent
- Agent: Ticket → Resolution
- Feedback: Resolution → Rating
- Learning: Historical data → Improved Model

## No Role Confusion Summary
- Customer: Submits issue, provides feedback
- System: Processes, classifies, prioritizes, routes, stores
- Agent: Resolves, updates status
- Management: Monitors analytics
- Data Scientist: Improves models

## Tech Stack
- Backend: Python
- Frontend: Next.js (exact design and layout will follow `frontend-ref`)
- DB: SQLite
