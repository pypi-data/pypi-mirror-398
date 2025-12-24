import numpy as np
import librosa
import pandas as pd
import re
from scipy.signal import butter, filtfilt

# Preprocess Audio
def preprocess_audio(audio_path, target_sr=16000, cutoff=100):
    y, sr = librosa.load(audio_path, sr=None)
    y_normalized = librosa.util.normalize(y)
    y_trimmed, _ = librosa.effects.trim(y_normalized, top_db=20)

    def highpass_filter(y, sr, cutoff):
        nyquist = 0.5 * sr
        normal_cutoff = cutoff / nyquist
        b, a = butter(1, normal_cutoff, btype='high', analog=False)
        return filtfilt(b, a, y)

    y_filtered = highpass_filter(y_trimmed, sr, cutoff)
    y_resampled = librosa.resample(y_filtered, orig_sr=sr, target_sr=target_sr)
    return y_resampled, target_sr

# Parse WEBVTT
def parse_webvtt(file_path):
    transcription_data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    timestamp_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")
    speaker_pattern = re.compile(r"<v (\w+)> (.+)")

    current_start = None
    current_end = None
    current_speaker = ""
    current_text = ""

    for line in lines:
        line = line.strip()

        if timestamp_match := timestamp_pattern.match(line):
            if current_text and current_start and current_end:
                transcription_data.append({
                    "start_time": current_start,
                    "end_time": current_end,
                    "speaker": current_speaker,
                    "text": current_text.strip()
                })
            current_text = ""
            current_start = timestamp_match.group(1)
            current_end = timestamp_match.group(2)

        elif speaker_match := speaker_pattern.match(line):
            current_speaker = speaker_match.group(1)
            current_text = speaker_match.group(2)
        elif line:
            current_text += " " + line

    if current_text and current_start and current_end:
        transcription_data.append({
            "start_time": current_start,
            "end_time": current_end,
            "speaker": current_speaker,
            "text": current_text.strip()
        })

    return transcription_data

# Extract Non-Silent Intervals
def extract_non_silent_segments(audio_segment, sr, top_db=20):
    non_silent_intervals = librosa.effects.split(audio_segment, top_db=top_db)
    non_silent_timestamps = [(start / sr, end / sr) for start, end in non_silent_intervals]
    return non_silent_intervals, non_silent_timestamps

# Weighted Pitch and RMS Calculation
def calculate_weighted_pitch_rms(audio_segment, sr, non_silent_intervals):
    total_duration = 0
    weighted_rms_sum = 0
    weighted_pitch_sum = 0

    for start, end in non_silent_intervals:
        segment = audio_segment[start:end]
        f0, _, _ = librosa.pyin(segment, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        rms = librosa.feature.rms(y=segment)[0]

        duration = (end - start) / sr
        total_duration += duration

        rms_weight = np.mean(rms) * duration
        pitch_weight = np.nanmean(f0) * duration if np.any(~np.isnan(f0)) else 0

        weighted_rms_sum += rms_weight
        weighted_pitch_sum += pitch_weight

    weighted_rms = (weighted_rms_sum / total_duration) if total_duration > 0 else 0
    weighted_pitch = weighted_pitch_sum / total_duration if total_duration > 0 else 0

    return weighted_pitch, weighted_rms

# Process Each Timestamp Segment
def process_audio_with_transcription(audio_path, vtt_path):
    transcription_data = parse_webvtt(vtt_path)
    y_preprocessed, sr = preprocess_audio(audio_path)

    results = []
    for entry in transcription_data:
        start_sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(entry['start_time'].split(":"))))
        end_sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(entry['end_time'].split(":"))))

        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        segment = y_preprocessed[start_sample:end_sample]

        non_silent_intervals, non_silent_timestamps = extract_non_silent_segments(segment, sr)
        weighted_pitch, weighted_rms = calculate_weighted_pitch_rms(segment, sr, non_silent_intervals)

        results.append({
            "timestamp": f"{entry['start_time']} --> {entry['end_time']}",
            "speaker": entry['speaker'],
            "non_silent_timestamps": non_silent_timestamps,
            "weighted_pitch": weighted_pitch,
            "weighted_rms": weighted_rms,
            "text": entry['text']
        })

    return pd.DataFrame(results)

# Calculate Speaker-wise Averages
def calculate_speaker_averages(df):
    speaker_averages = {}
    for speaker, group in df.groupby('speaker'):
        total_duration = sum([(end - start) for timestamps in group['non_silent_timestamps'] for start, end in timestamps])
        total_pitch = sum([row['weighted_pitch'] * sum((end - start) for start, end in row['non_silent_timestamps']) for _, row in group.iterrows()])
        total_rms = sum([row['weighted_rms'] * sum((end - start) for start, end in row['non_silent_timestamps']) for _, row in group.iterrows()])

        avg_pitch = total_pitch / total_duration if total_duration > 0 else 0
        avg_rms = total_rms / total_duration if total_duration > 0 else 0

        speaker_averages[speaker] = {'avg_pitch': avg_pitch, 'avg_rms': avg_rms}
    return speaker_averages

# Add Differences
def add_differences(df, speaker_averages):
    df['pitch_diff'] = df.apply(lambda row: row['weighted_pitch'] - speaker_averages[row['speaker']]['avg_pitch'], axis=1)
    df['rms_diff'] = df.apply(lambda row: row['weighted_rms'] - speaker_averages[row['speaker']]['avg_rms'], axis=1)
    return df

# Save Updated Results to VTT
def format_vtt_with_speaker_averages(vtt_path, df, speaker_averages):
    with open(vtt_path, 'r', encoding='utf-8') as file:
        vtt_lines = file.readlines()

    updated_lines = ["WEBVTT\n\n"]

    updated_lines.append("Average Pitch:\n")
    for speaker, stats in speaker_averages.items():
        updated_lines.append(f"{speaker}: {stats['avg_pitch']:.2f} Hz\n")

    updated_lines.append("\nAverage RMS:\n")
    for speaker, stats in speaker_averages.items():
        updated_lines.append(f"{speaker}: {stats['avg_rms']:.3f}\n")

    updated_lines.append("\n")

    for _, row in df.iterrows():
        updated_lines.append(f"{row['timestamp']}\n")
        updated_lines.append(f"<v {row['speaker']}> {row['text']}\n")
        updated_lines.append(f"Pitch: {row['weighted_pitch']:.2f} Hz | RMS: {row['weighted_rms']:.3f}\n")
        updated_lines.append(f"Pitch Difference with Average: {row['pitch_diff']:.2f} Hz\n")
        updated_lines.append(f"RMS Difference with Average: {row['rms_diff']:.3f}\n\n")

    return "".join(updated_lines)

#Main
def analyze_speaker_emotion(audio_path, vtt_path):
    df = process_audio_with_transcription(audio_path, vtt_path)
    speaker_averages = calculate_speaker_averages(df)

    df = add_differences(df, speaker_averages)

    output_text = format_vtt_with_speaker_averages(
        vtt_path,
        df,
        speaker_averages
    )

    return output_text