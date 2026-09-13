import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Chat with Document — LexAid",
  description:
    "Upload a PDF or paste your legal document to ask questions and get plain-English answers.",
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
