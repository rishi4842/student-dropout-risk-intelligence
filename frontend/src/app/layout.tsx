import type { Metadata } from "next";
import "./globals.css";
import { StudentProvider } from "@/context/StudentContext";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "RetainAI • Student Retention & Early-Warning Intelligence",
  description:
    "Interpretable early-warning machine learning system for higher education student retention",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans bg-background text-foreground antialiased">
        <StudentProvider>
          <AppShell>{children}</AppShell>
        </StudentProvider>
      </body>
    </html>
  );
}
