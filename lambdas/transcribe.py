
import boto3


def lambda_handler(event, context):

    record = event['Records'][0]
    feedback_id = record['s3']['object']['key']

    audio_bucket: str = "moment-assets-prod"
    text_bucket: str = "moment-ml-feedback-processing"

    text_prefix = f"{feedback_id}/{feedback_id}.json"
    audio_prefix = f"uploads/feedback/feedback_audio/{feedback_id}"

    audio_url = f"s3://{audio_bucket}/{audio_prefix}/mp3_blob.mp3"

    # Validate the source bucket
    source_bucket = record['s3']['bucket']['name']
    assert source_bucket == "moment-assets-prod", f"Wrong bucket, expected moment-assets-prod, found {source_bucket}."

    transcribe = boto3.client('transcribe')

    response = transcribe.start_transcription_job(
        TranscriptionJobName=f"moment-couch-feedback-{feedback_id}",
        Media={
            'MediaFileUri': audio_url
        },
        MediaFormat='mp3',
        OutputBucketName=text_bucket,
        OutputKey=text_prefix,
        IdentifyLanguage=True
    )

    return {
        'TranscriptionJobName': response['TranscriptionJob']['TranscriptionJobName']
    }
