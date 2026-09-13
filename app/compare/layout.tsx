import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compare Contracts — LexAid",
  description:
    "Upload or paste two legal documents to compare their terms, differences, and risks side by side.",
};

export default function CompareLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
