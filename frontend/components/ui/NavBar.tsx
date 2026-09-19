"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, LayoutDashboard, Mic, LogOut } from "lucide-react";
import { motion } from "framer-motion";

const NAV_ITEMS = [
  { href: "/practice/session", label: "Practice", icon: Mic },
  { href: "/dashboard/patient", label: "Dashboard", icon: LayoutDashboard },
];

export default function NavBar() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  if (isLanding) return null;

  return (
    <motion.nav
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: "rgba(5, 8, 16, 0.7)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
          >
            <Brain className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white tracking-tight">NeuroSpeak</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  active
                    ? "text-white"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
                style={active ? { background: "rgba(99,102,241,0.2)", color: "#a5b4fc" } : {}}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            );
          })}
        </div>

        {/* Logout / auth */}
        <Link
          href="/auth"
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-all duration-200 hover:bg-white/5"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </Link>
      </div>
    </motion.nav>
  );
}
