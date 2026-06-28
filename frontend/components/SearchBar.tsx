"use client";
import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  onFilterOpen: () => void;
}

export default function SearchBar({ onSearch, onFilterOpen }: SearchBarProps) {
  const [query, setQuery] = useState("");

  return (
    <div style={{
      position: "fixed", top: 12, left: 12, right: 12, zIndex: 20,
      display: "flex", gap: 8, alignItems: "center",
    }}>
      <div className="glass" style={{
        flex: 1, display: "flex", alignItems: "center",
        borderRadius: 12, padding: "10px 14px", gap: 8,
      }}>
        <span style={{ fontSize: 16 }}>🔍</span>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && onSearch(query)}
          placeholder="搜尋地區、捷運站、街道..."
          style={{
            flex: 1, background: "none", border: "none", outline: "none",
            color: "var(--text-primary)", fontSize: 14,
          }}
        />
      </div>
      <button
        onClick={onFilterOpen}
        className="glass gold-btn"
        style={{ borderRadius: 12, padding: "10px 16px", whiteSpace: "nowrap" }}
      >
        篩選
      </button>
    </div>
  );
}
