
import subprocess
import re

def detect(filepath, dB=-40, duration=3):
    cmd1 = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'info',
            '-i',
            ]
    cmd2 = [
            '-af',
            f'silencedetect=n={dB}dB:d={duration}',
            '-f',
            'null',
            '-',
            ]

    # Compile commands
    cmd = cmd1
    cmd.append(filepath)
    cmd = cmd + cmd2

    process = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True
            )
    output = process.stderr
    return output

def parse(stderr):
    silences = []

    for line in stderr.splitlines():
        if 'silence_start' in line:
            t = float(re.search(r'silence_start: ([0-9.]+)', line).group(1))
            silences.append({'start': t})
        elif 'silence_end' in line:
            matchs = re.search(r'silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)', line
                            )
            silences[-1]['end'] = float(matchs.group(1))
            silences[-1]['duration'] = float(matchs.group(2))

    return silences

def polish(silences, polish_duration=1):
    """
    silences = [
            { 'start': xx.xxx, 'end': yy.yyy, 'duration': zz.zzz },
            ...
        ]
    """
    output = []
    interval = None
    for i in silences:
        if interval is None:
            interval = i
        else:
            gap = i['start'] - interval['end']
            if gap < polish_duration:
                # merge
                interval['end'] = i['end']
                interval['duration'] = interval['end'] - interval['start']
            else:
                # store interval and start a new interval
                output.append(interval)
                interval = i
    output.append(interval)
    return output
