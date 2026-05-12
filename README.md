# ai-powered-web-app
AI-Powered Secure Web Application on AWS 

# AI-Powered Secure Web Application

**Stevens Institute of Technology | Spring 2026**

## 🎥 Video Demo
[Click here to watch the demo](https://drive.google.com/file/d/1ATElk1c4sNbiAqWcSf-l3wt9avl4MI8P/view?usp=sharing)

## Live Demo
https://d169r8mwjk1yr9.cloudfront.net

## Project Overview
A serverless AI-powered web app built on AWS that performs real-time
NLP analysis on user-submitted text.

## AWS Services Used
- Amazon S3 — Static website hosting + results storage
- AWS Lambda — Serverless Python NLP backend
- Amazon CloudFront — HTTPS content delivery
- Amazon CloudWatch — Monitoring and alerting

## Features
- Sentiment Analysis
- Named Entity Recognition
- Key Phrase Extraction
- Readability Scoring

## Architecture
User Browser → CloudFront (HTTPS) → S3 (static files)
User Browser → Lambda Function URL → Lambda (NLP processing)
Lambda → S3 (stores JSON results)
Lambda → CloudWatch (logs and metrics)
