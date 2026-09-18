import './globals.css';
export const metadata = { title: 'CivicProof — What the records establish', description: 'Explore the evidence behind five historical Nigerian road projects.' };
export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><a className="skip" href="#main">Skip to content</a><header><a className="brand" href="/">Civic<span>Proof</span><span className="brand-dot" aria-hidden="true">.</span></a><span className="edition">NIGERIA · RELEASE CANDIDATE</span></header>{children}<footer><strong>Evidence, with its limits intact.</strong><p>Five historical road dossiers. Public records are not independent proof of present-day conditions. Content-reviewed public hackathon proof of concept. Source-data rights are separate from the CivicProof code license.</p></footer></body></html>;
}
