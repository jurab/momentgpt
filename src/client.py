
import boto3
import lorem
import os
import requests
import time
import json

from botocore.config import Config
from botocore.exceptions import ClientError
from dataclasses import dataclass
from deepl import Translator
from threading import local

from core.utils import Singleton
from validators import validate_feedback_id

boto_config = Config(region_name='eu-west-2')

transcribe = boto3.client('transcribe', config=boto_config)
s3 = boto3.client('s3', config=boto_config)
translator = Translator(os.getenv('DEEPL_API_KEY'))

DEBUG = False

START_PROMPT = """The following is a transcript of a cooking lesson. The chef talks to the pupil. The narrator summarizes for the viewers what the chef says.

Chef: Let's start.
Narrator: The chef is about to start the lesson."""


QUESTIONS = [
    "What did you cook today?",
    "How did the chef describe the ideal version of the dish?",
    "What was exceptional about your result?",
    "Did you have any moments of doubt?",
    "What aspect of the dish did the chef focus the lesson on?",
    "What useful knowledge did you gain?",
    "Can you explain that in terms of the science of cooking?",
]


MID_PROMPT = """After the lesson is over, the pupil gets a questionnaire about the lesson. These are the questions:
{questions}

And here are the pupil's answers:"""


class Models:
    DAVINCI = 'text-davinci-001'  # largest
    CURIE = 'text-curie-001'
    BABBAGE = 'text-babbage-001'
    ADA = 'text-ada-001'  # smallest


class BotoError(Exception):
    pass


@dataclass(init=False)
class NarratorResult:
    feedback: str
    answers: str


class Narrator:

    model = Models.DAVINCI
    temperature = 0.9
    top_p = 1
    frequency_penalty = 0
    presence_penalty = 0
    result = NarratorResult()

    def __init__(self, client):
        self.client = client

    def _predict_next(self, prompt:str=START_PROMPT, stop:list=["Chef:", "Narrator:"], max_tokens:int=75) -> str:

        if DEBUG:
            return lorem.sentence()

        url = f"https://api.openai.com/v1/engines/{self.model}/completions"

        params = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stop": stop
        }

        headers = {
            'Authorization': f"Bearer {os.getenv('OPENAI_API_KEY')}",
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, json=params)

        if not response:
            ("FAILED PROMPT\n----------------------------------------\n" + prompt + '\n----------------------------------------')
            raise AssertionError("No response from GPT")

        return response.json()['choices'][0]['text'].strip()

    def _converse(self, prompt:str, persona_in:str, persona_gpt:str, sentences:str) -> str:
        stops = (f"{persona_in}:", f"{persona_gpt}:", "\n")

        for input_sentence in sentences:
            prompt += f"\n{persona_in}: {input_sentence}\n{persona_gpt}:"
            gpt_reaction = self._predict_next(prompt, stops, max_tokens=50)
            prompt += f" {gpt_reaction}"

        return prompt

    def _mid_prompt(self):
        return f"\n\n{MID_PROMPT.format(questions=self.client.question_string())}\n"

    def query_answers(self, context):
        prompt = context + self._mid_prompt()
        return self._predict_next(prompt, max_tokens=300, stop=None)

    def run(self, transcript:str, model=Models.ADA) -> str:
        sentences = transcript.strip().replace('...', '@@').split('.')
        sentences = [sentence.strip().replace('@@', '...') + '.' for sentence in sentences if sentence]
        sentence_pairs = [' '.join(pair) for pair in zip(sentences[::2], sentences[1::2])]

        # CHEF FEEDBACK
        prompt = self._converse(START_PROMPT, 'Chef', 'Narrator', sentence_pairs)
        # prompt = open('results/aki_paella.txt', 'r').read()

        self.result.feedback = prompt

        # INQUIRIES
        gpt_answers = self.query_answers(prompt)
        prompt += self._mid_prompt()
        prompt += gpt_answers
        self.result.answers = gpt_answers

        return prompt


class Client(local, metaclass=Singleton):
    s3_url = "https://s3.console.aws.amazon.com/s3/object"

    audio_bucket: str = "moment-assets-prod"
    audio_prefix: str = None
    audio_url: str = None

    text_bucket: str = "moment-ml-feedback-processing"
    text_prefix: str = None
    text_url: str = None

    feedback_id: str = None
    questions: list = None
    narrative: str = None
    transcript: str = None
    translation: str = None

    def __init__(self, feedback_id:str=None):
        self.narrator = Narrator(client=self)
        self.questions = QUESTIONS

        if feedback_id:
            self.set_feedback_id(feedback_id)

    def set_feedback_id(self, feedback_id:str):
        validate_feedback_id(feedback_id)
        self.feedback_id = feedback_id if feedback_id else None

        self.audio_prefix = f"uploads/feedback/feedback_audio/{feedback_id}"
        self.text_prefix = f"{self.feedback_id}/{self.feedback_id}.json"

        self.audio_url = f"s3://{self.audio_bucket}/{self.audio_prefix}/mp3_blob.mp3"
        self.text_url = f"s3://{self.text_bucket}/{self.text_prefix}.json"

        if self.text_exists():
            self.transcript = self.fetch_transcript()

    def question_string(self):
        return '\n'.join([f'{i}. {question}' for i, question in enumerate(QUESTIONS, 1)])

    def question_html(self):
        return '<br><br>'.join([f'{i}. {question}' for i, question in enumerate(QUESTIONS, 1)])

    def narrate(self) -> str:
        self.narrative = self.narrator.run(self.transcript, model=Models.DAVINCI)
        return self.narrative

    def _s3_folder_exists(self, bucket: str, prefix: str) -> bool:
        return 'Contents' in s3.list_objects(Bucket=bucket, Prefix=prefix)

    def audio_exists(self):
        return self._s3_folder_exists(self.audio_bucket, self.audio_prefix)

    def text_exists(self):
        return self._s3_folder_exists(self.text_bucket, self.feedback_id)

    def fetch_transcript(self):

        try:
            return  json.loads(s3.get_object(Bucket=self.text_bucket, Key=self.text_prefix)['Body'].read())['results']['transcripts'][0]['transcript']
        except ClientError:
            raise BotoError(f"Cannot find transcript at {self.audio_url}")

    def detect_language(self, text):
        return translator.translate_text(text, target_lang="FR").detected_source_lang

    def translate(self):
        if self.translation:
            return self.translation

        source_language = self.detect_language(self.transcript.split('.')[0])

        if 'EN' in source_language:
            return

        result = translator.translate_text(self.transcript, target_lang='EN-GB')
        self.translation = result.text
        return result.text

    def transcribe(self):
        if not self.audio_exists():
            raise BotoError(f"Feedback folder not found at {self.audio_url}")

        if self.text_exists():
            raise BotoError(f"Transcription already exists at {self.text_url}")

        try:
            transcribe.start_transcription_job(
                TranscriptionJobName=self.feedback_id,
                Media={
                    'MediaFileUri': self.audio_url
                },
                MediaFormat='mp3',
                OutputBucketName=self.text_bucket,
                OutputKey=self.text_prefix,
                IdentifyLanguage=True
            )

        except ClientError:
            raise BotoError(f"Failed starting transcription at {self.audio_url}")

        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=self.feedback_id)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)

        transcript = self.fetch_transcript()

        self.transcript = transcript
        return transcript


client = Client()
