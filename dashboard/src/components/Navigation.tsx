'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Mic2, MonitorPlay, Gamepad2, ActivitySquare } from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
  { name: 'Command Hub', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Dysarthric Suite', path: '/translate', icon: Mic2 },
  { name: 'Lip Trainer', path: '/lip-trainer', icon: MonitorPlay },
  { name: 'Articulation Quests', path: '/quests', icon: Gamepad2 },
  { name: 'Clinical Portal', path: '/clinical-portal', icon: ActivitySquare },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed left-0 top-0 h-full w-20 md:w-64 bg-black/40 backdrop-blur-md border-r border-white/10 z-[100] flex flex-col transition-all duration-300">
      <div className="p-6 pb-12">
        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-[var(--color-neural-indigo)] to-[var(--color-synaptic-cyan)] shadow-[0_0_15px_rgba(79,70,229,0.5)] mx-auto md:mx-0 flex items-center justify-center font-bold text-white tracking-widest text-xs">
          NS
        </div>
      </div>
      
      <div className="flex-1 px-4 flex flex-col gap-4">
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link key={item.path} href={item.path} className="relative group block">
              <div className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive ? 'text-white' : 'text-gray-400 hover:text-white'
              }`}>
                <item.icon className={`w-5 h-5 ${isActive ? 'text-[var(--color-synaptic-cyan)]' : 'group-hover:text-[var(--color-neural-indigo)]'}`} />
                <span className="hidden md:block font-medium tracking-wide text-sm">{item.name}</span>
              </div>
              
              {isActive && (
                <motion.div 
                  layoutId="activeTab"
                  className="absolute inset-0 bg-white/5 border border-white/10 rounded-xl -z-10"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </Link>
          );
        })}
      </div>
      
      <div className="p-6 mt-auto">
        <div className="hidden md:flex flex-col gap-1">
          <span className="text-[10px] uppercase text-gray-500 tracking-widest font-semibold">System Status</span>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            ALL SYSTEMS NOMINAL
          </div>
        </div>
      </div>
    </nav>
  );
}
