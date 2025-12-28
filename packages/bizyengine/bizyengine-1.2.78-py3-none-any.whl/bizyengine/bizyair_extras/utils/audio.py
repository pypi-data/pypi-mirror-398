import io

import av
import torchaudio


# Adapted from ComfyUI save_audio function
def save_audio(
    audio,
    filename_prefix="ComfyUI",
    format="flac",
    prompt=None,
    extra_pnginfo=None,
    quality="128k",
) -> io.BytesIO:
    # Opus supported sample rates
    OPUS_RATES = [8000, 12000, 16000, 24000, 48000]

    for batch_number, waveform in enumerate(audio["waveform"].cpu()):
        # Use original sample rate initially
        sample_rate = audio["sample_rate"]

        # Handle Opus sample rate requirements
        if format == "opus":
            if sample_rate > 48000:
                sample_rate = 48000
            elif sample_rate not in OPUS_RATES:
                # Find the next highest supported rate
                for rate in sorted(OPUS_RATES):
                    if rate > sample_rate:
                        sample_rate = rate
                        break
                if sample_rate not in OPUS_RATES:  # Fallback if still not supported
                    sample_rate = 48000

            # Resample if necessary
            if sample_rate != audio["sample_rate"]:
                waveform = torchaudio.functional.resample(
                    waveform, audio["sample_rate"], sample_rate
                )

        # Create output with specified format
        output_buffer = io.BytesIO()
        output_container = av.open(output_buffer, mode="w", format=format)

        # Set up the output stream with appropriate properties
        if format == "opus":
            out_stream = output_container.add_stream("libopus", rate=sample_rate)
            if quality == "64k":
                out_stream.bit_rate = 64000
            elif quality == "96k":
                out_stream.bit_rate = 96000
            elif quality == "128k":
                out_stream.bit_rate = 128000
            elif quality == "192k":
                out_stream.bit_rate = 192000
            elif quality == "320k":
                out_stream.bit_rate = 320000
        elif format == "mp3":
            out_stream = output_container.add_stream("libmp3lame", rate=sample_rate)
            if quality == "V0":
                # TODO i would really love to support V3 and V5 but there doesn't seem to be a way to set the qscale level, the property below is a bool
                out_stream.codec_context.qscale = 1
            elif quality == "128k":
                out_stream.bit_rate = 128000
            elif quality == "320k":
                out_stream.bit_rate = 320000
        else:  # format == "flac":
            out_stream = output_container.add_stream("flac", rate=sample_rate)

        frame = av.AudioFrame.from_ndarray(
            waveform.movedim(0, 1).reshape(1, -1).float().numpy(),
            format="flt",
            layout="mono" if waveform.shape[0] == 1 else "stereo",
        )
        frame.sample_rate = sample_rate
        frame.pts = 0
        output_container.mux(out_stream.encode(frame))

        # Flush encoder
        output_container.mux(out_stream.encode(None))

        # Close containers
        output_container.close()

        # Write the output to file
        output_buffer.seek(0)
        return output_buffer
