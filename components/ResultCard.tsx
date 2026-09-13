import type { ResultCardProps } from "@/types/index";

const variantClasses: Record<
  NonNullable<ResultCardProps["variant"]>,
  string
> = {
  default: "bg-white border-slate-200",
  warning: "bg-amber-50 border-amber-300",
  info: "bg-blue-50 border-blue-300",
};

export default function ResultCard({
  title,
  content,
  variant = "default",
}: ResultCardProps) {
  return (
    <div className={`rounded-lg border p-4 ${variantClasses[variant]}`}>
      <h2 className="text-base font-semibold text-slate-800 mb-2">{title}</h2>
      <p className="whitespace-pre-wrap text-sm text-slate-700">{content}</p>
    </div>
  );
}
