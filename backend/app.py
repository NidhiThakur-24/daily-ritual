from flask import Flask, request, jsonify
from flask_cors import CORS

from google import genai

import os
from dotenv import load_dotenv



# -------------------------
# LOAD ENV VARIABLES
# -------------------------

load_dotenv()

api_key = os.getenv("GEMINI_KEY")

print("API KEY FOUND :", api_key is not None)



# -------------------------
# GEMINI CLIENT
# -------------------------

client = None

try:

    if not api_key:
        raise Exception("Missing API Key")

    client = genai.Client(
        api_key=api_key
    )

    print("Gemini Client Ready")

except Exception as e:

    print("Gemini ERROR :", e)



# -------------------------
# FLASK APP
# -------------------------

app = Flask(__name__)

CORS(app)



@app.route("/")
def home():

    return "Backend Running"



# -------------------------
# REFLECTION ROUTE
# -------------------------

@app.route("/reflection", methods=["POST"])

def reflection():

    try:

        if client is None:

            raise Exception("Gemini not initialized")


        data = request.json

        thought = data.get("thought","")

        action = data.get("action","")

        reflection_text = data.get("reflection","")


        print("Incoming Request")


        prompt = f"""
You are an analytical reflection assistant.

Do NOT emotionally validate excessively.

User Thought:
{thought}

Action Taken:
{action}

User Reflection:
{reflection}

Respond EXACTLY in this format:

Insight:
(2-3 sentences analysing behaviour patterns.)

Improve:
(2-3 sentences suggesting practical improvement.)

Next Step:
(Describe a small clear action step in detail.)

Encouragement:
(One grounded calm sentence encouraging persistence.)
"""


        print("Sending Gemini Request")


        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt,

            config={

                "temperature":0.5

            }

        )


        print("Gemini Success")


        ai_text = response.text.strip()


        return jsonify({

            "aiReflection": ai_text

        })


    except Exception as e:

        print("ERROR :", e)

        return jsonify({

            "aiReflection":

            "AI failed to generate insight."

        }),500



if __name__ == "__main__":

    app.run(debug=True)
