import json
import os
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from num2words import num2words
from pyannote.audio import Pipeline
from pydub import AudioSegment
from pydub.silence import split_on_silence
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transliterate import translit
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import nemo.collections.asr as nemo_asr
import requests


def log(x, debug=True):
    if debug:
        print(x)


def init():
    global model, tokenizer, sr_model, pipeline
    tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ru", cache_dir="cache/")
    model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-ru", cache_dir="cache/")
    sr_model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained("nvidia/stt_en_conformer_ctc_large")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", cache_dir="cache/")


def reshape(lst1, lst2):
    iterator = iter(lst2)
    return [[next(iterator) for _ in sublist]
            for sublist in lst1]


def word_preprocess(sentence):
    sentence = sentence.replace("%", " percent ")
    sentence = sentence.replace("  ", " ").replace("\n", "")
    return sentence


def translate(x_):
    x_ = word_preprocess(x_)
    x_ = tokenizer.decode(
        model.generate(**tokenizer(x_, return_tensors="pt", padding=True))[0],
        skip_special_tokens=True)
    x_ = " ".join([x if not x.isnumeric() else num2words(x, lang="ru") for x in x_.split()]).strip()
    return translit(x_, 'ru')


def flat(xss):
    return [x for xs in xss for x in xs]


def get_sentence(sentence, voice='xenia'):
    language = 'ru'
    model_id = 'v3_1_ru'
    model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                              model='silero_tts',
                              language=language,
                              speaker=model_id)
    model.to(torch.device("cpu"))
    sample_rate = 48000
    put_accent = True
    put_yo = True
    # speakers = ['aidar', 'eugene', 'baya', 'kseniya', 'xenia', 'random']
    # sentence = 'З+а+анкокуу но теншииии нойонииии'

    ret_audio = model.apply_tts(text=sentence,
                                speaker=voice,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
    sf.write("data/temp.wav", ret_audio, sample_rate)


def audio_file_to_np_array(asg):
    dtype = getattr(np, "int{:d}".format(asg.sample_width * 8))
    arr = np.ndarray((int(asg.frame_count()), asg.channels), buffer=asg.raw_data, dtype=dtype)
    # print("\n", asg.frame_rate, arr.shape, arr.dtype, arr.size, len(asg.raw_data), len(asg.get_array_of_samples()))
    return arr.copy()


def audio_file_to_np_array2(asg):
    arr = np.ndarray((int(asg.frame_count()), asg.channels), buffer=asg.raw_data, dtype=np.byte)
    # print("\n", asg.frame_rate, arr.shape, arr.dtype, arr.size, len(asg.raw_data), len(asg.get_array_of_samples()))
    return arr.copy()


def stt(_chunk):
    _chunk.split_to_mono()[0].export("data/_chunk.wav")
    return sr_model.transcribe(["data/_chunk.wav"])[0]


def get_translated_wav(text_, audio_chunk_):
    get_sentence(text_)
    translated_wav = AudioSegment.from_file("data/temp.wav")
    translated_wav = AudioSegment.from_mono_audiosegments(translated_wav, translated_wav)
    if len(audio_chunk_) < len(translated_wav):
        duration_ = 300
    else:
        duration_ = len(audio_chunk_) - len(translated_wav)
    return translated_wav, duration_


done_init = False


def query(filename):
    API_URL = "https://api-inference.huggingface.co/models/pyannote/speaker-diarization"
    headers = {"Authorization": "Bearer **your_code**"}
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))


