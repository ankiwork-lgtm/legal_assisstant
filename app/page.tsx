import Link from "next/link";

const features = [
  {
    id: "FEAT-01",
    name: "Document Simplifier",
    emoji: "📄",
    description:
      "Upload or paste a legal document and get a plain-English summary with key clauses and risk flags.",
    href: "/simplify",
  },
  {
    id: "FEAT-02",
    name: "Contract Comparator",
    emoji: "⚖️",
    description:
      "Compare two contracts side-by-side to surface differences, matching terms, and potential risks.",
    href: "/compare",
  },
  {
    id: "FEAT-03",
    name: "Q&A Chat",
    emoji: "💬",
    description:
      "Ask plain-English questions about any legal document and get answers grounded in its text.",
    href: "/chat",
  },
  {
    id: "FEAT-04",
    name: "Lawyer Prep",
    emoji: "🏛️",
    description:
      "Generate a tailored list of questions, documents to gather, and watch-out points before your lawyer meeting.",
    href: "/prep",
  },
];

export default function HomePage() {
  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-slate-900 mb-3">LexAid</h1>
        <p className="text-lg text-slate-600 font-medium mb-4">
          Understand your legal documents — no law degree required.
        </p>
        <p className="text-slate-500 max-w-xl mx-auto">
          LexAid uses AI to simplify complex legal language, compare contracts,
          answer your questions, and help you prepare for meetings with your
          lawyer.
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {features.map(({ id, name, emoji, description, href }) => (
          <Link
            key={id}
            href={href}
            className="group block rounded-xl border border-slate-200 bg-white p-6 hover:border-blue-400 hover:shadow-md transition-all"
          >
            <div className="text-3xl mb-3">{emoji}</div>
            <h2 className="text-lg font-semibold text-slate-800 group-hover:text-blue-700 mb-1">
              {name}
            </h2>
            <p className="text-sm text-slate-500">{description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
