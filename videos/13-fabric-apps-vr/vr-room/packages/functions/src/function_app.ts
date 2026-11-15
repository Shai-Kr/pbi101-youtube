// Server-side functions of the VR room.
//
// askFabricDataAgent: passes one question to the published Fabric data agent over its MCP endpoint and
// returns the agent's text. The Fabric token never leaves this function; nothing is logged.

import { AudienceType, UserDataFunctions, type RayfinContext } from '@microsoft/fabric-user-data-functions';

import { DATA_AGENT_MCP_ENDPOINT } from './agent_endpoint';

const udf = new UserDataFunctions();

/** No app-owned data model is used here. */
type AppSchema = Record<string, never>;

export interface DataAgentResult {
  ok: boolean;
  /** The agent's answer, or a short reason when `ok` is false. */
  answer: string;
}

type JsonRpcResponse = {
  id?: number;
  result?: unknown;
  error?: { code?: number; message?: string };
};

type McpResponse = {
  responseStatus: number;
  sessionId: string | null;
  body: JsonRpcResponse | null;
};

function parseJsonRpcResponse(text: string): JsonRpcResponse | null {
  const trimmed = text.trim();
  if (!trimmed) return null;
  const dataLines = trimmed
    .split(/\r?\n/)
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice('data:'.length).trim());
  const payload = dataLines.at(-1) ?? trimmed;
  try {
    const parsed: unknown = JSON.parse(payload);
    return parsed && typeof parsed === 'object' ? (parsed as JsonRpcResponse) : null;
  } catch {
    return null;
  }
}

async function postMcpRequest(
  endpoint: string,
  token: string,
  payload: Record<string, unknown>,
  signal: AbortSignal,
  sessionId?: string
): Promise<McpResponse> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      Accept: 'application/json, text/event-stream',
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'MCP-Protocol-Version': '2025-03-26',
      ...(sessionId ? { 'Mcp-Session-Id': sessionId } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });
  const responseSessionId = response.headers.get('mcp-session-id');
  if (!response.ok) {
    return { responseStatus: response.status, sessionId: responseSessionId, body: null };
  }
  const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
  const isJsonRpc = contentType.includes('application/json') || contentType.includes('text/event-stream');
  const text = await response.text();
  return { responseStatus: response.status, sessionId: responseSessionId, body: isJsonRpc ? parseJsonRpcResponse(text) : null };
}

const MAX_QUESTION = 300;
const MAX_ANSWER = 1800;

udf.func(
  'askFabricDataAgent',
  async (ctx: RayfinContext<AppSchema, AudienceType.Fabric>, question: string): Promise<DataAgentResult> => {
    const q = (question ?? '').trim().slice(0, MAX_QUESTION);
    if (q.length < 3) return { ok: false, answer: 'The question is too short.' };
    if (!DATA_AGENT_MCP_ENDPOINT) {
      return { ok: false, answer: 'No Fabric data agent is connected to this app yet (see agent_endpoint.ts).' };
    }
    const token: string = ctx.Tokens.Fabric;
    // the platform stops a function at 250 seconds; stop the outbound call a little earlier
    const signal = AbortSignal.timeout(235_000);
    try {
      const init = await postMcpRequest(
        DATA_AGENT_MCP_ENDPOINT,
        token,
        {
          jsonrpc: '2.0',
          id: 1,
          method: 'initialize',
          params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'aurora-vr-room', version: '1.0.0' } },
        },
        signal
      );
      if (init.responseStatus === 401 || init.responseStatus === 403) {
        return { ok: false, answer: 'The data agent refused the app (no permission on the agent or its data).' };
      }
      if (init.responseStatus >= 400) return { ok: false, answer: `The data agent did not start (status ${init.responseStatus}).` };
      const session = init.sessionId ?? undefined;
      await postMcpRequest(DATA_AGENT_MCP_ENDPOINT, token, { jsonrpc: '2.0', method: 'notifications/initialized' }, signal, session);

      const list = await postMcpRequest(DATA_AGENT_MCP_ENDPOINT, token, { jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }, signal, session);
      const tools = (list.body?.result as { tools?: { name?: string; inputSchema?: { properties?: Record<string, unknown>; required?: string[] } }[] } | undefined)?.tools;
      const tool = tools?.[0];
      if (!tool?.name) return { ok: false, answer: 'The data agent offered no tool to ask.' };
      const props = Object.keys(tool.inputSchema?.properties ?? {});
      const arg = tool.inputSchema?.required?.[0] ?? props.find((p) => /question|query|prompt|input|message/i.test(p)) ?? props[0] ?? 'question';

      const call = await postMcpRequest(
        DATA_AGENT_MCP_ENDPOINT,
        token,
        { jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: tool.name, arguments: { [arg]: q } } },
        signal,
        session
      );
      if (call.responseStatus >= 400) return { ok: false, answer: `The data agent failed to answer (status ${call.responseStatus}).` };
      if (call.body?.error) return { ok: false, answer: 'The data agent reported an error for this question.' };
      const content = (call.body?.result as { content?: { type?: string; text?: string }[]; isError?: boolean } | undefined)?.content ?? [];
      const text = content
        .filter((c) => c.type === 'text' && typeof c.text === 'string')
        .map((c) => c.text as string)
        .join('\n')
        .trim();
      if (!text) return { ok: false, answer: 'The data agent returned no text.' };
      return { ok: true, answer: text.slice(0, MAX_ANSWER) };
    } catch (err) {
      const name = err instanceof Error ? err.name : '';
      return { ok: false, answer: name === 'TimeoutError' || name === 'AbortError' ? 'The data agent took too long (more than four minutes).' : 'The data agent could not be reached.' };
    }
  },
  [] // the audience in the annotation is the declaration
);
