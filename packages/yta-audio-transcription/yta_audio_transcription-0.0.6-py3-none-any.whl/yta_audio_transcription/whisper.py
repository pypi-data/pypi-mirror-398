"""
# Very interesting (https://github.com/m-bain/whisperX)
# to get timestamps of each word but the one I use is
# this one (https://github.com/linto-ai/whisper-timestamped)
"""
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_constants.enum import YTAEnum as Enum
from typing import Union, BinaryIO
from io import BytesIO

import whisper_timestamped
import numpy as np


class WhisperModel(Enum):
    """
    The model of Whisper you want to use to detect
    the audio.

    See more:
    https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages
    """
    
    TINY = 'tiny'
    """
    Trained with 39M parameters.
    Required VRAM: ~1GB.
    Relative speed: ~10x.
    """
    BASE = 'base'
    """
    Trained with 74M parameters.
    Required VRAM: ~1GB.
    Relative speed: ~7x.
    """
    SMALL = 'small'
    """
    Trained with 244M parameters.
    Required VRAM: ~2GB.
    Relative speed: ~4x.
    """
    MEDIUM = 'medium'
    """
    Trained with 769M parameters.
    Required VRAM: ~5GB.
    Relative speed: ~2x.
    """
    LARGE = 'large'
    """
    Trained with 1550M parameters.
    Required VRAM: ~10GB.
    Relative speed: ~1x.
    """
    TURBO = 'turbo'
    """
    Trained with 809M parameters.
    Required VRAM: ~6GB.
    Relative speed: ~8x.
    """

def transcribe_whisper_with_timestamps(
    audio: Union[str, BinaryIO, BytesIO, np.ndarray],
    initial_prompt: Union[str, None] = None,
    model: WhisperModel = WhisperModel.BASE
):
    """
    Transcribe the provided 'audio' using the specified
    'model' and obtains a list of 'words' (with the
    'start' and 'end' times) and the whole 'text' in
    the audio.

    This method returns the tuple (words, text).
    """
    model = WhisperModel.to_enum(model)

    # TODO: Is BinaryIO or BytesIO accepted here (?)
    audio = whisper_timestamped.load_audio(audio)
    model = whisper_timestamped.load_model(model.value, device = 'cpu')

    # See this: https://github.com/openai/openai-cookbook/blob/main/examples/Whisper_prompting_guide.ipynb
    # I do this 'initial_prompt' formatting due to some issues when using it 
    # as it was. I read in Cookguide to pass natural sentences like this below
    # and it seems to be working well, so here it is:
    if initial_prompt is not None:
        #initial_prompt = '""""' + initial_prompt + '""""'
        #initial_prompt = 'I know exactly what is said in this audio and I will give it to you (between double quotes) to give me the exact transcription. The audio says, exactly """"' + initial_prompt + '""""'
        initial_prompt = 'I will give you exactly what the audio says (the output), so please ensure it fits. The output must be """"' + initial_prompt + '""""'

    # 'vad' = True would remove silent parts to decrease hallucinations
    # 'detect_disfluences' detects corrections, repetitions, etc. so the
    # word prediction should be more accurate. Useful for natural narrations
    transcription = whisper_timestamped.transcribe(model, audio, language = "es", initial_prompt = initial_prompt)
    """
    'text', which includes the whole text
    'segments', which has the different segments
    'words', inside 'segments', which contains each 
    word and its 'text', 'start' and 'end'
    """
    words = [
        word
        for segment in transcription['segments']
        for word in segment['words']
    ]
    text = ' '.join([
        word['text']
        for word in words
    ])

    return words, text
    
