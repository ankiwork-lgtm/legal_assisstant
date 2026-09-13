"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { text: "LexAid", href: "/" },
  { text: "Simplify", href: "/simplify" },
  { text: "Compare", href: "/compare" },
  { text: "Chat", href: "/chat" },
  { text: "Lawyer Prep", href: "/prep" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-slate-900 text-white px-6 py-3 flex items-center gap-6">
      {links.map(({ text, href }) => (
        <Link
          key={href}
          href={href}
          className={
            pathname === href
              ? "font-semibold underline"
              : "hover:text-slate-300 transition-colors"
          }
        >
          {text}
        </Link>
      ))}
    </nav>
  );
}
