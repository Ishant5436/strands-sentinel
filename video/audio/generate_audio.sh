#!/bin/bash
# Synthesizes the demo's audio track entirely from ffmpeg lavfi sources:
# an ambient synth pad plus a handful of short UI sound cues, mixed at the
# exact timestamps computed from the video's own scene-duration constants
# (see video/src/theme.ts SCENE_FRAMES / TransitionSeries overlap).
#
# No licensed music or recorded samples are used, matching the fallback
# the task itself authorized when no good TTS voice is available.
#
# Gain levels below were tuned by measuring true overall peak/RMS via
# `ffmpeg -i f.wav -af astats -f null -` (the cumulative "Overall" block,
# NOT `astats=reset=1` piped through `tail`, which only reports the last
# analysis window and reads as false near-silence after any fade-out).
set -euo pipefail
cd "$(dirname "$0")"

DURATION=83.4
SR=44100

echo "generating ambient pad..."
ffmpeg -y -loglevel error \
  -f lavfi -i "sine=frequency=110:duration=${DURATION}:sample_rate=${SR}" \
  -f lavfi -i "sine=frequency=164.81:duration=${DURATION}:sample_rate=${SR}" \
  -f lavfi -i "sine=frequency=220:duration=${DURATION}:sample_rate=${SR}" \
  -filter_complex "\
    [0][1][2]amix=inputs=3:duration=longest:normalize=0, \
    tremolo=f=0.12:d=0.25, \
    volume=0.45, \
    afade=t=in:st=0:d=3, \
    afade=t=out:st=79:d=4 \
  " \
  -ar ${SR} -ac 2 ambient.wav

echo "generating click.wav..."
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=900:duration=0.05:sample_rate=${SR}" \
  -af "afade=t=in:st=0:d=0.005,afade=t=out:st=0.02:d=0.03,volume=2.5" -ar ${SR} -ac 2 click.wav

echo "generating alert.wav (two-tone rising)..."
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=700:duration=0.15:sample_rate=${SR}" \
  -af "afade=t=in:st=0:d=0.01,afade=t=out:st=0.1:d=0.05,volume=2.8" -ar ${SR} -ac 2 alert_a.wav
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=1000:duration=0.18:sample_rate=${SR}" \
  -af "afade=t=in:st=0:d=0.01,afade=t=out:st=0.12:d=0.06,volume=2.8" -ar ${SR} -ac 2 alert_b.wav
ffmpeg -y -loglevel error -i alert_a.wav -i alert_b.wav -filter_complex "[0][1]concat=n=2:v=0:a=1" -ar ${SR} -ac 2 alert.wav

echo "generating success.wav (ascending triad)..."
for i in 0 1 2; do
  freq=$(python3 -c "print([523.25,659.25,783.99][$i])")
  ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=${freq}:duration=0.14:sample_rate=${SR}" \
    -af "afade=t=in:st=0:d=0.01,afade=t=out:st=0.09:d=0.05,volume=2.5" -ar ${SR} -ac 2 "note_${i}.wav"
done
ffmpeg -y -loglevel error -i note_0.wav -i note_1.wav -i note_2.wav \
  -filter_complex "[0][1]acrossfade=d=0.03[ab];[ab][2]acrossfade=d=0.03" -ar ${SR} -ac 2 success.wav

echo "generating danger.wav (low ominous tone)..."
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=90:duration=0.6:sample_rate=${SR}" \
  -af "afade=t=in:st=0:d=0.05,afade=t=out:st=0.35:d=0.25,volume=1.8" -ar ${SR} -ac 2 danger.wav

echo "generating whoosh.wav (outro entrance)..."
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=300:duration=0.8:sample_rate=${SR}" \
  -af "afade=t=in:st=0:d=0.3,afade=t=out:st=0.5:d=0.3,volume=1.6" -ar ${SR} -ac 2 whoosh.wav

echo "mixing SFX bed (avoiding anullsrc; amix inputs are real signals, then padded/trimmed)..."
ffmpeg -y -loglevel error \
  -i danger.wav -i alert.wav -i click.wav -i success.wav -i whoosh.wav \
  -filter_complex "\
    [0]adelay=8330|8330[a0]; \
    [1]adelay=47200|47200[a1]; \
    [2]adelay=49870|49870[a2]; \
    [3]adelay=58530|58530[a3]; \
    [4]adelay=76400|76400[a4]; \
    [a0][a1][a2][a3][a4]amix=inputs=5:duration=longest:normalize=0,apad \
  " \
  -ar ${SR} -ac 2 -t ${DURATION} sfx_bed.wav

echo "mixing final track (ambient + sfx bed, limiter as clip safety net)..."
ffmpeg -y -loglevel error \
  -i ambient.wav -i sfx_bed.wav \
  -filter_complex "[0][1]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9" \
  -ar ${SR} -ac 2 -t ${DURATION} full_track.wav

echo "=== final levels ==="
ffmpeg -i full_track.wav -af astats -f null - 2>&1 | grep -A20 "Overall" | grep -E "Peak level|RMS level"
echo "done: audio/full_track.wav"
