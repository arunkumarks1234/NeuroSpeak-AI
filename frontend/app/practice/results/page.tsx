"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, RotateCcw, LayoutDashboard, RadarIcon } from "lucide-react";
import ScoreDisplay from "@/components/speech/ScoreDisplay";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip
} from "recharts";

function getScoreColor(score: number) {
  if (score >= 85) return "#10b981";
  if (score >= 60) return "#f59e0b";
  return "#f43f5e";
}

function getScoreLabel(score: number) {
  if (score >= 90) return "Excellent!";
  if (score >= 80) return "Great job!";
  if (score >= 70) return "Good effort!";
  if (score >= 60) return "Keep practicing!";
  return "Let's try again!";
}

const COACHING_TIPS: Record<string, string[]> = {
  high: [
    "Outstanding pronunciation! Move to harder words.",
    "Your fluency is excellent — try complex sentences next.",
  ],
  mid: [
    "Focus on slower, deliberate articulation for difficult phonemes.",
    "Try recording yourself and comparing with the reference audio.",
    "Practice the target phoneme in isolation before in words.",
  ],
  low: [
    "Start with simpler words and build up gradually.",
    "Warm up your speech muscles with lip and tongue exercises.",
    "Listen carefully to the reference pronunciation before speaking.",
  ],
};

export default function PracticeResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const raw = localStorage.getItem("ns_last_result");
    if (raw) setResult(JSON.parse(raw));
  }, []);

  if (!result) {
    return (
      <main className="min-h-screen flex items-center justify-center pt-20">
        <div className="flex flex-col items-center gap-4">
          <p className="text-slate-400">No session results found.</p>
          <button onClick={() => router.push("/practice/session")} className="btn-primary">
            Start a Session
          </button>
        </div>
      </main>
    );
  }

  const scoreColor = getScoreColor(result.overall_score);
  const scoreLabel = getScoreLabel(result.overall_score);
  const tipCategory = result.overall_score >= 85 ? "high" : result.overall_score >= 65 ? "mid" : "low";

  const radarData = [
    { metric: "Accuracy", score: result.accuracy_score },
    { metric: "Fluency", score: result.fluency_score },
    { metric: "Completeness", score: result.completeness_score },
    { metric: "Prosody", score: result.prosody_score || 75 },
  ];

  return (
    <main className="min-h-screen flex flex-col pt-20 pb-12 px-6 relative">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: `radial-gradient(ellipse 70% 40% at 50% 0%, ${scoreColor}10, transparent)`,
      }} />

      <div className="relative z-10 max-w-5xl mx-auto w-full">

        {/* Back button */}
        <button
          onClick={() => router.push("/practice/session")}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8"
          id="btn-back-to-session"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Practice
        </button>

        {/* ── Hero Score ──────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass p-10 rounded-3xl text-center mb-6"
          style={{
            border: `1px solid ${scoreColor}30`,
            boxShadow: `0 0 60px ${scoreColor}15`,
          }}
        >
          {/* Animated score ring */}
          <div
            className="relative w-36 h-36 mx-auto mb-4"
            style={{
              background: `conic-gradient(${scoreColor} ${result.overall_score}%, rgba(255,255,255,0.04) 0%)`,
              borderRadius: "50%",
              boxShadow: `0 0 50px ${scoreColor}35`,
            }}
          >
            <div
              className="absolute inset-[10px] flex flex-col items-center justify-center rounded-full"
              style={{ background: "var(--ns-bg-2)" }}
            >
              <span className="text-3xl font-black" style={{ color: scoreColor }}>
                {Math.round(result.overall_score)}%
              </span>
              <span className="text-xs text-slate-500">Overall</span>
            </div>
          </div>

          <h1 className="text-3xl font-black text-white mb-2">{scoreLabel}</h1>
          <p className="text-slate-400 mb-6">Session complete · {result.difficulty} difficulty</p>

          {/* XP + Tier row */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <div
              className="flex items-center gap-2 px-5 py-2.5 rounded-full"
              style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)" }}
            >
              <span className="text-yellow-400 text-xl">⚡</span>
              <span className="font-bold text-indigo-300 text-lg">+{result.xp_earned} XP</span>
            </div>

            {result.tier_promoted && (
              <motion.div
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 15 }}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full"
                style={{ background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.4)" }}
              >
                <span className="text-xl">🏅</span>
                <span className="font-bold text-violet-300 text-lg">
                  Tier Up → {result.new_tier.toUpperCase()}
                </span>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* ── Grid ────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

          {/* Radar chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass p-6 rounded-2xl"
          >
            <div className="flex items-center gap-2 mb-4">
              <RadarIcon className="w-5 h-5 text-indigo-400" />
              <h2 className="font-bold text-white">Metric Radar</h2>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.05)" />
                <PolarAngleAxis
                  dataKey="metric"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                />
                <Radar
                  name="Score"
                  dataKey="score"
                  stroke={scoreColor}
                  fill={scoreColor}
                  fillOpacity={0.2}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(5,8,16,0.9)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    color: "white",
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Phoneme breakdown */}
          {result.words?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="glass p-6 rounded-2xl overflow-y-auto"
              style={{ maxHeight: 320 }}
            >
              <h2 className="font-bold text-white mb-4">Word & Phoneme Detail</h2>
              <div className="flex flex-col gap-4">
                {result.words.map((word: any, wi: number) => (
                  <div key={wi}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold text-white">{word.word}</span>
                      {word.error_type && (
                        <span className="text-xs px-2 py-0.5 rounded-full text-rose-400 bg-rose-500/10 border border-rose-500/20">
                          {word.error_type}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {word.phonemes?.map((ph: any, pi: number) => {
                        const c = getScoreColor(ph.score);
                        return (
                          <div
                            key={pi}
                            className="flex flex-col items-center px-2 py-1 rounded-lg"
                            style={{ background: `${c}12`, border: `1px solid ${c}25` }}
                          >
                            <span className="text-sm font-bold font-mono" style={{ color: c }}>{ph.phoneme}</span>
                            <span className="text-xs text-slate-500">{Math.round(ph.score)}%</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Coaching tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass p-6 rounded-2xl mb-6"
        >
          <h2 className="font-bold text-white mb-4">💡 Coaching Recommendations</h2>
          <div className="flex flex-col gap-3">
            {COACHING_TIPS[tipCategory].map((tip, i) => (
              <div key={i} className="flex items-start gap-3">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                  style={{ background: "rgba(99,102,241,0.2)", color: "#a5b4fc" }}
                >
                  {i + 1}
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">{tip}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-4 justify-center">
          <button
            onClick={() => router.push("/practice/session")}
            className="btn-ghost flex items-center gap-2"
            id="btn-practice-again"
          >
            <RotateCcw className="w-4 h-4" />
            Practice Again
          </button>
          <button
            onClick={() => router.push("/dashboard/patient")}
            className="btn-primary flex items-center gap-2"
            id="btn-go-to-dashboard"
          >
            <LayoutDashboard className="w-4 h-4" />
            View Dashboard
          </button>
        </div>
      </div>
    </main>
  );
}
