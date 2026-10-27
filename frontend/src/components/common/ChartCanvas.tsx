import React, { useState } from "react";

export interface DataPoint {
  x: string;
  y: number;
  y2?: number;
  bandUpper?: number;
  bandLower?: number;
  label?: string;
}

interface ChartCanvasProps {
  data: DataPoint[];
  title?: string;
  yAxisLabel?: string;
  seriesName?: string;
  series2Name?: string;
  height?: number;
  color?: string;
  color2?: string;
  isBar?: boolean;
  showZeroLine?: boolean;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({
  data,
  title,
  yAxisLabel,
  seriesName = "Value",
  series2Name,
  height = 240,
  color = "#c5a059",
  color2 = "#3b82f6",
  isBar = false,
  showZeroLine = false,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center bg-gray-50 border border-dashed border-gray-200 rounded-lg text-sm text-gray-400"
        style={{ height }}
      >
        No time-series data available for display
      </div>
    );
  }

  // Calculate scales
  const allY = data.flatMap((d) => [
    d.y,
    ...(d.y2 !== undefined ? [d.y2] : []),
    ...(d.bandUpper !== undefined ? [d.bandUpper] : []),
    ...(d.bandLower !== undefined ? [d.bandLower] : []),
  ]);
  const minY = Math.min(...allY);
  const maxY = Math.max(...allY);
  const range = maxY - minY || 1;
  const paddingY = range * 0.1;
  const scaledMin = minY - paddingY;
  const scaledMax = maxY + paddingY;
  const scaledRange = scaledMax - scaledMin;

  const width = 800; // viewBox width
  const padLeft = 60;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 30;
  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const getX = (i: number) => padLeft + (i / Math.max(1, data.length - 1)) * chartW;
  const getY = (val: number) => padTop + chartH - ((val - scaledMin) / scaledRange) * chartH;

  // Path generator
  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i).toFixed(1)} ${getY(d.y).toFixed(1)}`)
    .join(" ");

  const line2Path = series2Name
    ? data
        .filter((d) => d.y2 !== undefined)
        .map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i).toFixed(1)} ${getY(d.y2!).toFixed(1)}`)
        .join(" ")
    : null;

  // Zero reference line if applicable
  const zeroY = showZeroLine && scaledMin <= 0 && scaledMax >= 0 ? getY(0) : null;

  return (
    <div className="w-full bg-white border border-gray-200 rounded-lg p-3">
      {title && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">{title}</span>
            {yAxisLabel && <span className="text-[10px] text-gray-400 font-mono">({yAxisLabel})</span>}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-gray-600">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              {seriesName}
            </span>
            {series2Name && (
              <span className="flex items-center gap-1.5 text-gray-600">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color2 }} />
                {series2Name}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padTop + chartH * pct;
            const val = scaledMax - pct * scaledRange;
            return (
              <g key={idx}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke="#f3f4f6"
                  strokeWidth="1"
                />
                <text
                  x={padLeft - 6}
                  y={y + 3}
                  textAnchor="end"
                  className="text-[10px] fill-gray-400 tabular-nums font-mono"
                >
                  {val.toFixed(val > 100 ? 0 : 2)}
                </text>
              </g>
            );
          })}

          {/* Zero baseline */}
          {zeroY !== null && (
            <line
              x1={padLeft}
              y1={zeroY}
              x2={width - padRight}
              y2={zeroY}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              strokeWidth="1.2"
            />
          )}

          {/* Bar Chart or Line Chart */}
          {isBar ? (
            data.map((d, i) => {
              const x = getX(i) - (chartW / data.length / 2) * 0.8;
              const barW = Math.max(2, (chartW / data.length) * 0.7);
              const baselineY = zeroY !== null ? zeroY : padTop + chartH;
              const targetY = getY(d.y);
              const barH = Math.abs(baselineY - targetY);
              const yTop = Math.min(baselineY, targetY);
              const barColor = d.y >= 0 ? color : "#ef4444";
              return (
                <rect
                  key={i}
                  x={x}
                  y={yTop}
                  width={barW}
                  height={barH}
                  fill={barColor}
                  opacity={hoverIndex === i ? 1 : 0.85}
                  onMouseEnter={() => setHoverIndex(i)}
                />
              );
            })
          ) : (
            <>
              {/* Primary Line */}
              <path d={linePath} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
              {/* Secondary Line */}
              {line2Path && (
                <path
                  d={line2Path}
                  fill="none"
                  stroke={color2}
                  strokeWidth="1.8"
                  strokeDasharray="4 2"
                  strokeLinecap="round"
                />
              )}
            </>
          )}

          {/* X Axis Dates */}
          {data.length > 0 &&
            [0, Math.floor(data.length / 2), data.length - 1].map((idx) => {
              const item = data[idx];
              if (!item) return null;
              return (
                <text
                  key={idx}
                  x={getX(idx)}
                  y={height - 8}
                  textAnchor="middle"
                  className="text-[10px] fill-gray-400 font-mono"
                >
                  {item.x}
                </text>
              );
            })}

          {/* Interactive Hover Vertical Crosshair */}
          {hoverIndex !== null && (
            <g>
              <line
                x1={getX(hoverIndex)}
                y1={padTop}
                x2={getX(hoverIndex)}
                y2={padTop + chartH}
                stroke="#6b7280"
                strokeDasharray="2 2"
                strokeWidth="1"
              />
              <circle
                cx={getX(hoverIndex)}
                cy={getY(data[hoverIndex].y)}
                r="4"
                fill={color}
                stroke="#ffffff"
                strokeWidth="2"
              />
              {data[hoverIndex].y2 !== undefined && (
                <circle
                  cx={getX(hoverIndex)}
                  cy={getY(data[hoverIndex].y2!)}
                  r="4"
                  fill={color2}
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              )}
            </g>
          )}

          {/* Transparent Hover Hit Areas */}
          {data.map((_, i) => (
            <rect
              key={i}
              x={getX(i) - chartW / data.length / 2}
              y={padTop}
              width={chartW / data.length}
              height={chartH}
              fill="transparent"
              className="cursor-crosshair"
              onMouseEnter={() => setHoverIndex(i)}
            />
          ))}
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoverIndex !== null && data[hoverIndex] && (
          <div
            className="absolute top-2 right-4 bg-gray-900/90 text-white px-2.5 py-1.5 rounded shadow text-xs font-mono pointer-events-none z-10"
          >
            <div className="text-gray-300 font-sans text-[11px] mb-0.5">{data[hoverIndex].x}</div>
            <div className="flex items-center gap-2">
              <span style={{ color }}>{seriesName}:</span>
              <span className="font-bold">{data[hoverIndex].y.toFixed(2)}</span>
            </div>
            {data[hoverIndex].y2 !== undefined && (
              <div className="flex items-center gap-2">
                <span style={{ color: color2 }}>{series2Name}:</span>
                <span className="font-bold">{data[hoverIndex].y2!.toFixed(2)}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
