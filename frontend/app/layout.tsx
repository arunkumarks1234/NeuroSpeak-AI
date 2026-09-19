import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "NeuroSpeak AI — Gamified Speech Therapy",
  description:
    "AI-powered speech therapy and pronunciation assessment platform with 3D gamification, real-time phoneme analysis, and clinical monitoring for speech-language pathologists.",
  keywords: [
    "speech therapy", "pronunciation assessment", "dysarthria rehabilitation",
    "phoneme analysis", "speech pathology", "AI speech", "gamified therapy",
  ],
  openGraph: {
    title: "NeuroSpeak AI",
    description: "Next-generation AI speech therapy platform",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#050810" />
      </head>
      <body className="animated-bg min-h-screen antialiased">{children}</body>
    </html>
  );
}
