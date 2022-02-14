
import boto3
import os
import openai
import json

openai.api_key = os.getenv("OPENAI_KEY")
s3 = boto3.resource('s3')

start_prompt = """The following is a transcript of a cooking lesson. The chef comments on the pupil's cooking itself and the narrator explains what the expert chef means.

Chef: The pupil just finished cooking, so let's see how did it go.
Narrator: The chef is about to start the lesson."""


questions = (
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

_questions = (
    "What dish have you made today?",
    "How did the chef describe their vision for the dish?",
    "Did you mention any moments of doubt to the chef?",
    "What part of the dish did the chef focus on?",
    "What would the chef like you to improve on that?",
    "What's the best way to do that?",
    "Did the chef not focus on anything else?"
)


class Models:
    DAVINCI = 'text-davinci-001'
    CURIE = 'text-curie-001'
    BABBAGE = 'text-babbage-001'
    ADA = 'text-ada-001'


class BotoError(Exception):
    pass


class Narrator:

    model = Models.DAVINCI
    temperature = 0.5
    max_tokens=150
    top_p=1
    frequency_penalty=0
    presence_penalty=0.6

    def _predict_next(self, prompt:str=start_prompt, stop:list=["Chef:", "Narrator:"]) -> str:
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

        # CHEF FEEDBACK
        prompt = self._converse(start_prompt, 'Chef', 'Narrator', sentences)

        # INQUIRIES
        prompt += "\nA\n\n"
        prompt = self._converse(prompt, 'Narrator', 'Pupil', questions)

        return prompt



class Client:
    bucket = "moment-assets-prod"
    prefix = "uploads/feedback/feedback_audio"

    def __init__(self, feedback_id:str):
        self.feedback_id = feedback_id
        self.s3_url = f"https://s3.console.aws.amazon.com/s3/object/moment-assets-prod?region=eu-west-2&prefix={self.prefix}/{self.feedback_id}/mp3_blob.mp3"

    def narrate(self, filename:str) -> str:
        return Narrator().run(filename, model=Models.DAVINCI)

    def _feedback_exists(self, feedback_id: str) -> bool:
        list_response = json.loads(s3.list_objects(Bucket=self.bucket, Prefix=f"{self.prefix}/{feedback_id}"))
        return bool(list_response.get('Contents', None))

    def transcribe(self, feedback_id: str):
        if not _feedback_exists(feedback_id):
            raise BotoError(f"Feedback not found at {self.bucket}/{self.prefix}/{feedback_id}")
