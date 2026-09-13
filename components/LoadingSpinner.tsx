import type { LoadingSpinnerProps } from "@/types/index";

export default function LoadingSpinner({ label }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label ?? "Loading"}
      className="flex flex-col items-center gap-2"
    >
      <div className="animate-spin h-8 w-8 rounded-full border-4 border-slate-200 border-t-blue-600" />
      {label && (
        <span className="text-sm text-slate-600">{label}</span>
      )}
    </div>
  );
}
