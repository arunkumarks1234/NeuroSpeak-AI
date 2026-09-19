"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, RefreshCw, BarChart3 } from "lucide-react";
import MicCapture, { RecordingResult } from "@/components/speech/MicCapture";

const WaveformVisualizer = dynamic(() => import("@/components/three/WaveformVisualizer"), { ssr: false });
const PhonemeTarget = dynamic(() => import("@/components/three/PhonemeTarget"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Word library (fetched lazily, seeded here for demo)
const PRACTICE_WORDS = [
  { text: "The butterfly rested on the flower.", difficulty: "moderate" },
  { text: "strength", difficulty: "hard" },
  { text: "She sells seashells by the seashore.", difficulty: "hard" },
  { text: "cat", difficulty: "easy" },
  { text: "beautiful", difficulty: "moderate" },
  { text: "hospital", difficulty: "moderate" },
  { text: "thirty-three thieves", difficulty: "hard" },
  { text: "sun", difficulty: "easy" },
];

const PHONEME_TARGETS: Record<string, string> = {
  easy: "æ", moderate: "ɛ", hard: "θ",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "#10b981",
  moderate: "#f59e0b",
  hard: "#f43f5e",
};

function getScoreColor(score: number) {
  if (score >= 85) return "#10b981";
  if (score >= 60) return "#f59e0b";
  return "#f43f5e";
}

type SessionState = "idle" | "recording" | "processing" | "scored";

interface ScoreResult {
  overall_score: number;
  accuracy_score: number;
  fluency_score: number;
  completeness_score: number;
  xp_earned: number;
  tier_promoted: boolean;
  new_tier: string;
  session_uuid: string;
  words: any[];
}

export default function PracticeSessionPage() {
  const router = useRouter();
  const analyserRef = useRef<AnalyserNode | null>(null);

  const [wordIndex, setWordIndex] = useState(0);
  const [state, setState] = useState<SessionState>("idle");
  const [result, setResult] = useState<ScoreResult | null>(null);
  const [amplitude, setAmplitude] = useState(0);
  const [sessionScore, setSessionScore] = useState<number | null>(null);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);

  const currentWord = PRACTICE_WORDS[wordIndex % PRACTICE_WORDS.length];
  const scoreColor = result ? getScoreColor(result.overall_score) : "#6366f1";
  const phonemeTarget = PHONEME_TARGETS[currentWord.difficulty] || "æ";

  const handleRecordingResult = useCallback(async (recording: RecordingResult) => {
    setState("processing");

    const userRaw = typeof window !== "undefined" ? localStorage.getItem("ns_user") : null;
    const user = userRaw ? JSON.parse(userRaw) : { id: 1 };

    try {
      const res = await fetch(`${API_BASE}/api/v2/speech/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          target_text: currentWord.text,
          audio_base64: recording.audioBase64,
          audio_duration_sec: recording.durationSec,
          language: localStorage.getItem("ns_language") || "en-US",
        }),
      });

      if (!res.ok) throw new Error("Assessment failed");
      const data = await res.json();
      setResult(data);
      setState("scored");
      setSessionScore((prev) => prev === null ? data.overall_score : (prev + data.overall_score) / 2);
      setQuestionsAnswered((q) => q + 1);

      // Save result to localStorage for results page
      localStorage.setItem("ns_last_result", JSON.stringify(data));
    } catch (err) {
      console.error(err);
      setState("idle");
    }
  }, [currentWord]);

  const handleNext = () => {
    setWordIndex((i) => i + 1);
    setResult(null);
    setState("idle");
  };

  const handleViewResults = () => {
    router.push("/practice/results");
  };

  return (
    <main className="min-h-screen flex flex-col pt-20 pb-8 px-4 relative overflow-hidden">
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: state === "scored"
          ? `radial-gradient(ellipse 60% 40% at 50% 50%, ${scoreColor}15, transparent)`
          : "radial-gradient(ellipse 60% 40% at 50% 20%, rgba(99,102,241,0.08), transparent)",
        transition: "background 1s ease",
      }} />

      <div className="relative z-10 flex flex-col items-center gap-6 max-w-5xl mx-auto w-full">

        {/* Header */}
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <div className="flex gap-2 items-center">
              {PRACTICE_WORDS.slice(0, 8).map((_, i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full transition-all duration-300"
                  style={{
                    background: i < questionsAnswered ? "#10b981" : i === wordIndex % 8 ? "#6366f1" : "rgba(255,255,255,0.1)",
                  }}
                />
              ))}
            </div>
          </div>

          {questionsAnswered > 0 && (
            <button onClick={handleViewResults} className="btn-ghost flex items-center gap-2 text-sm" id="btn-view-results">
              <BarChart3 className="w-4 h-4" />
              View Results
            </button>
          )}
        </div>

        {/* Main arena */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">

          {/* ── Left: 3D Canvas ────────────────────────────────────────── */}
          <div
            className="glass rounded-3xl overflow-hidden relative"
            style={{ height: "420px" }}
          >
            {state === "recording" || state === "idle" ? (
              <WaveformVisualizer
                analyser={analyserRef}
                scoreColor={state === "recording" ? "#6366f1" : "#334155"}
                className="absolute inset-0"
              />
            ) : (
              <PhonemeTarget
                phoneme={phonemeTarget}
                scoreColor={scoreColor}
                className="absolute inset-0"
              />
            )}

            {/* Difficulty badge */}
            <div className="absolute top-4 left-4">
              <span
                className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
                style={{
                  background: `${DIFFICULTY_COLORS[currentWord.difficulty]}15`,
                  color: DIFFICULTY_COLORS[currentWord.difficulty],
                  border: `1px solid ${DIFFICULTY_COLORS[currentWord.difficulty]}30`,
                }}
              >
                {currentWord.difficulty}
              </span>
            </div>

            {/* Processing overlay */}
            <AnimatePresence>
              {state === "processing" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex items-center justify-center"
                  style={{ background: "rgba(5,8,16,0.7)", backdropFilter: "blur(10px)" }}
                >
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
                    <p className="text-indigo-300 font-medium">Analyzing pronunciation…</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Score overlay */}
            <AnimatePresence>
              {state === "scored" && result && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="absolute bottom-0 left-0 right-0 p-4"
                  style={{ background: "linear-gradient(to top, rgba(5,8,16,0.9), transparent)" }}
                >
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-4xl font-black" style={{ color: scoreColor }}>
                        {Math.round(result.overall_score)}%
                      </div>
                      <div className="text-sm text-slate-400">Overall Score</div>
                    </div>
                    <div
                      className="flex items-center gap-2 px-4 py-2 rounded-full"
                      style={{ background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.4)" }}
                    >
                      <span className="text-yellow-400">⚡</span>
                      <span className="font-bold text-indigo-300">+{result.xp_earned} XP</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── Right: Controls ────────────────────────────────────────── */}
          <div className="flex flex-col gap-4">
            {/* Target word */}
            <div
              className="glass p-6 rounded-2xl"
              style={{ border: state === "recording" ? "1px solid rgba(99,102,241,0.5)" : undefined }}
            >
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Say this out loud
              </div>
              <div className="text-2xl font-black text-white leading-snug">
                "{currentWord.text}"
              </div>
            </div>

            {/* Mic capture */}
            <div className="glass p-6 rounded-2xl flex flex-col items-center gap-4">
              <MicCapture
                onResult={handleRecordingResult}
                onAmplitudeChange={setAmplitude}
                analyserRef={analyserRef}
                disabled={state === "processing"}
              />
            </div>

            {/* Score breakdown */}
            {state === "scored" && result && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass p-6 rounded-2xl flex flex-col gap-3"
              >
                {[
                  ["Accuracy", result.accuracy_score, "#6366f1"],
                  ["Fluency", result.fluency_score, "#8b5cf6"],
                  ["Completeness", result.completeness_score, "#06b6d4"],
                ].map(([label, value, color]) => (
                  <div key={label as string} className="flex flex-col gap-1.5">
                    <div className="flex justify-between text-sm">
                      <span style={{ color: "var(--ns-text-secondary)" }}>{label as string}</span>
                      <span className="font-bold" style={{ color: color as string }}>
                        {Math.round(value as number)}%
                      </span>
                    </div>
                    <div className="score-bar-track">
                      <motion.div
                        className="score-bar-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${value}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        style={{ background: `linear-gradient(90deg, ${color}88, ${color})` }}
                      />
                    </div>
                  </div>
                ))}

                {/* Tier promotion */}
                {result.tier_promoted && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="mt-2 p-3 rounded-xl text-center"
                    style={{ background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
                  >
                    <span className="text-violet-300 font-bold">🎉 Tier Up! You reached {result.new_tier.toUpperCase()}</span>
                  </motion.div>
                )}

                {/* Action buttons */}
                <div className="flex gap-3 mt-2">
                  <button onClick={handleNext} className="btn-ghost flex-1 flex items-center justify-center gap-2" id="btn-retry">
                    <RefreshCw className="w-4 h-4" />
                    Next Word
                  </button>
                  {questionsAnswered >= 3 && (
                    <button onClick={handleViewResults} className="btn-primary flex-1 flex items-center justify-center gap-2" id="btn-finish-session">
                      Finish Session
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
