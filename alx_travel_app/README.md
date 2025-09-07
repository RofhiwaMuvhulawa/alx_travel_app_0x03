# ALX Travel App Deployment Guide

This guide provides instructions for deploying the ALX Travel App to a production server with Celery background tasks and Swagger API documentation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Environment Variables](#environment-variables)
4. [Deploying to PythonAnywhere](#deploying-to-pythonanywhere)
5. [Deploying to Render](#deploying-to-render)
6. [Configuring Celery with RabbitMQ](#configuring-celery-with-rabbitmq)
7. [Testing the Deployed Application](#testing-the-deployed-application)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- A complete Django application with all requirements installed
- A GitHub repository with your code (https://github.com/RofhiwaMuvhulawa/alx_travel_app_0x03)
- Database credentials for production
- SMTP email credentials for sending emails
- RabbitMQ credentials for Celery tasks

## Deployment Options

This guide covers two recommended deployment options:

1. **PythonAnywhere** - Easy to set up, includes MySQL database, good free tier
2. **Render** - Modern cloud platform with good scaling options

## Environment Variables

The following environment variables must be configured on your production server:
