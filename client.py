
import boto3
import os
import openai
import json

openai.api_key = os.getenv("OPENAI_KEY")
s3 = boto3.resource('s3')

START_PROMPT = """The following is a transcript of a cooking lesson. The chef talks to the pupil. The narrator summarizes for the viewers what the chef says.

Chef: Let's start.
Narrator: The chef is about to start the lesson."""

MID_PROMPT = "The lesson is over. Let's talk to the pupil now to find out what they learned."


QUESTIONS = (
    "What dish have you made today?",
    "How did the chef describe their vision for the dish?",
    "Did you have any moments of doubt?",
    "What part of the recipe was the focus today?",
    "What was the key technique for that?",
    "Did the chef talk mostly about that?",
    "How do you get control there?",
    "What's the reasoning, or science behind it?",
    "When do you have to react?",
    "What happens when it goes wrong?",
)


class Models:
    DAVINCI = 'text-davinci-001'
    CURIE = 'text-curie-001'
    BABBAGE = 'text-babbage-001'
    ADA = 'text-ada-001'


class BotoError(Exception):
    pass


class Narrator(Models):

    model = Models.DAVINCI
    temperature = 0.5
    max_tokens=50
    top_p=1
    frequency_penalty=0
    presence_penalty=0

    def _predict_next(self, prompt:str=START_PROMPT, stop:list=["Chef:", "Narrator:"]) -> str:
        response = openai.Completion.create(
          engine=self.model,
          prompt=prompt,
          temperature=self.temperature,
          max_tokens=self.max_tokens,
          top_p=self.top_p,
          frequency_penalty=self.frequency_penalty,
          presence_penalty=self.presence_penalty,
          stop=stop).to_dict()['choices'][0]['text'].strip()

        if not response:
            print("FAILED PROMPT\n----------------------------------------\n" + prompt + '\n----------------------------------------')
            raise AssertionError("No response from GPT")

        return response

    def _converse(self, prompt:str, persona_in:str, persona_gpt:str, sentences:str) -> str:
        stops = (f"{persona_in}:", f"{persona_gpt}:", "\n")

        for input_sentence in sentences:
            prompt += f"\n{persona_in}: {input_sentence}\n{persona_gpt}:"
            gpt_reaction = self._predict_next(prompt, stops)
            prompt += f" {gpt_reaction}"

        return prompt

    def run(self, filename:str, model=Models.ADA) -> str:
        sentences = [item.strip() + '.' for item in open(f"transcripts/{filename}", 'r').read().strip().split('.') if item]
        sentence_pairs = [' '.join(pair) for pair in zip(sentences[::2], sentences[1::2])]

        # CHEF FEEDBACK
        prompt = self._converse(START_PROMPT, 'Chef', 'Narrator', sentence_pairs)

        # INQUIRIES
        # prompt += f"\n\n{MID_PROMPT}\n"
        # prompt = self._converse(prompt, 'Narrator', 'Pupil', QUESTIONS)

        return prompt


class Client:
    bucket = "moment-assets-prod"
    prefix = "uploads/feedback/feedback_audio"
    bucket_url = "https://s3.console.aws.amazon.com/s3/object/moment-assets-prod"

    def __init__(self, feedback_id:str=None):
        self.feedback_id = feedback_id
        self.s3_url = f"{self.bucket_url}?region=eu-west-2&prefix={self.prefix}/{self.feedback_id}/mp3_blob.mp3"

    def narrate(self, filename:str) -> str:
        return Narrator().run(filename, model=Models.DAVINCI)

    def _feedback_exists(self, feedback_id: str) -> bool:
        list_response = json.loads(s3.list_objects(Bucket=self.bucket, Prefix=f"{self.prefix}/{feedback_id}"))
        return bool(list_response.get('Contents', None))

    def transcribe(self, feedback_id: str):
        if not self._feedback_exists(feedback_id):
            raise BotoError(f"Feedback not found at {self.bucket}/{self.prefix}/{feedback_id}")


client = Client()
out = client.narrate("aki_paella.txt")
print(out)
