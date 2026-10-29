import { PCMEncoder } from "./pcm";

export class VoiceRecorder {
    private stream: MediaStream | null = null;

    private context: AudioContext | null = null;

    private source: MediaStreamAudioSourceNode | null = null;

    private processor: ScriptProcessorNode | null = null;

    private callback: ((buffer: ArrayBuffer) => void) | null = null;

    async start(
        onAudio: (buffer: ArrayBuffer) => void,
    ) {
        if (this.context) {
            return;
        }

        this.callback = onAudio;

        let stream: MediaStream;
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1,
                },
            });
        } else {
            const getUserMedia = (navigator as any).getUserMedia ||
                                 (navigator as any).webkitGetUserMedia ||
                                 (navigator as any).mozGetUserMedia;
            
            if (!getUserMedia) {
                throw new Error("Microphone access is not supported. Please ensure you are using HTTPS or localhost.");
            }
            
            stream = await new Promise((resolve, reject) => {
                getUserMedia.call(navigator, {
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        channelCount: 1,
                    },
                }, resolve, reject);
            });
        }
        
        this.stream = stream;

        this.context = new AudioContext();

        const sampleRate = this.context.sampleRate;

        console.log(
            "[VOICE] Sample Rate:",
            sampleRate,
        );

        this.source =
            this.context.createMediaStreamSource(
                this.stream,
            );

        this.processor =
            this.context.createScriptProcessor(
                4096,
                1,
                1,
            );

        this.processor.onaudioprocess = (event) => {

            const samples =
                event.inputBuffer.getChannelData(0);

            const pcm =
                PCMEncoder.encode(
                    samples,
                    sampleRate,
                );

            console.log(
                "[VOICE] Resampled →",
                PCMEncoder.TARGET_SAMPLE_RATE,
            );

            this.callback?.(pcm);
        };

        this.source.connect(this.processor);

        this.processor.connect(
            this.context.destination,
        );

        console.log("[VOICE] Recorder started");
    }

    stop() {

        this.processor?.disconnect();

        this.source?.disconnect();

        this.stream?.getTracks().forEach(track =>
            track.stop(),
        );

        this.context?.close();

        this.processor = null;
        this.source = null;
        this.context = null;
        this.stream = null;

        console.log("[VOICE] Recorder stopped");
    }

    get recording() {
        return this.context !== null;
    }
}