def process_video(url, limit=120):
    if "backend" not in os.getcwd():
        os.chdir("backend")
    video_id = url.split("watch?v=")[1]
    if Path(f"../static/out/{video_id}.mp4").exists():
        return
    global done_init
    if not done_init:
        done_init = True
        init()
    # url = "https://www.youtube.com/watch?v=1fmha9dtASA"
    # url = "https://www.youtube.com/watch?v=JOg_smPzq5A"
    # url = "https://www.youtube.com/watch?v=rnnU8nT8yDc"
    # url = "https://www.youtube.com/watch?v=2OSrvzNW9FE"
    os.chdir("data")
    videopath = YoutubeDL({'format': 'bestvideo+bestaudio/best'}).extract_info(url)["requested_downloads"][0][
        "filepath"]
    if limit is None:
        os.system(f"ffmpeg -y -i \"{videopath}\" -vn -c:a copy -acodec pcm_s16le -ar 48000 {video_id}.wav")
    else:
        os.system(
            f"ffmpeg -y -i \"{videopath}\" -vn -c:a copy -acodec pcm_s16le -ar 48000 -t {limit} {video_id}.wav")
    log("Downloaded audio")
    original_audio = AudioSegment.from_file(f"{video_id}.wav").set_frame_rate(48000)
    # original_audio_samples = audio_file_to_np_array(original_audio)
    transcript = None
    need2translate = False
    os.chdir("..")
    try:  # it's called production
        if "ru" in YouTubeTranscriptApi.list_transcripts(video_id)._manually_created_transcripts:
            try:
                transcript = YouTubeTranscriptApi.list_transcripts(video_id)._manually_created_transcripts["ru"].fetch()
                print("Found manual russian subtitles")
                need2translate = False
            except:
                pass
        elif "en" in YouTubeTranscriptApi.list_transcripts(video_id)._manually_created_transcripts:
            try:
                transcript = YouTubeTranscriptApi.list_transcripts(video_id)._manually_created_transcripts["en"].fetch()
                print("Found manual english subtitles")
                need2translate = True
            except:
                pass
    except:
        pass
    final_audio = AudioSegment.silent(duration=500)
    start_padded = False
    if transcript is not None:
        print(f"Translating {len(transcript)} chunks via a transcript")
        for i, line in enumerate(transcript):
            text, start, duration = line["text"], line["start"], line["duration"]
            if start/1000 > limit:  # limit
                break
            if not start_padded:
                final_audio = AudioSegment.silent(duration=start)
                start_padded = True
            if need2translate:
                text = text.replace("$", " US dollar ")
                _text = translate(text)
                print(f"{text} : {_text}")
                text = _text
            else:
                text = text.replace("$", " долларов США ")
                text = " ".join([x if not x.isnumeric() else num2words(x, lang="ru") for x in text.split()]).strip()
            audio_chunk = original_audio[start * 1000:(start + duration) * 1000]
            # print(text)
            translated, pad_duration = get_translated_wav(text, audio_chunk)
            final_audio += (translated + AudioSegment.silent(duration=pad_duration))
    else:
        try:
            diarization = pipeline(f"data/{video_id}.wav")
        except:
            print("OOM, retrying online inference")
            diarization = query(f"data/{video_id}.wav")
        print(f"Translating {len(diarization)} chunks")
        for i, (turn, _, speaker) in enumerate(diarization.itertracks(yield_label=True)):
            if not start_padded:
                final_audio = AudioSegment.silent(duration=turn.start * 1000)
                start_padded = True
            audio_chunks = [original_audio[turn.start * 1000: turn.end * 1000]]
            if turn.end - turn.start > 5:
                audio_chunks = split_on_silence(
                    audio_chunks[0],
                    min_silence_len=500,
                    silence_thresh=audio_chunks[0].dBFS - 16,
                    keep_silence=True,  # optional
                )
            print("split again in", len(audio_chunks))
            for audio_chunk in audio_chunks:
                print("audio chunk of len", len(audio_chunk))
                text_ = stt(audio_chunk)
                # audio_chunk = original_audio[start * 1000:(start + duration) * 1000]
                text_ = text_.replace("$", " US dollar ")
                if text_ == "" or text_ == " ":
                    text = "хм"
                else:
                    text = translate(text_.replace("\n", ""))
                    print(f"{text_} : {text}")
                try:
                    translated, pad_duration = get_translated_wav(text, audio_chunk)
                except:
                    translated = AudioSegment.silent(len(audio_chunk))
                    pad_duration = 0
                final_audio += (translated + AudioSegment.silent(duration=pad_duration))
    final_audio = (original_audio - 12).overlay(final_audio, position=0)
    final_audio.export("data/export.wav")
    os.system(
        f"ffmpeg -y -i \"{videopath}\" -i data/export.wav -c:v copy -map 0:v:0 -map 1:a:0 ../static/out/{video_id}.mp4")
    return


if __name__ == '__main__':
    process_video("https://www.youtube.com/watch?v=1sRP6eBqGbo", limit=320)  # seconds
