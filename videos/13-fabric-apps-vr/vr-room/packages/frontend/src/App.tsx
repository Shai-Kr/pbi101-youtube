import { toQueryResult } from '@microsoft/rayfin-connector-fabric-semanticmodel';

import { getRayfinClient } from './lib/rayfin-client';
import { auroraCube } from './queries/aurora-cube';
import { cubeFromTable, type Cube } from './vr/data';
import { VrRoom } from './VrRoom';

/** One DAX query against the Aurora Sales semantic model, as the signed-in user. Runs every time the app opens. */
async function loadAurora(): Promise<Cube> {
  const { query } = auroraCube();
  const client = await getRayfinClient();
  const result = toQueryResult(await client.connectors.aurora.executeQuery({ query }));
  if (result.status !== 'success') {
    throw new Error(`${result.error.category}: ${result.error.message}`);
  }
  if (!result.table.rows.length) throw new Error('The model answered with no rows.');
  return cubeFromTable(
    result.table.columns.map((c) => c.name),
    result.table.rows
  );
}

/** One question to the published Fabric data agent, through the app's server-side function. Can take minutes. */
async function askDataAgent(question: string): Promise<string> {
  const client = await getRayfinClient();
  const result = await client.functions.askFabricDataAgent.invoke({ question }, { timeoutMs: 250_000 });
  if (!result.ok) throw new Error(result.answer);
  return result.answer;
}

// The whole app is one VR room over the live model (see vr/app.ts).
function App() {
  return <VrRoom loadCube={loadAurora} source="Real numbers, straight from the Aurora Sales model in Fabric" ask={askDataAgent} />;
}

export default App;
