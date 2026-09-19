import { NextResponse } from 'next/server';

export async function GET() {
  // Simulate dynamic telemetry data
  return NextResponse.json({
    latency: Math.floor(Math.random() * 20) + 15, // 15-35ms
    bandwidth: (Math.random() * 2 + 8).toFixed(2) + ' GB/s',
    modelStatus: Math.random() > 0.05 ? 'ONLINE & READY' : 'RECALIBRATING',
    confidence: Math.random() * 5 + 94 // 94-99%
  });
}
