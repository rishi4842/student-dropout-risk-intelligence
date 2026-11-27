"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { fetchMetadata } from "@/lib/api";

interface StudentContextType {
  tag: "early" | "full";
  setTag: (tag: "early" | "full") => void;
  metadata: any;
  studentValues: Record<string, any>;
  setStudentValues: (vals: Record<string, any>) => void;
  targetLabel: string | null;
  setTargetLabel: (label: string | null) => void;
  selectedPersona: string;
  setSelectedPersona: (name: string) => void;
  selectStudentFromOverview: (vals: Record<string, any>, label: string) => void;
}

const StudentContext = createContext<StudentContextType | null>(null);

export function StudentProvider({ children }: { children: React.ReactNode }) {
  const [tag, setTag] = useState<"early" | "full">("early");
  const [metadata, setMetadata] = useState<any>(null);
  const [studentValues, setStudentValues] = useState<Record<string, any>>({});
  const [targetLabel, setTargetLabel] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string>("High-Risk Attrition");

  useEffect(() => {
    fetchMetadata()
      .then((meta) => {
        setMetadata(meta);
        const persona = meta.personas["High-Risk Attrition"];
        if (persona) {
          setStudentValues(persona.values);
          setTargetLabel(persona.target);
        }
      })
      .catch((err) => console.error("Failed to fetch metadata:", err));
  }, []);

  const selectStudentFromOverview = (vals: Record<string, any>, label: string) => {
    setStudentValues(vals);
    setTargetLabel(label);
    setSelectedPersona("Custom Input");
  };

  return (
    <StudentContext.Provider
      value={{
        tag,
        setTag,
        metadata,
        studentValues,
        setStudentValues,
        targetLabel,
        setTargetLabel,
        selectedPersona,
        setSelectedPersona,
        selectStudentFromOverview,
      }}
    >
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent() {
  const ctx = useContext(StudentContext);
  if (!ctx) {
    throw new Error("useStudent must be used inside StudentProvider");
  }
  return ctx;
}
