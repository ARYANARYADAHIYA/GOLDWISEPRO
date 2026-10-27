import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon,
  badge,
  className = "",
}) => {
  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-4 shadow-xs hover:border-gray-300 transition-colors ${className}`}
    >
      <div className="flex items-center justify-between text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">
        <span className="truncate">{label}</span>
        {icon && <span className="text-gray-400">{icon}</span>}
      </div>
      <div className="flex items-baseline justify-between mt-1">
        <div className="text-2xl font-bold text-gray-900 tabular-nums">{value}</div>
        {badge && <div>{badge}</div>}
      </div>
      {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
    </div>
  );
};
