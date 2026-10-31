import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Paytm Voice Teammate",
  description: "An interruptible voice teammate for Paytm merchants, in Hindi, Kannada and English.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        {process.env.NEXT_PUBLIC_DEPLOYMENT_PROFILE === "lite" && (
          <div style={{ backgroundColor: "#F0F0F0", borderBottom: "2px solid #00B9F1", color: "#002E6E", padding: "10px", textAlign: "center", fontWeight: "bold", zIndex: 1000, fontSize: "0.9rem" }}>
            <svg aria-hidden="true" focusable="false" height="16" style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} viewBox="0 0 24 24" width="16">
              <path d="M12 3 2.8 20h18.4L12 3Zm0 5.2v5.6m0 2.8v.1" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
            Lite Mode: This is a constrained build for free deployment. Full emotional intelligence and Whisper fallback are only available in the local/dev version. Responses may be slower than local.
          </div>
        )}
        {children}
      </body>
    </html>
  );
}
