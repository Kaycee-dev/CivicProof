import { Dossier } from '../../../components/Product';
import manifest from '../../../lib/build-manifest.json';
export function generateStaticParams() { return Object.keys(manifest.artifacts).map(id => ({ id })); }
export default async function Project({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <Dossier id={id}/>; }
