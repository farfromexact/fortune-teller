import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://guanbian.openai.site"),
  title: "观变｜以易观时，以行验知",
  description: "借《周易》的变化视角，整理处境、风险与下一步行动。不是命运预言，而是一份东方决策与复盘工具。",
  icons: { icon: "/favicon.svg" },
  openGraph: {
    title: "观变｜以易观时，以行验知",
    description: "在不确定中，看见变化的方向。",
    images: ["/og.png"],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "观变｜以易观时，以行验知",
    description: "在不确定中，看见变化的方向。",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
