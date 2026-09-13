import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Lawyer Prep Checklist — LexAid",
  description:
    "Generate a preparation checklist for your lawyer meeting based on your legal document.",
};

export default function PrepLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
