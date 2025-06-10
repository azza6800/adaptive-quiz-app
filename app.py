from flask import Flask, request, render_template,jsonify
from openai import OpenAI
from PyPDF2 import PdfReader
from classes.classes import QuizResult, Segmentations, QuizData,Explanation
import os
from dotenv import load_dotenv
# Load the environment variables from the .env file 
load_dotenv()
# Initialize the Flask app
app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL") 
)
# Function to parse text using OpenAI API
def parse_event(user_input): 
    try:
        if not user_input:
            return {"error": "No input provided"}
        
        # Définir une tâche plus spécifique pour le modèle OpenAI, en se concentrant sur la segmentation du contenu
        task_description = (
            "Segmenter intelligemment le contenu du texte en sections logiques, en se basant exclusivement sur les sujets ou le contexte abordé dans le contenu. "
            "Il est crucial d'éviter de suivre ou de considérer le plan initial indiqué au début de l'input comme une base pour la segmentation."
        )


        # Appeler l'API OpenAI pour analyser l'entrée
        completion = client.beta.chat.completions.parse(
            model=os.getenv("OPENAI_MODEL_ID"),
            messages=[
                {"role": "system", "content": task_description},
                {"role": "user", "content": user_input},
            ],
            response_format=Segmentations
        )

        # Extraire les informations de segmentation
        parsed_event = completion.choices[0].message.parsed 
        return parsed_event

    except Exception as e:
        return {"error": str(e)}


#route to generate quiz
@app.route('/generate-quiz-ai', methods=['POST']) 
def parse_event_(): 
    data = request.json
    segmentation_title = data.get("segmentation_title")
    questionCount = "5"
    singleChoiceCount = "5" 
    multipleChoiceCount = "0"
    print("segmentation_title"+segmentation_title)
    user_input = "prompt : Genere un quiz pour : " + segmentation_title + "questionCount: "+questionCount+" singleChoiceCount: "+singleChoiceCount+" multipleChoiceCount:"+ multipleChoiceCount
    try:
        # Call OpenAI API to parse the input
        completion = client.beta.chat.completions.parse( 
            model=os.getenv("OPENAI_MODEL_ID"),
            messages=[
                {"role": "system", "content": "Geanerate a quiz for user prompt."},
                {"role": "user", "content": user_input},
            ], 
            response_format=QuizData 
        )
        # Extract parsed event information
        response = completion.choices[0].message.parsed 
        return response.dict()
     
    except Exception as e:
        return {"error": str(e)}


@app.route('/generate-explication-ai', methods=['POST'])
def generate_explanation():
    data = request.json
    segment_content = data.get("segmentation_title")  # Contenu du segment
    score = data.get("score")  # Score du quiz

    if not segment_content:
        return jsonify({"error": "No segment content provided"}), 400  # Validation de l'entrée

    if score is None:
        return jsonify({"error": "No score provided"}), 400  # Validation de l'entrée

    # Adapter le prompt en fonction du score
    if score <= 30:
        level_comment = "Il semble que vous ayez besoin de revoir le matériel plus attentivement."
    elif score <= 60:
        level_comment = "Vous vous en sortez bien, mais il y a encore de la place pour l'amélioration."
    else:
        level_comment = "Excellent travail ! Vous avez bien compris le matériel."

    user_input = (
        f"Génère une explication détaillée pour le contenu suivant : {segment_content}. "
        f"{level_comment} Adaptez l'explication au niveau de compréhension indiqué par le score du quiz : {score}."
    )

    try:
        # Appeler l'API OpenAI pour générer l'explication
        completion = client.beta.chat.completions.parse(
            model=os.getenv("OPENAI_MODEL_ID"),
            messages=[{
                "role": "system",
                "content": "Génère une explication pour l'utilisateur en fonction du contenu du segment et du score du quiz."
            }, {
                "role": "user",
                "content": user_input,
            }]
        )

        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            response = completion.choices[0].message.content
            print("*************Explication***************** " + response)
            return jsonify({"explanation": response})
        else:
            return jsonify({"error": "No valid explanation generated"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Erreur lors de l'appel à l'API OpenAI


# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    try:
        if not os.path.exists(file_path):
            return "File not found"

        reader = PdfReader(file_path)
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text()
        print("**************extracted_text**************"+extracted_text)
        return extracted_text

    except Exception as e:
        return f"Error extracting text: {e}"

# Route for the upload form
@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/submit-quiz-result', methods=['POST'])
def submit_quiz_result():
    try:
        data = request.json
        quiz_result = QuizResult(**data)  # Use Pydantic to validate the data


        # Return a success response
        return {"message": "Quiz result saved successfully"}
    except Exception as e:
        return {"error": f"Error saving quiz result: {str(e)}"}


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template('upload.html', error="No file uploaded.")

        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', error="No file selected.")

        # Define the specific folder path where you want to save the file
        specific_folder = os.path.join(os.getcwd(), 'files')

        # Create the folder if it does not exist
        if not os.path.exists(specific_folder):
            os.makedirs(specific_folder)

        # Save the uploaded file to the specific folder
        file_path = os.path.join(specific_folder, file.filename)
        file.save(file_path)

        # Extract text from the saved PDF file
        extracted_text = extract_text_from_pdf(file_path)
        # Parse event from extracted text
        segmentations = parse_event(extracted_text)
        # Add index to subtitles
        if 'Sous_titres_segmentation' in segmentations:
            segmentations['Sous_titres_segmentation'] = [
                (i + 1, sous_titre) for i, sous_titre in enumerate(segmentations['Sous_titres_segmentation'])
            ]

        # Render the extracted text on the webpage
        return render_template('upload.html', extracted_text=segmentations)
    except Exception as e:
        return render_template('upload.html', error=f"An error occurred: {e}")
 
if __name__ == '__main__':
    port = os.getenv('PORT')  # Use PORT environment variable if available
    app.run(debug=True, host='0.0.0.0', port=int(port))  
