"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Flame, Zap, Target, TrendingUp, Mic, Trophy } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIER_CONFIG: Record<string, { emoji: string; color: string; next: string; xpNeeded: number }> = {
  bronze: { emoji: "🥉", color: "#cd7f32", next: "Silver", xpNeeded: 500 },
  silver: { emoji: "🥈", color: "#c0c0c0", next: "Gold", xpNeeded: 2000 },
  gold: { emoji: "🥇", color: "#ffd700", next: "Master", xpNeeded: 5000 },
  master: { emoji: "💎", color: "#7c3aed", next: "MAX", xpNeeded: 5000 },
};

// Mock streak calendar data when API unavailable
function mockCalendar() {
  const today = new Date();
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (29 - i));
    return {
      date: d.toISOString().split("T")[0],
      practiced: Math.random() > 0.4,
    };
  });
}

function mockRecentSessions() {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - i);
    return {
      date: d.toISOString().split("T")[0],
      overall: Math.round(65 + Math.random() * 30),
      difficulty: ["easy", "moderate", "hard"][Math.floor(Math.random() * 3)],
    };
  }).reverse();
}

export default function PatientDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userRaw = localStorage.getItem("ns_user");
    const user = userRaw ? JSON.parse(userRaw) : { id: 1, name: "Demo Patient" };

    fetch(`${API_BASE}/api/v2/patient/${user.id}/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {
        // Offline / demo mode
        setData({
          user: { name: user.name || "Demo Patient" },
          gamification: {
            total_xp: 1240,
            tier: "silver",
            streak_days: 7,
            longest_streak: 12,
            total_sessions: 34,
            avg_accuracy: 78.4,
            daily_quest_progress: 60,
            daily_quest_completed: false,
          },
          streak_calendar: mockCalendar(),
          phoneme_weaknesses: [
            { phoneme: "θ", avg_score: 42 },
            { phoneme: "ʒ", avg_score: 51 },
            { phoneme: "ŋ", avg_score: 58 },
            { phoneme: "ð", avg_score: 63 },
            { phoneme: "ʃ", avg_score: 69 },
          ],
          recent_sessions: mockRecentSessions().map((s, i) => ({
            session_uuid: `demo-${i}`,
            target_text: ["cat", "butterfly", "strength", "beautiful"][i % 4],
            difficulty: s.difficulty,
            overall_score: s.overall,
            xp_earned: Math.round(s.overall / 5),
            timestamp: new Date(s.date).toISOString(),
          })),
          prescriptions: [],
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center pt-20">
        <div className="w-10 h-10 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </main>
    );
  }

  const gam = data?.gamification ?? {};
  const tierCfg = TIER_CONFIG[gam.tier ?? "bronze"];
  const xpProgress = gam.tier === "master"
    ? 100
    : Math.min((gam.total_xp / tierCfg.xpNeeded) * 100, 100);

  const chartData = (data?.recent_sessions ?? []).slice(-10).map((s: any) => ({
    date: s.timestamp?.split("T")[0]?.slice(5),
    score: Math.round(s.overall_score ?? 0),
  }));

  return (
    <main className="min-h-screen pt-20 pb-12 px-6">
      <div className="max-w-6xl mx-auto">

        {/* ── Header ──────────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-3xl font-black text-white">
              Welcome back, {data?.user?.name?.split(" ")[0] ?? "Warrior"} 👋
            </h1>
            <p className="text-slate-400 mt-1">Keep pushing — every practice session counts.</p>
          </div>
          <button
            onClick={() => router.push("/practice/session")}
            className="btn-primary flex items-center gap-2"
            id="btn-start-practice"
          >
            <Mic className="w-4 h-4" />
            Practice Now
          </button>
        </motion.div>

        {/* ── Stats Row ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { icon: Flame, label: "Day Streak", value: `${gam.streak_days ?? 0}`, color: "#f59e0b", unit: "days" },
            { icon: Zap, label: "Total XP", value: `${gam.total_xp ?? 0}`, color: "#6366f1", unit: "xp" },
            { icon: Target, label: "Sessions", value: `${gam.total_sessions ?? 0}`, color: "#10b981", unit: "total" },
            { icon: TrendingUp, label: "Avg Accuracy", value: gam.avg_accuracy ? `${gam.avg_accuracy.toFixed(1)}%` : "—", color: "#06b6d4", unit: "score" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className="glass p-5 rounded-2xl flex items-start gap-4"
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: `${stat.color}15`, border: `1px solid ${stat.color}25` }}
              >
                <stat.icon className="w-5 h-5" style={{ color: stat.color }} />
              </div>
              <div>
                <div className="text-2xl font-black text-white">{stat.value}</div>
                <div className="text-xs text-slate-500">{stat.label}</div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

          {/* ── Tier Card ────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass p-6 rounded-2xl flex flex-col gap-4"
            style={{ border: `1px solid ${tierCfg.color}25`, boxShadow: `0 0 30px ${tierCfg.color}08` }}
          >
            <div className="flex items-center gap-3">
              <Trophy className="w-5 h-5 text-slate-400" />
              <h2 className="font-bold text-white">Current Tier</h2>
            </div>
            <div className="flex flex-col items-center py-4">
              <div className="text-6xl mb-3 float-anim">{tierCfg.emoji}</div>
              <div className="text-2xl font-black capitalize" style={{ color: tierCfg.color }}>
                {gam.tier ?? "bronze"}
              </div>
              <div className="text-sm text-slate-500 mt-1">{gam.total_xp ?? 0} XP total</div>
            </div>
            {gam.tier !== "master" && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Progress to {tierCfg.next}</span>
                  <span style={{ color: tierCfg.color }}>{Math.round(xpProgress)}%</span>
                </div>
                <div className="score-bar-track">
                  <motion.div
                    className="score-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${xpProgress}%` }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                    style={{ background: `linear-gradient(90deg, ${tierCfg.color}88, ${tierCfg.color})` }}
                  />
                </div>
              </div>
            )}
          </motion.div>

          {/* ── Daily Quest ──────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="glass p-6 rounded-2xl flex flex-col gap-4"
          >
            <h2 className="font-bold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-400" />
              Daily Quest
            </h2>
            <div
              className="relative flex flex-col items-center justify-center rounded-2xl py-8"
              style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.15)" }}
            >
              <div
                className="w-24 h-24 rounded-full flex items-center justify-center mb-3"
                style={{
                  background: `conic-gradient(#6366f1 ${gam.daily_quest_progress ?? 0}%, rgba(255,255,255,0.04) 0%)`,
                  boxShadow: "0 0 30px rgba(99,102,241,0.2)",
                }}
              >
                <div
                  className="w-[72px] h-[72px] rounded-full flex items-center justify-center"
                  style={{ background: "var(--ns-bg-2)" }}
                >
                  <span className="text-xl font-black text-indigo-300">
                    {Math.round(gam.daily_quest_progress ?? 0)}%
                  </span>
                </div>
              </div>
              <div className="text-white font-semibold">15-Minute Practice</div>
              <div className="text-xs text-slate-500 mt-1">
                {gam.daily_quest_completed ? "✅ Completed today!" : "Keep going to earn +50 XP bonus!"}
              </div>
            </div>
            <button
              onClick={() => router.push("/practice/session")}
              className="btn-primary w-full flex items-center justify-center gap-2"
              id="btn-quest-practice"
            >
              <Mic className="w-4 h-4" />
              {gam.daily_quest_completed ? "Practice More" : "Continue Quest"}
            </button>
          </motion.div>

          {/* ── Phoneme Weaknesses ───────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="glass p-6 rounded-2xl flex flex-col gap-4"
          >
            <h2 className="font-bold text-white">Trouble Phonemes</h2>
            <div className="flex flex-col gap-3">
              {(data?.phoneme_weaknesses ?? []).slice(0, 5).map((pw: any, i: number) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="phoneme-pill w-10 justify-center shrink-0">{pw.phoneme}</div>
                  <div className="flex-1">
                    <div className="score-bar-track">
                      <div
                        className="score-bar-fill"
                        style={{
                          width: `${pw.avg_score}%`,
                          background: `linear-gradient(90deg, #f43f5e88, #f43f5e)`,
                          transition: "width 1s ease",
                        }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-bold text-rose-400 w-10 text-right">
                    {pw.avg_score}%
                  </span>
                </div>
              ))}
              {(data?.phoneme_weaknesses ?? []).length === 0 && (
                <p className="text-slate-500 text-sm text-center py-4">
                  Complete more sessions to see phoneme analysis.
                </p>
              )}
            </div>
          </motion.div>
        </div>

        {/* ── Streak Calendar ──────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="glass p-6 rounded-2xl mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Flame className="w-5 h-5 text-amber-400" />
            <h2 className="font-bold text-white">Practice Streak</h2>
            <span className="ml-auto text-sm text-slate-500">Last 30 days</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(data?.streak_calendar ?? []).map((day: any, i: number) => (
              <div
                key={i}
                title={day.date}
                className="w-7 h-7 rounded-md transition-all duration-200"
                style={{
                  background: day.practiced
                    ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
                    : "rgba(255,255,255,0.04)",
                  border: day.practiced
                    ? "1px solid rgba(99,102,241,0.4)"
                    : "1px solid rgba(255,255,255,0.04)",
                  boxShadow: day.practiced ? "0 0 8px rgba(99,102,241,0.3)" : "none",
                }}
              />
            ))}
          </div>
          <div className="flex items-center gap-3 mt-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ background: "rgba(255,255,255,0.06)" }} />
              <span className="text-xs text-slate-500">No practice</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }} />
              <span className="text-xs text-slate-500">Practiced</span>
            </div>
          </div>
        </motion.div>

        {/* ── Accuracy Chart ───────────────────────────────────────────── */}
        {chartData.length > 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass p-6 rounded-2xl"
          >
            <h2 className="font-bold text-white mb-4">Accuracy Trend</h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "rgba(5,8,16,0.9)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    color: "white",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#6366f1"
                  strokeWidth={2.5}
                  dot={{ fill: "#6366f1", strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, fill: "#818cf8" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </div>
    </main>
  );
}