@requires_dependency('faster_whisper', 'yta_audio', 'faster_whisper') # >=1.0.2
def transcribe_whisper_without_timestamps(
    audio: Union[str, BinaryIO, BytesIO, np.ndarray],
    initial_prompt: Union[str, None] = None,
    model: WhisperModel = WhisperModel.BASE
) -> str:
    """
    Obtain the transcription with no timestamps, fast and
    ideal to get ideas from the text, summarize it, etc.

    I recommend you using the 'transcribe_with_timestamps'
    because the result is more complete.

    The result is just the transcription as a text.
    """
    from faster_whisper import WhisperModel as FasterWhisperModel
    # TODO: What if 'whisper_timestamped' is better?
    # We should use it
    model: FasterWhisperModel = FasterWhisperModel(WhisperModel.to_enum(model).value)

    segments, _ = model.transcribe(
        audio = audio,
        # TODO: Audio should be customizable
        language = 'es',
        beam_size = 5,
        initial_prompt = initial_prompt
    )

    return ' '.join([
        segment.text
        for segment in segments
    ]).strip()

    model = WhisperModel.to_enum(model)

    # TODO: Is BinaryIO or BytesIO accepted here (?)
    audio = whisper_timestamped.load_audio(audio)
    model = whisper_timestamped.load_model(model.value, device = 'cpu')

    if initial_prompt is not None:
        #initial_prompt = '""""' + initial_prompt + '""""'
        #initial_prompt = 'I know exactly what is said in this audio and I will give it to you (between double quotes) to give me the exact transcription. The audio says, exactly """"' + initial_prompt + '""""'
        initial_prompt = 'I will give you exactly what the audio says (the output), so please ensure it fits. The output must be """"' + initial_prompt + '""""'

    # 'vad' = True would remove silent parts to decrease hallucinations
    # 'detect_disfluences' detects corrections, repetitions, etc. so the
    # word prediction should be more accurate. Useful for natural narrations
    transcription = whisper_timestamped.transcribe(model, audio, language = "es", initial_prompt = initial_prompt)

    words = [word for segment in transcription['segments'] for word in segment['words']]
    text = ' '.join([word['text'] for word in words])

    return text

    # TODO: This was previously written, maybe use
    # FastestWhisper or normal whisper (?)
    segments, _ = model.transcribe(audio, language = 'es', beam_size = 5, initial_prompt = initial_prompt)

    text = ' '.join([
        segment.text
        for segment in segments
    ]).strip()

    return text

# TODO: This is being tested, use carefully
@requires_dependency('speech_recognition', 'yta_audio', 'SpeechRecognition')
def transcribe_whisper_without_timestamps_real_time(
    model: WhisperModel = WhisperModel.BASE
) -> str:
    """
    Detects the audio in real time speaking and
    returns the sentence that has been said.

    TODO: This work very slow, it is not worth it
    to detect commands in real time, from the
    moment you say the phrase until it is
    transcribed it takes a long time.
    """
    # Test real time speech recognition
    import os
    import numpy as np
    import speech_recognition as sr
    # TODO: Maybe try with 'faster_whisper' (?)
    import whisper
    import torch

    from datetime import datetime, timedelta
    from queue import Queue
    from time import sleep

    # Based on this: https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py
    model = WhisperModel.to_enum(model).value
    # Use or not the English model
    #non_english = True
    # Energy level for mic to detect
    energy_threshold = 1000
    # Real time recording length (in seconds)
    record_timeout = 2
    # Empty space between recordings before
    # considering a new line (in seconds)
    phrase_timeout = 3

    # The last time a recording was retrieved
    # from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from
    # the threaded recording callback
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio
    # because it has a nice feature where it can
    # detect when speech ends
    recorder = sr.Recognizer()
    recorder.energy_threshold = energy_threshold
    # Definitely do this, dynamic energy compensation
    # lowers the energy threshold dramatically to a
    # point where the SpeechRecognizer never stops
    # recording
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate = 16000)
    audio_model = whisper.load_model(model)

    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the
        # thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw
    # audio bytes. We could do this manually but
    # SpeechRecognizer provides a nice helper
    recorder.listen_in_background(source, record_callback, phrase_time_limit = record_timeout)

    # Cue the user that we're ready to go.
    # print('System is listening:\n')

    while True:
        try:
            now = datetime.utcnow()
            #now = datetime.now(datetime.astimezone(utc))
            # Pull raw recorded audio from the queue
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings,
                # consider the phrase complete
                # Clear the current working audio buffer to
                # start over with the new data
                if (
                    phrase_time
                    and now - phrase_time > timedelta(seconds=phrase_timeout)
                ):
                    phrase_complete = True
                # This is the last time we received new audio
                # data from the queue
                phrase_time = now
                
                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()
                
                # Convert in-ram buffer to something the model
                # can use directly without needing a temp file
                # Convert data from 16 bit wide integers to
                # floating point with a width of 32 bits
                # Clamp the audio stream frequency to a PCM
                # wavelength compatible default of 32768hz max
                audio_np = np.frombuffer(
                    audio_data,
                    dtype = np.int16
                ).astype(np.float32) / 32768.0

                # Read the transcription
                result = audio_model.transcribe(audio_np, fp16 = torch.cuda.is_available())
                text = result['text'].strip()

                # If we detected a pause between recordings, add
                # a new item to our transcription Otherwise edit
                # the existing one
                if phrase_complete:
                    transcription.append(text)
                    # TODO: This line is returning the text so we are
                    # able to accept one line in real time, but this
                    # code was initially prepared to handle continuos
                    # narration (remove return and check)
                    return text
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated
                # transcription
                os.system(
                    'cls'
                    if os.name == 'nt' else
                    'clear'
                )

                for line in transcription:
                    print(line)
                # Flush stdout.
                print('', end = '', flush = True)
            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break