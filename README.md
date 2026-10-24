# CityVoice

CityVoice is a smart municipal complaint and maintenance management system for Ma'in District, Sana'a.

## System Architecture

The project consists of two separate systems:

### 1. Operational System
Manages daily transactions and services, including:

- Citizen complaint submission and tracking
- Municipal complaint management
- Field-worker maintenance tasks
- Municipal assets and service categories
- Geographic data using GIS

### 2. Analytical System
Uses data extracted from the operational system to provide:

- Data warehouse and ETL processes
- Performance indicators
- Analytical dashboards
- Spatial analysis
- Findings and recommendations for decision support

## Technologies

- Python and Django
- PostgreSQL and PostGIS
- Django REST Framework
- Power BI
- HTML, CSS, and JavaScript

## Project Structure

- `operational_system/` — Operational applications and database
- `analytical_system/` — Data warehouse and analytical applications
- `.env.example` — Required environment-variable template

## Status

This project is currently under development as a graduation project.