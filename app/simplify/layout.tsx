import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Simplify Document — LexAid",
  description:
    "Upload a PDF or paste your legal document to get a plain-English summary and clause breakdown.",
};

export default function SimplifyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
