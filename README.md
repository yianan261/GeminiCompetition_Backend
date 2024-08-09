# Gemini Trip App Backend for Google Gemini Developer Competition 2024

This repository contains the backend services for the Gemini Trip App (Update: now Wanderfinds), an application designed to help add a dash of spontaneity to your daily life. Users can use the app to explore new places on their daily commutes to work, or as they are traveling in a new place. All the recommended places will be based on their personality types and interests. We use Google Gemini to help filter recommendations for new spots to visit that is tailored to each user by digesting their Google Takeout history. In addition, our application has an AI tour guide that helps give user more context and information about a place. The backend storing and retrieving saved places, and interacting with external APIs such as Google Maps and Google Gemini.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Contributing](#contributing)

## Features

- **User Management:** Once users have registered through firebase from the frontend, they can upload their Google takeout data and find and save their favorite places.
- **Saved Places:** Users can bookmark places, retrieve their saved places, and remove bookmarks.
- **Google Takeout Integration:** Allows users to upload their Google Takeout files to save locations from their history.
- **Google Maps Integration:** Fetches nearby attractions and restaurants based on user preferences.
- **LLM Integration:** Uses Google Gemini for generating personalized descriptions and filtering places based on user preferences.

## Tech Stack

- **Backend Framework:** Flask
- **Frontend Framework:** Flutter ([here is the frontend repository](https://github.com/yianan261/GeminiFrontend))
- **Database:** Firestore (Google Cloud Firestore)
- **Authentication:** Firebase Authentication
- **APIs:** Google Maps API, Google Takeout, Google Gemini
- **Environment Management:** Python’s `venv`, Docker

## Setup and Installation

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized development)

### Clone the Repository

```bash
git clone https://github.com/yourusername/GeminiApp.git
cd GeminiApp/GeminiCompetition_Backend/api_service
```

### Set up virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Running the app

To run the Flask app, simply just run `./runCompose.sh`. If this is the first time, run `chmod +x runCompose.sh`

store the firebase _.json_ file to api*service and put the filename on *.gitignore\_

If possible, use \*api_response\*\* function to return the api response. You can find example in /api_service/api_service.py
