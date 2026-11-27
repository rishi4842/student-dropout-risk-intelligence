import type { Metadata } from "next";
import "./globals.css";
import { StudentProvider } from "@/context/StudentContext";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Retention Intelligence • Student Success Analytics",
  description:
    "AI-powered university student retention and early-warning decision-support platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans bg-background text-foreground antialiased">
        <StudentProvider>
          <AppShell>{children}</AppShell>
        </StudentProvider>
      </body>
    </html>
  );
}
