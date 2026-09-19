import { NextResponse } from 'next/server';

export async function GET() {
  const frames = Array.from({ length: 192 }, (_, i) => {
    const padNum = String(i + 1).padStart(3, '0');
    return `/assets/neurospeak/ezgif-frame-${padNum}.jpg`;
  });

  return NextResponse.json({
    totalFrames: 192,
    basePath: '/assets/neurospeak/',
    frames
  });
}
