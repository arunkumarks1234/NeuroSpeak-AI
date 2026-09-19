"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";

export interface RecordingResult {
  audioBlob: Blob;
  audioBase64: string;
  durationSec: number;
}

interface MicCaptureProps {
  onResult: (result: RecordingResult) => void;
  onAmplitudeChange?: (amplitude: number) => void;
  analyserRef?: React.MutableRefObject<AnalyserNode | null>;
  disabled?: boolean;
}

export default function MicCapture({
  onResult,
  onAmplitudeChange,
  analyserRef,
  disabled = false,
}: MicCaptureProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [amplitude, setAmplitude] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const animFrameRef = useRef<number>(0);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const localAnalyserRef = useRef<AnalyserNode | null>(null);

  const stopAmplitudeTracking = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current);
  }, []);

  const startAmplitudeTracking = useCallback((stream: MediaStream) => {
    if (!audioCtxRef.current || audioCtxRef.current.state === "closed") {
      audioCtxRef.current = new AudioContext();
    }

    const ctx = audioCtxRef.current;
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 1024;
    analyser.smoothingTimeConstant = 0.8;

    localAnalyserRef.current = analyser;
    if (analyserRef) analyserRef.current = analyser;

    const source = ctx.createMediaStreamSource(stream);
    source.connect(analyser);

    const data = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteTimeDomainData(data);
      const rms = Math.sqrt(
        data.reduce((sum, v) => sum + Math.pow((v - 128) / 128, 2), 0) / data.length
      );
      const amp = Math.min(rms * 4, 1);
      setAmplitude(amp);
      onAmplitudeChange?.(amp);
      animFrameRef.current = requestAnimationFrame(tick);
    };

    tick();
  }, [analyserRef, onAmplitudeChange]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      chunksRef.current = [];
      startTimeRef.current = Date.now();

      const mr = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = async () => {
        setIsProcessing(true);
        const durationSec = (Date.now() - startTimeRef.current) / 1000;
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });

        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(",")[1];
          setIsProcessing(false);
          onResult({ audioBlob: blob, audioBase64: base64, durationSec });
        };
        reader.readAsDataURL(blob);

        // Cleanup
        stream.getTracks().forEach((t) => t.stop());
        stopAmplitudeTracking();
        setAmplitude(0);
        if (analyserRef) analyserRef.current = null;
      };

      mr.start(100);
      mediaRecorderRef.current = mr;
      startAmplitudeTracking(stream);
      setIsRecording(true);
      setPermissionDenied(false);
    } catch (err: any) {
      if (err.name === "NotAllowedError") setPermissionDenied(true);
      console.error("Mic error:", err);
    }
  }, [onResult, startAmplitudeTracking, stopAmplitudeTracking, analyserRef]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }, []);

  const handleClick = useCallback(() => {
    if (disabled || isProcessing) return;
    if (isRecording) stopRecording();
    else startRecording();
  }, [disabled, isProcessing, isRecording, startRecording, stopRecording]);

  // Ring scale based on amplitude
  const ringScale = 1 + amplitude * 0.6;

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Mic button with pulse rings */}
      <div className="relative flex items-center justify-center">
        {/* Amplitude rings */}
        {isRecording && (
          <>
            <div
              className="absolute rounded-full border border-indigo-500/30 transition-transform duration-75"
              style={{
                width: `${80 + amplitude * 40}px`,
                height: `${80 + amplitude * 40}px`,
              }}
            />
            <div
              className="absolute rounded-full border border-violet-500/20 transition-transform duration-100"
              style={{
                width: `${100 + amplitude * 60}px`,
                height: `${100 + amplitude * 60}px`,
              }}
            />
          </>
        )}

        <button
          onClick={handleClick}
          disabled={disabled}
          className={`
            relative z-10 w-16 h-16 rounded-full flex items-center justify-center
            transition-all duration-300 cursor-pointer
            ${isRecording
              ? "bg-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.6)] scale-110"
              : "bg-gradient-to-br from-indigo-500 to-violet-600 shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:scale-110"
            }
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
          id="mic-capture-btn"
        >
          {isProcessing ? (
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-6 h-6 text-white" />
          ) : (
            <Mic className="w-6 h-6 text-white" />
          )}
        </button>
      </div>

      {/* Status text */}
      <p className="text-sm font-medium" style={{ color: "var(--ns-text-secondary)" }}>
        {permissionDenied
          ? "Microphone access denied — check browser settings"
          : isProcessing
          ? "Processing audio…"
          : isRecording
          ? "Recording… tap to stop"
          : "Tap to start recording"}
      </p>
    </div>
  );
}
