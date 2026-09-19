"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Mic, Brain, BarChart3, Shield, Zap, Users } from "lucide-react";

// Dynamic import for Three.js (no SSR)
const PhoneticParticleField = dynamic(
  () => import("@/components/three/PhoneticParticleField"),
  { ssr: false }
);

const FEATURES = [
  {
    icon: Mic,
    title: "Pronunciation AI",
    desc: "Azure-powered phoneme-level accuracy scoring with real-time feedback",
    color: "#6366f1",
  },
  {
    icon: Zap,
    title: "Gamified Progress",
    desc: "Bronze to Master leagues, daily quests, and XP streaks that keep you motivated",
    color: "#8b5cf6",
  },
  {
    icon: Brain,
    title: "Neural Analysis",
    desc: "Whisper ASR + Wav2Vec2 embeddings + Praat acoustic feature extraction",
    color: "#06b6d4",
  },
  {
    icon: BarChart3,
    title: "Clinical Dashboard",
    desc: "Longitudinal phoneme heatmaps and exportable PDF/CSV reports for SLPs",
    color: "#10b981",
  },
  {
    icon: Shield,
    title: "Dysarthria Support",
    desc: "Specialized model tuned for dysarthric speech patterns and severity classification",
    color: "#f59e0b",
  },
  {
    icon: Users,
    title: "Doctor Portal",
    desc: "Assign custom word sets, monitor patient sessions, and prescribe exercises",
    color: "#ec4899",
  },
];

const TIER_BADGES = [
  { label: "Bronze", color: "#cd7f32", emoji: "🥉" },
  { label: "Silver", color: "#c0c0c0", emoji: "🥈" },
  { label: "Gold", color: "#ffd700", emoji: "🥇" },
  { label: "Master", color: "#7c3aed", emoji: "💎" },
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden">
      {/* ── 3D Background Canvas ─────────────────────────────────────────── */}
      <div className="fixed inset-0 z-0">
        <PhoneticParticleField className="w-full h-full" />
      </div>

      {/* ── Gradient overlay for readability ────────────────────────────── */}
      <div
        className="fixed inset-0 z-[1] pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 60% at 50% 0%, rgba(5,8,16,0) 0%, rgba(5,8,16,0.85) 100%)",
        }}
      />

      {/* ── Content ──────────────────────────────────────────────────────── */}
      <div className="relative z-10">

        {/* ── Hero Section ──────────────────────────────────────────────── */}
        <section className="min-h-screen flex flex-col items-center justify-center px-6 pt-24 pb-16">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8 flex items-center gap-2 px-4 py-2 rounded-full"
            style={{
              background: "rgba(99, 102, 241, 0.12)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
            }}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-medium text-indigo-300">
              AI-Powered Speech Rehabilitation
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-center font-black leading-[1.05] tracking-tight max-w-4xl"
            style={{ fontSize: "clamp(3rem, 8vw, 6rem)" }}
          >
            <span className="text-white">Speak Clearly.</span>
            <br />
            <span className="gradient-text">Level Up Daily.</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.25 }}
            className="mt-6 text-center max-w-2xl text-lg leading-relaxed"
            style={{ color: "var(--ns-text-secondary)" }}
          >
            The world's first gamified speech therapy platform powered by Whisper ASR,
            Azure Pronunciation Assessment, and real-time 3D phoneme visualization —
            designed for patients and speech-language pathologists.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <Link href="/auth" id="cta-begin-assessment">
              <button className="btn-primary flex items-center gap-3 text-base">
                Begin Assessment
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            <Link href="/auth?role=clinician" id="cta-clinician-portal">
              <button className="btn-ghost text-base">
                Clinician Portal
              </button>
            </Link>
          </motion.div>

          {/* Tier badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="mt-16 flex items-center gap-6 flex-wrap justify-center"
          >
            {TIER_BADGES.map((tier, i) => (
              <motion.div
                key={tier.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + i * 0.1 }}
                className="flex flex-col items-center gap-1"
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl float-anim"
                  style={{
                    background: `${tier.color}15`,
                    border: `1px solid ${tier.color}30`,
                    animationDelay: `${i * 0.8}s`,
                    boxShadow: `0 0 20px ${tier.color}20`,
                  }}
                >
                  {tier.emoji}
                </div>
                <span className="text-xs font-semibold" style={{ color: tier.color }}>
                  {tier.label}
                </span>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ── Features Grid ─────────────────────────────────────────────── */}
        <section className="relative px-6 pb-24 max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-black text-white mb-4">
              Everything You Need to{" "}
              <span className="gradient-text">Master Speech</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-xl mx-auto">
              Clinical-grade tools wrapped in a beautifully gamified experience
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feat, i) => (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="glass-hover p-6 rounded-2xl group"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110"
                  style={{
                    background: `${feat.color}15`,
                    border: `1px solid ${feat.color}30`,
                  }}
                >
                  <feat.icon className="w-6 h-6" style={{ color: feat.color }} />
                </div>
                <h3 className="text-white font-bold text-lg mb-2">{feat.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Stats bar ─────────────────────────────────────────────────── */}
        <section
          className="py-16 px-6"
          style={{
            background: "rgba(255,255,255,0.02)",
            borderTop: "1px solid rgba(255,255,255,0.05)",
            borderBottom: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: "38", label: "IPA Phonemes Tracked", unit: "" },
              { value: "98.7", label: "Whisper Accuracy", unit: "%" },
              { value: "50ms", label: "Inference Latency", unit: "" },
              { value: "4", label: "Articulation Leagues", unit: "" },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex flex-col items-center text-center"
              >
                <span className="text-4xl font-black gradient-text">{stat.value}{stat.unit}</span>
                <span className="text-sm text-slate-400 mt-1">{stat.label}</span>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Final CTA ─────────────────────────────────────────────────── */}
        <section className="py-24 px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-2xl mx-auto"
          >
            <h2 className="text-4xl font-black text-white mb-6">
              Start Your Speech Journey Today
            </h2>
            <Link href="/auth" id="cta-get-started-bottom">
              <button className="btn-primary text-lg flex items-center gap-3 mx-auto">
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </button>
            </Link>
          </motion.div>
        </section>

        {/* Footer */}
        <footer
          className="py-8 px-6 text-center text-sm text-slate-600"
          style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
        >
          NeuroSpeak AI © 2026 — Built for speech-language pathologists and patients worldwide
        </footer>
      </div>
    </main>
  );
}
