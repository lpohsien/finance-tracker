import React from 'react';

interface DataItem {
  name: string;
  value: number;
  color: string;
}

interface SimplePieChartProps {
  data: DataItem[];
}

export const SimplePieChart: React.FC<SimplePieChartProps> = ({ data }) => {
  const total = data.reduce((a, b) => a + b.value, 0);
  let accumulatedAngle = 0;

  if (total === 0) {
      return (
          <svg viewBox="0 0 32 32" className="w-full h-full -rotate-90">
              <circle cx="16" cy="16" r="16" fill="#e5e7eb" />
              <circle cx="16" cy="16" r="10" fill="white" />
          </svg>
      )
  }

  return (
    <svg viewBox="0 0 32 32" className="w-full h-full -rotate-90">
      {data.map((slice, i) => {
        const angle = (slice.value / total) * 360;
        // If angle is 360 (can happen if only 1 item), we need to draw a full circle
        if (angle === 360) {
            return (
                 <circle key={i} cx="16" cy="16" r="16" fill={slice.color} />
            );
        }

        const x1 = Math.cos((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        const y1 = Math.sin((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        
        const nextAngle = accumulatedAngle + angle;
        const x2 = Math.cos((nextAngle * Math.PI) / 180) * 16 + 16;
        const y2 = Math.sin((nextAngle * Math.PI) / 180) * 16 + 16;
        
        const largeArcFlag = angle > 180 ? 1 : 0;
        
        const pathData = `M 16 16 L ${x1} ${y1} A 16 16 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
        
        accumulatedAngle += angle;

        return (
          <path
            key={i}
            d={pathData}
            fill={slice.color}
          />
        );
      })}
      <circle cx="16" cy="16" r="10" fill="white" />
    </svg>
  );
};
