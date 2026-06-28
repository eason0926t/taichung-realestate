// frontend/app/layout.tsx
import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "台中房市通",
  description: "台中市房地產資訊 — 實價登錄 + 多家房仲物件",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body style={{ margin: 0, overflow: "hidden" }}>{children}</body>
    </html>
  );
}
