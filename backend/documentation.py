from flask import Blueprint, request, jsonify, Response
import json
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Load Azure OpenAI credentials from .env
azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=azure_openai_key,
    api_version=azure_openai_api_version,
    azure_endpoint=azure_openai_endpoint
)

documentation_bp = Blueprint('documentation', __name__)

@documentation_bp.route("/generate-narrative", methods=['POST'])
def generate_narrative():
    try: 
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400

        def generate_stream():
            try:
                completion = client.chat.completions.create(
                    model=azure_openai_deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an AI assistant that generates structured, professional narratives for BMC Control-M workflows.
                            Your response must follow this exact structure and formatting:
                            
                            # Workflow Name
                            [A concise, descriptive name based on the use case]

                            ## Introduction
                            [A brief overview of the workflow's purpose and business value]

                            ## Use Case Overview
                            [High-level description of the business need and objectives]

                            ## Technical Implementation
                            [Detailed technical explanation of how the workflow operates, including:
                            - Data flow between jobs
                            - Dependencies and relationships
                            - Error handling and recovery
                            - Performance considerations]

                            ## Job Types and Technologies
                            [List of the Job Types in the workflow:
                            1. [Technology Name]
                            
                            2. [Technology Name]

                            And so on for each technology...]

                            Format your response with clear section headers and professional, technical language.
                            Use markdown formatting for better readability."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate a structured narrative for the following workflow:
                            Technologies: {technologies}
                            Workflow Order: {ordered_workflow}
                            Use Case: {use_case}
                            
                            Follow the exact structure provided, with clear section headers."""
                        }
                    ],
                    stream=True
                )

                for chunk in completion:
                    if chunk.choices and hasattr(chunk.choices[0], "delta"):
                        content = getattr(chunk.choices[0].delta, "content", None)
                        if content:
                            yield content
            except Exception as e:
                yield json.dumps({"error": str(e)})

        return Response(generate_stream(), content_type="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@documentation_bp.route("/generate-talktrack", methods=['POST'])
def generate_talktrack():
    try: 
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400

        def generate_stream():
            try:
                completion = client.chat.completions.create(
                    model=azure_openai_deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an AI assistant that generates presentation-style talk tracks for BMC Control-M workflow demonstrations.
                            Your response must follow this exact structure and formatting:
                            
                            # Workflow Demonstration Talk Track
                            [A compelling title that captures the essence of the workflow]

                            ## Introduction (30 seconds)
                            [A brief, engaging introduction that hooks the audience and sets up the business context]

                            ## Business Challenge (1 minute)
                            [Describe the business problem or opportunity that this workflow addresses]

                            ## Solution Overview (1 minute)
                            [High-level explanation of how the workflow solves the business challenge]

                            ## Workflow Walkthrough (3-4 minutes)
                            [Step-by-step explanation of the workflow, including:
                            - What each job does
                            - Why it's important
                            - How it connects to the next step
                            - Business value at each stage]

                            ## Key Benefits (1 minute)
                            [Highlight the main advantages and improvements this workflow brings]

                            ## Technical Highlights (1 minute)
                            [Point out the most impressive technical aspects of the implementation]

                            ## Conclusion (30 seconds)
                            [Wrap up with a strong call to action or next steps]

                            Format your response with clear section headers and engaging, presentation-style language.
                            Use markdown formatting for better readability."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate a presentation talk track for the following workflow:
                            Technologies: {technologies}
                            Workflow Order: {ordered_workflow}
                            Use Case: {use_case}
                            
                            Follow the exact structure provided, with clear section headers and timing guidance."""
                        }
                    ],
                    stream=True
                )

                for chunk in completion:
                    if chunk.choices and hasattr(chunk.choices[0], "delta"):
                        content = getattr(chunk.choices[0].delta, "content", None)
                        if content:
                            yield content
            except Exception as e:
                yield json.dumps({"error": str(e)})

        return Response(generate_stream(), content_type="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500 