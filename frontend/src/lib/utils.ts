import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(val: number): string {
  return `${(val * 100).toFixed(1)}%`;
}

export function getTierColor(tier: string) {
  if (tier === "High") {
    return {
      text: "text-red-500 dark:text-red-400",
      bg: "bg-red-500/10",
      border: "border-red-500/20",
      badge: "bg-red-500/10 text-red-500 border-red-500/30",
      indicator: "bg-red-500",
      label: "HIGH RISK",
    };
  }
  if (tier === "Medium") {
    return {
      text: "text-amber-500 dark:text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      badge: "bg-amber-500/10 text-amber-500 border-amber-500/30",
      indicator: "bg-amber-500",
      label: "MEDIUM RISK",
    };
  }
  return {
    text: "text-emerald-500 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
    indicator: "bg-emerald-500",
    label: "LOW RISK",
  };
}
