import { NextResponse } from 'next/server';

const PHONEMES = ['æ', 'b', 'd', 'eɪ', 'f', 'g', 'i:', 'k', 'l', 'm', 'n', 'oʊ', 'p', 'r', 's', 't', 'v', 'w', 'z', 'θ'];

export async function POST() {
  // Simulate decoding speech parameters
  return NextResponse.json({
    accuracy: Math.random() * 4 + 95, // 95-99%
    snr: Math.floor(Math.random() * 15) + 30, // 30-45 dB
    activePhoneme: PHONEMES[Math.floor(Math.random() * PHONEMES.length)]
  });
}

export async function GET() {
  return POST();
}
