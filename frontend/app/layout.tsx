import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Profit Sharing App - Stellar Testnet',
  description: 'A profit-sharing web application using Stellar blockchain for commission deposits',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="testnet-banner">
          🧪 STELLAR TESTNET MODE - No real funds at risk
        </div>
        {children}
      </body>
    </html>
  );
}
