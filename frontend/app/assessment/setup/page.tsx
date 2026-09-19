"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Globe, Mic, Volume2, ArrowRight, CheckCircle2 } from "lucide-react";

const LANGUAGES = [
  { code: "en-US", label: "English (US)", flag: "🇺🇸" },
  { code: "en-GB", label: "English (UK)", flag: "🇬🇧" },
  { code: "hi-IN", label: "Hindi", flag: "🇮🇳" },
  { code: "kn-IN", label: "Kannada", flag: "🇮🇳" },
  { code: "ta-IN", label: "Tamil", flag: "🇮🇳" },
  { code: "es-ES", label: "Spanish", flag: "🇪🇸" },
  { code: "fr-FR", label: "French", flag: "🇫🇷" },
  { code: "de-DE", label: "German", flag: "🇩🇪" },
];

const BASELINE_WORDS = ["cat", "butterfly", "strength"];

export default function AssessmentSetupPage() {
  const router = useRouter();
  const [language, setLanguage] = useState("en-US");
  const [step, setStep] = useState<"language" | "mic" | "baseline">("language");
  const [micOk, setMicOk] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [baselineIdx, setBaselineIdx] = useState(0);
  const [baselineResults, setBaselineResults] = useState<boolean[]>([]);

  const streamRef = useRef<MediaStream | null>(null);
  const animRef = useRef<number>(0);

  const testMic = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx = new AudioContext();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);

      const tick = () => {
        analyser.getByteTimeDomainData(data);
        const rms = Math.sqrt(data.reduce((s, v) => s + Math.pow((v - 128) / 128, 2), 0) / data.length);
        setMicLevel(Math.min(rms * 5, 1));
        animRef.current = requestAnimationFrame(tick);
      };
      tick();

      setTimeout(() => {
        cancelAnimationFrame(animRef.current);
        stream.getTracks().forEach((t) => t.stop());
        setMicOk(true);
        setMicLevel(0);
      }, 3000);
    } catch {
      alert("Microphone permission denied. Please allow microphone access.");
    }
  };

  const handleBaselineWord = (success: boolean) => {
    const next = [...baselineResults, success];
    setBaselineResults(next);
    if (baselineIdx < BASELINE_WORDS.length - 1) {
      setBaselineIdx(baselineIdx + 1);
    }
  };

  const handleStart = () => {
    const user = typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("ns_user") || '{"preferred_language":"en-US"}')
      : { preferred_language: "en-US" };
    localStorage.setItem("ns_language", language);
    router.push("/practice/session");
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 pt-20 pb-12">
      {/* Background glow */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.12), transparent)",
      }} />

      <div className="w-full max-w-lg relative z-10">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10 text-center">
          <h1 className="text-3xl font-black text-white mb-2">Setup Your Session</h1>
          <p className="text-slate-400">Configure your language, test your microphone, and calibrate baseline</p>
        </motion.div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8 justify-center">
          {(["language", "mic", "baseline"] as const).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                  step === s ? "text-white" : step > s || (s === "mic" && step === "baseline") || (s === "language" && step !== "language")
                    ? "text-emerald-400" : "text-slate-600"
                }`}
                style={{
                  background: step === s ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "rgba(255,255,255,0.05)",
                  border: `1px solid ${step === s ? "transparent" : "rgba(255,255,255,0.08)"}`,
                }}
              >
                {i + 1}
              </div>
              {i < 2 && <div className="w-12 h-px" style={{ background: "rgba(255,255,255,0.08)" }} />}
            </div>
          ))}
        </div>

        {/* ── Step 1: Language ──────────────────────────────────────────── */}
        {step === "language" && (
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="glass p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-6">
              <Globe className="w-6 h-6 text-indigo-400" />
              <h2 className="text-xl font-bold text-white">Select Language</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-6">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`flex items-center gap-3 p-3 rounded-xl text-left transition-all duration-200 ${
                    language === lang.code ? "" : "hover:bg-white/5"
                  }`}
                  style={language === lang.code ? {
                    background: "rgba(99,102,241,0.15)",
                    border: "1px solid rgba(99,102,241,0.4)",
                  } : {
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                  id={`lang-${lang.code}`}
                >
                  <span className="text-xl">{lang.flag}</span>
                  <span className="text-sm font-medium text-white">{lang.label}</span>
                </button>
              ))}
            </div>
            <button onClick={() => setStep("mic")} className="btn-primary w-full flex items-center justify-center gap-2" id="btn-next-to-mic">
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        )}

        {/* ── Step 2: Microphone ───────────────────────────────────────── */}
        {step === "mic" && (
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="glass p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-6">
              <Mic className="w-6 h-6 text-indigo-400" />
              <h2 className="text-xl font-bold text-white">Microphone Test</h2>
            </div>

            {/* Level bar */}
            <div className="flex flex-col items-center gap-6 mb-8">
              <div
                className="relative w-32 h-32 rounded-full flex items-center justify-center"
                style={{
                  background: `conic-gradient(#6366f1 ${micLevel * 100}%, rgba(255,255,255,0.04) 0%)`,
                  boxShadow: micLevel > 0.1 ? "0 0 30px rgba(99,102,241,0.4)" : "none",
                }}
              >
                <div
                  className="w-24 h-24 rounded-full flex items-center justify-center"
                  style={{ background: "var(--ns-bg-2)" }}
                >
                  <Mic className={`w-8 h-8 ${micLevel > 0.1 ? "text-indigo-400" : "text-slate-600"}`} />
                </div>
              </div>

              {micOk && (
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-semibold">Microphone detected!</span>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              {!micOk && (
                <button onClick={testMic} className="btn-ghost w-full" id="btn-test-mic">
                  Test Microphone (3 seconds)
                </button>
              )}
              <button
                onClick={() => setStep("baseline")}
                disabled={!micOk}
                className={`btn-primary w-full flex items-center justify-center gap-2 ${!micOk ? "opacity-50 cursor-not-allowed" : ""}`}
                id="btn-next-to-baseline"
              >
                Continue <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}

        {/* ── Step 3: Baseline ─────────────────────────────────────────── */}
        {step === "baseline" && (
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="glass p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-6">
              <Volume2 className="w-6 h-6 text-indigo-400" />
              <h2 className="text-xl font-bold text-white">Baseline Check</h2>
            </div>
            <p className="text-slate-400 text-sm mb-6">
              Say each word clearly to help calibrate your session difficulty.
              {baselineResults.length < BASELINE_WORDS.length
                ? ` Word ${baselineResults.length + 1} of ${BASELINE_WORDS.length}:`
                : " All done!"}
            </p>

            {baselineResults.length < BASELINE_WORDS.length ? (
              <>
                <div
                  className="text-center py-10 rounded-2xl mb-6"
                  style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)" }}
                >
                  <div className="text-5xl font-black gradient-text mb-2">
                    {BASELINE_WORDS[baselineIdx]}
                  </div>
                  <div className="text-sm text-slate-500">Difficulty: {
                    baselineIdx === 0 ? "Easy" : baselineIdx === 1 ? "Moderate" : "Hard"
                  }</div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => handleBaselineWord(false)} className="btn-ghost flex-1" id="baseline-retry">
                    Skip
                  </button>
                  <button onClick={() => handleBaselineWord(true)} className="btn-primary flex-1" id="baseline-ok">
                    I said it ✓
                  </button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="text-center">
                  <div className="text-4xl mb-2">🎯</div>
                  <p className="text-emerald-400 font-semibold">Calibration complete!</p>
                </div>
                <button onClick={handleStart} className="btn-primary w-full flex items-center justify-center gap-2" id="btn-start-session">
                  Start Practice Session <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </main>
  );
}
