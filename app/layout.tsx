import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import DisclaimerBanner from "@/components/DisclaimerBanner";

export const metadata: Metadata = {
  title: "LexAid",
  description: "AI-powered legal document assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <DisclaimerBanner />
        {children}
      </body>
    </html>
  );
}
