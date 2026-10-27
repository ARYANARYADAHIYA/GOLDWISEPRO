import React from "react";

interface BadgeProps {
  variant?: "investigate" | "suppressed" | "insufficient" | "synthetic" | "real" | "neutral" | "gold";
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = "neutral", children, className = "" }) => {
  const styles = {
    investigate: "bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold",
    suppressed: "bg-rose-50 text-rose-800 border-rose-200 font-medium",
    insufficient: "bg-amber-50 text-amber-800 border-amber-300 font-medium",
    synthetic: "bg-amber-50 text-amber-900 border-amber-300 font-semibold tracking-wide",
    real: "bg-emerald-100 text-emerald-900 border-emerald-400 font-semibold tracking-wide",
    neutral: "bg-gray-100 text-gray-700 border-gray-200",
    gold: "bg-[#fbf7ed] text-[#8c6d23] border-[#e7d8b5] font-medium"
  }[variant];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs border uppercase tracking-wider ${styles} ${className}`}
    >
      {children}
    </span>
  );
};
