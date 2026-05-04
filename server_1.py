"""
Flask proxy server for Daily Ritual — Gemini 1.5 Flash
API key is loaded from system environment variables directly.
"""

import os  # Import the os module to access operating system functionalities like environment variables
import requests  # Import the requests library to make HTTP requests to external APIs
from flask import Flask, request, jsonify  # Import Flask components: Flask for the app, request for handling requests, jsonify for JSON responses
from flask_cors import CORS  # Import CORS to handle Cross-Origin Resource Sharing for web requests

# LESSON: No load_dotenv() needed anymore.
# When your key is set as a system environment variable,
# os.getenv() reads it directly — no .env file required.
# In VS Code terminal you can verify with: echo $GEMINI_API_KEY (Mac/Linux)
# or: echo %GEMINI_API_KEY% (Windows)

app = Flask(__name__)  # Create a Flask application instance with the current module name
CORS(app)  # Enable Cross-Origin Resource Sharing for the Flask app to allow requests from different origins

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Retrieve the Gemini API key from system environment variables

GEMINI_URL = (  # Define the URL for the Gemini API endpoint, using string formatting for the key
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-2.5-flash:generateContent?key={key}"
)


@app.route("/api/chat", methods=["POST"])  # Decorator to define a route for POST requests to /api/chat endpoint
def chat():  # Define the function to handle chat API requests
    if not GEMINI_API_KEY:  # Check if the API key is not set (falsy)
        return jsonify({"error": {"message": "GEMINI_API_KEY not found in system environment"}}), 500  # Return a JSON error response with HTTP 500 status

    body = request.get_json()  # Parse the incoming request body as JSON

    system_text = body.get("system", "")  # Extract the 'system' field from the JSON body, default to empty string
    messages    = body.get("messages", [])  # Extract the 'messages' field from the JSON body, default to empty list

    # Translate Anthropic message format → Gemini format
    contents = []  # Initialize an empty list to hold the formatted contents for Gemini
    if system_text:  # If system text is provided, add it as the first message
        contents.append({  # Append system message to contents
            "role": "user",  # Use 'user' role for system prompt
            "parts": [{"text": system_text}]  # Include the system text
        })
    for msg in messages:  # Loop through each message in the messages list
        role = "model" if msg["role"] == "assistant" else "user"  # Map the role: 'assistant' becomes 'model', others 'user'
        contents.append({  # Append a dictionary representing the message to contents
            "role": role,  # Set the role for the message
            "parts": [{"text": msg["content"]}]  # Set the content as a list of parts with text
        })

    gemini_body = {  # Create the request body dictionary for the Gemini API
        "contents": contents,  # Include the list of contents (messages)
        "generationConfig": {  # Configure generation parameters
            "temperature": 0.7,  # Set temperature for randomness in responses
            "maxOutputTokens": 2500, # Set max tokens, default to 2500
        }
    }

    try:  # Start a try block to handle potential exceptions during the API call
        response = requests.post(  # Send a POST request to the Gemini API
            GEMINI_URL.format(key=GEMINI_API_KEY),  # Format the URL with the API key
            headers={"Content-Type": "application/json"},  # Set headers to indicate JSON content
            json=gemini_body,  # Send the request body as JSON
            timeout=30,  # Set a timeout of 30 seconds for the request
        )
        print("Gemini response status:", response.status_code)  # Debug: print status
        print("Gemini response text:", response.text[:500])  # Debug: print first 500 chars of response
        try:
            gemini_data = response.json()  # Parse the response as JSON
        except ValueError as e:
            return jsonify({"error": {"message": f"Invalid JSON from Gemini: {response.text}"}}), 500  # Return error with response text
    except requests.exceptions.Timeout:  # Catch timeout exceptions
        return jsonify({"error": {"message": "Request to Gemini timed out"}}), 504  # Return timeout error with HTTP 504
    except Exception as e:  # Catch any other exceptions
        return jsonify({"error": {"message": str(e)}}), 500  # Return general error with HTTP 500

    if "error" in gemini_data:  # Check if the Gemini response contains an error
        return jsonify({"error": {"message": gemini_data["error"].get("message", "Gemini error")}}), 500  # Return the error message

    try:  # Try to extract the generated text from the response
        text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]  # Access the text from the first candidate
    except (KeyError, IndexError):  # Catch key or index errors if response structure is unexpected
        return jsonify({"error": {"message": "Unexpected response shape from Gemini"}}), 500  # Return parsing error

    # Return in Anthropic shape so the frontend doesn't change
    return jsonify({  # Return a JSON response in the expected format
        "content": [{"type": "text", "text": text}]  # Include the generated text as content
    })


@app.route("/health", methods=["GET"])  # Decorator to define a route for GET requests to /health endpoint
def health():  # Define the function to handle health check requests
    return jsonify({  # Return a JSON response with health information
        "status": "ok",  # Indicate the status is okay
        "provider": "Gemini 2.5 Flash",  # Specify the AI provider
        "key_loaded": bool(GEMINI_API_KEY)  # Check if the API key is loaded (True/False)
    })

@app.route("/api/models", methods=["GET"])  # Define a route for GET requests to /api/models endpoint
def list_models():  # Define the function to list available Gemini models
    if not GEMINI_API_KEY:  # Check if the API key is not set
        return jsonify({"error": {"message": "GEMINI_API_KEY not set"}}), 500  # Return error

    try:  # Try to fetch the list of models
        response = requests.get(  # Send GET request to list models
            f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_API_KEY}"  # URL for listing models
        )
        return jsonify(response.json()), response.status_code  # Return the response
    except Exception as e:  # Catch any exceptions
        return jsonify({"error": {"message": str(e)}}), 500  # Return error

if __name__ == "__main__":  # Check if this script is being run directly (not imported)
    print("\n✦ Daily Ritual API server starting...")  # Print a starting message to the console
    print(f"✦ Gemini key loaded: {bool(GEMINI_API_KEY)}")  # Print whether the API key is loaded
    print("✦ Health check → http://localhost:5000/health\n")  # Print the health check URL
    app.run(debug=True, port=5000)  # Run the Flask application in debug mode on port 5000
