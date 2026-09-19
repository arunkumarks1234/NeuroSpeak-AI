"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ScoreDisplayProps {
  accuracy: number;
  fluency: number;
  completeness: number;
  overall: number;
  words?: Array<{
    word: string;
    accuracy_score: number;
    error_type?: string | null;
    phonemes: Array<{ phoneme: string; score: number; error_type?: string | null }>;
  }>;
  xpEarned?: number;
}

function AnimatedNumber({ target, duration = 1200 }: { target: number; duration?: number }) {
  const [value, setValue] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    startRef.current = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress >= 1) clearInterval(interval);
    }, 16);
    return () => clearInterval(interval);
  }, [target, duration]);

  return <span>{value}</span>;
}

function ScoreGauge({
  label,
  value,
  color,
  delay,
}: {
  label: string;
  value: number;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className="flex flex-col gap-2"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium" style={{ color: "var(--ns-text-secondary)" }}>
          {label}
        </span>
        <span className="text-sm font-bold" style={{ color }}>
          <AnimatedNumber target={Math.round(value)} />%
        </span>
      </div>
      <div className="score-bar-track">
        <motion.div
          className="score-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ delay: delay + 0.2, duration: 1, ease: "easeOut" }}
          style={{ background: `linear-gradient(90deg, ${color}88, ${color})` }}
        />
      </div>
    </motion.div>
  );
}

function getScoreColor(score: number): string {
  if (score >= 85) return "#10b981"; // emerald
  if (score >= 60) return "#f59e0b"; // amber
  return "#f43f5e"; // coral
}

function PhonemeChip({
  phoneme,
  score,
  error_type,
}: {
  phoneme: string;
  score: number;
  error_type?: string | null;
}) {
  const color = getScoreColor(score);
  return (
    <div
      className="inline-flex flex-col items-center gap-1 p-2 rounded-xl"
      style={{
        background: `${color}15`,
        border: `1px solid ${color}30`,
        minWidth: "48px",
      }}
      title={error_type ? `Error: ${error_type}` : `Score: ${score.toFixed(0)}%`}
    >
      <span className="text-base font-bold font-mono" style={{ color }}>
        {phoneme}
      </span>
      <span className="text-xs" style={{ color: "var(--ns-text-muted)" }}>
        {Math.round(score)}%
      </span>
    </div>
  );
}

export default function ScoreDisplay({
  accuracy,
  fluency,
  completeness,
  overall,
  words = [],
  xpEarned = 0,
}: ScoreDisplayProps) {
  const overallColor = getScoreColor(overall);

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Overall circle */}
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className="flex flex-col items-center gap-2"
      >
        <div
          className="relative flex items-center justify-center rounded-full"
          style={{
            width: 120,
            height: 120,
            background: `conic-gradient(${overallColor} ${overall}%, rgba(255,255,255,0.05) 0%)`,
            boxShadow: `0 0 40px ${overallColor}40`,
          }}
        >
          <div
            className="flex flex-col items-center justify-center rounded-full"
            style={{
              width: 90,
              height: 90,
              background: "var(--ns-bg-2)",
            }}
          >
            <span className="text-2xl font-black" style={{ color: overallColor }}>
              <AnimatedNumber target={Math.round(overall)} />
            </span>
            <span className="text-xs" style={{ color: "var(--ns-text-muted)" }}>Overall</span>
          </div>
        </div>

        {/* XP badge */}
        {xpEarned > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex items-center gap-2 px-4 py-1.5 rounded-full"
            style={{
              background: "rgba(99, 102, 241, 0.2)",
              border: "1px solid rgba(99, 102, 241, 0.4)",
            }}
          >
            <span className="text-yellow-400 text-lg">⚡</span>
            <span className="font-bold text-sm" style={{ color: "#a5b4fc" }}>
              +{xpEarned} XP
            </span>
          </motion.div>
        )}
      </motion.div>

      {/* Score gauges */}
      <div className="flex flex-col gap-3">
        <ScoreGauge label="Accuracy" value={accuracy} color="#6366f1" delay={0.2} />
        <ScoreGauge label="Fluency" value={fluency} color="#8b5cf6" delay={0.35} />
        <ScoreGauge label="Completeness" value={completeness} color="#06b6d4" delay={0.5} />
      </div>

      {/* Phoneme breakdown */}
      {words.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex flex-col gap-3"
        >
          <h3 className="text-sm font-semibold" style={{ color: "var(--ns-text-secondary)" }}>
            Phoneme Breakdown
          </h3>
          {words.map((word, wi) => (
            <div key={wi} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">{word.word}</span>
                {word.error_type && (
                  <span
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      background: "rgba(244, 63, 94, 0.15)",
                      color: "#f43f5e",
                      border: "1px solid rgba(244, 63, 94, 0.3)",
                    }}
                  >
                    {word.error_type}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {word.phonemes.map((ph, pi) => (
                  <PhonemeChip
                    key={pi}
                    phoneme={ph.phoneme}
                    score={ph.score}
                    error_type={ph.error_type}
                  />
                ))}
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
