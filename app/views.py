from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from groq import Groq
import os
from django.http import FileResponse
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

groq_api_key = os.environ.get("groq_api")
client = Groq(api_key=groq_api_key) 
aws_secret_key = os.environ.get("aws_secret_key")
aws_access_key = os.environ.get("aws_access_key")

@api_view(['POST'])
def transcribe_and_synthesize(request):
    audio_file = request.FILES.get('file')

    if not audio_file:
        logger.error("No audio file provided")
        return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info("Starting transcription for file: %s", audio_file.name)
        
        # Transcribe the audio file
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3-turbo",
            prompt="Specify context or spelling",
            response_format="json",
            language="en",
            temperature=0.0
        )

        transcribed_text = transcription.text
        logger.info("Transcription completed: %s", transcribed_text)


        if not transcribed_text:
            logger.error("Transcription failed, no text returned")
            return Response({'error': 'Transcription failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info("Starting speech synthesis for text: %s", transcribed_text)

        chat_completion = client.chat.completions.create(
            #
            # Required parameters
            #
            messages=[
                # Set an optional system message. This sets the behavior of the
                # assistant and can be used to provide specific instructions for
                # how it should behave throughout the conversation.
                {
                    "role": "system",
                    "content": "you are a helpful assistant."
                },
                # Set a user message for the assistant to respond to.
                {
                    "role": "user",
                    "content": transcribed_text,
                }
            ],

            # The language model which will generate the completion.
            model="llama3-8b-8192",

            #
            # Optional parameters
            #

            # Controls randomness: lowering results in less random completions.
            # As the temperature approaches zero, the model will become deterministic
            # and repetitive.
            temperature=0.8,

            # The maximum number of tokens to generate. Requests can use up to
            # 32,768 tokens shared between prompt and completion.
            max_tokens=512,

            # Controls diversity via nucleus sampling: 0.5 means half of all
            # likelihood-weighted options are considered.
            top_p=1,

            # A stop sequence is a predefined or user-specified text string that
            # signals an AI to stop generating content, ensuring its responses
            # remain focused and concise. Examples include punctuation marks and
            # markers like "[end]".
            stop=None,

            # If set, partial message deltas will be sent.
            stream=False,
        )

        # Print the completion returned by the LLM.
        print(chat_completion.choices[0].message.content)


        response_text = chat_completion.choices[0].message.content
        # print(response_text
        # Synthesize speech from the transcribed text
        polly_client = boto3.Session(
            aws_access_key_id= aws_access_key,
            aws_secret_access_key= aws_secret_key,
            region_name='us-west-2'
        ).client('polly')

        response = polly_client.synthesize_speech(
            VoiceId='Danielle',
            OutputFormat='mp3',
            Text=response_text,
            Engine='neural'
        )

        audio_file_path = 'speech.mp3'
        with open(audio_file_path, 'wb') as file:
            file.write(response['AudioStream'].read())

        logger.info("Speech synthesis completed, returning audio file")

        # Return the audio file as a response
        return FileResponse(open(audio_file_path, 'rb'), content_type='audio/mpeg', as_attachment=True, filename='speech.mp3')

    except (BotoCoreError, ClientError) as error:
        logger.error("Error occurred in AWS Polly: %s", str(error))
        return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error("An unexpected error occurred: %s", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)