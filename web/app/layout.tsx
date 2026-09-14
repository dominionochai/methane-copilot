import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Methane Copilot | Detect. Bill. Heal.",
  description: "A local sample-data story from methane detection to verified repair.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
