import * as vscode from "vscode";

interface StreamEvent {
  type: string;
  timestamp: string;
  session_id: string;
  payload: Record<string, unknown>;
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("enterpriseAgent.open", async () => {
      const panel = vscode.window.createWebviewPanel(
        "enterpriseAgent",
        "AI Coding Agent",
        vscode.ViewColumn.Beside,
        { enableScripts: true }
      );

      panel.webview.html = getWebviewHtml();

      let currentSessionId: string | null = null;

      panel.webview.onDidReceiveMessage(async (message) => {
        try {
          if (message.type === "run") {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
              throw new Error("Open a workspace folder before running the agent.");
            }

            const config = vscode.workspace.getConfiguration();
            const apiBaseUrl = config.get<string>("enterpriseAgent.apiBaseUrl") || "http://localhost:8080";
            const apiKey = config.get<string>("enterpriseAgent.apiKey") || "dev-local-key";

            const sessionResponse = await fetch(`${apiBaseUrl}/v1/sessions`, {
              method: "POST",
              headers: {
                "content-type": "application/json",
                "x-api-key": apiKey,
              },
              body: JSON.stringify({ workspace_path: workspaceFolder.uri.fsPath }),
            });
            if (!sessionResponse.ok) {
              throw new Error(await sessionResponse.text());
            }
            const sessionPayload = (await sessionResponse.json()) as { session_id: string };
            currentSessionId = sessionPayload.session_id;
            panel.webview.postMessage({ type: "status", text: `Session created: ${currentSessionId}` });

            const runResponse = await fetch(`${apiBaseUrl}/v1/sessions/${currentSessionId}/messages`, {
              method: "POST",
              headers: {
                "content-type": "application/json",
                "x-api-key": apiKey,
              },
              body: JSON.stringify({ message: String(message.task || "") }),
            });
            if (!runResponse.ok) {
              throw new Error(await runResponse.text());
            }

            void streamEvents(apiBaseUrl, apiKey, currentSessionId, panel);
          }

          if (message.type === "cancel" && currentSessionId) {
            const config = vscode.workspace.getConfiguration();
            const apiBaseUrl = config.get<string>("enterpriseAgent.apiBaseUrl") || "http://localhost:8080";
            const apiKey = config.get<string>("enterpriseAgent.apiKey") || "dev-local-key";
            await fetch(`${apiBaseUrl}/v1/sessions/${currentSessionId}/cancel`, {
              method: "POST",
              headers: { "x-api-key": apiKey },
            });
            panel.webview.postMessage({ type: "status", text: "Cancellation requested." });
          }

          if (message.type === "apply" && currentSessionId) {
            const config = vscode.workspace.getConfiguration();
            const apiBaseUrl = config.get<string>("enterpriseAgent.apiBaseUrl") || "http://localhost:8080";
            const apiKey = config.get<string>("enterpriseAgent.apiKey") || "dev-local-key";
            const response = await fetch(`${apiBaseUrl}/v1/sessions/${currentSessionId}/apply`, {
              method: "POST",
              headers: { "x-api-key": apiKey },
            });
            panel.webview.postMessage({ type: "status", text: `Apply: ${response.status}` });
            await vscode.commands.executeCommand("workbench.files.action.refreshFilesExplorer");
          }

          if (message.type === "review" && currentSessionId) {
            const config = vscode.workspace.getConfiguration();
            const apiBaseUrl = config.get<string>("enterpriseAgent.apiBaseUrl") || "http://localhost:8080";
            const apiKey = config.get<string>("enterpriseAgent.apiKey") || "dev-local-key";
            const response = await fetch(`${apiBaseUrl}/v1/sessions/${currentSessionId}/result`, {
              method: "GET",
              headers: { "x-api-key": apiKey },
            });
            if (!response.ok) {
              panel.webview.postMessage({ type: "status", text: `Review unavailable: ${response.status}` });
            } else {
              const data = await response.json();
              panel.webview.postMessage({ type: "reviewData", data });
            }
          }

          if (message.type === "reject" && currentSessionId) {
            const config = vscode.workspace.getConfiguration();
            const apiBaseUrl = config.get<string>("enterpriseAgent.apiBaseUrl") || "http://localhost:8080";
            const apiKey = config.get<string>("enterpriseAgent.apiKey") || "dev-local-key";
            const response = await fetch(`${apiBaseUrl}/v1/sessions/${currentSessionId}/reject`, {
              method: "POST",
              headers: { "x-api-key": apiKey },
            });
            panel.webview.postMessage({ type: "status", text: `Reject: ${response.status}` });
          }
        } catch (error) {
          panel.webview.postMessage({ type: "status", text: `Error: ${String(error)}` });
        }
      });
    })
  );
}

async function streamEvents(
  apiBaseUrl: string,
  apiKey: string,
  sessionId: string,
  panel: vscode.WebviewPanel
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/v1/sessions/${sessionId}/stream`, {
    method: "GET",
    headers: { "x-api-key": apiKey },
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed: ${response.status}`);
  }

  const decoder = new TextDecoder();
  const reader = response.body.getReader();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      if (!frame.startsWith("data:")) {
        continue;
      }
      const payload = frame.slice(5).trim();
      if (!payload) {
        continue;
      }
      const event = JSON.parse(payload) as StreamEvent;
      panel.webview.postMessage({ type: "event", event });
    }
  }
}

function getWebviewHtml(): string {
  return `<!doctype html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 12px; }
    textarea { width: 100%; min-height: 80px; margin-bottom: 8px; }
    button { margin-right: 8px; margin-bottom: 8px; }
    pre { background: #111; color: #ddd; padding: 8px; max-height: 280px; overflow: auto; }
    .log { white-space: pre-wrap; font-size: 12px; border: 1px solid #444; padding: 8px; min-height: 120px; }
  </style>
</head>
<body>
  <h2>AI Coding Agent</h2>
  <textarea id="task" placeholder="Describe your task"></textarea>
  <div>
    <button id="run">Run Agent</button>
    <button id="cancel">Cancel</button>
    <button id="review">Review Changes</button>
    <button id="apply">Apply Changes</button>
    <button id="reject">Reject Changes</button>
  </div>

  <h3>Progress</h3>
  <div id="log" class="log"></div>

  <h3>Changed Files</h3>
  <pre id="files"></pre>

  <h3>Final Diff</h3>
  <pre id="diff"></pre>

  <script>
    const vscode = acquireVsCodeApi();
    const log = document.getElementById("log");
    const files = document.getElementById("files");
    const diff = document.getElementById("diff");

    function append(text) {
      log.textContent += text + "\n";
      log.scrollTop = log.scrollHeight;
    }

    document.getElementById("run").addEventListener("click", () => {
      log.textContent = "";
      files.textContent = "";
      diff.textContent = "";
      vscode.postMessage({ type: "run", task: document.getElementById("task").value });
    });
    document.getElementById("cancel").addEventListener("click", () => vscode.postMessage({ type: "cancel" }));
    document.getElementById("review").addEventListener("click", () => vscode.postMessage({ type: "review" }));
    document.getElementById("apply").addEventListener("click", () => vscode.postMessage({ type: "apply" }));
    document.getElementById("reject").addEventListener("click", () => vscode.postMessage({ type: "reject" }));

    window.addEventListener("message", (event) => {
      const message = event.data;
      if (message.type === "status") {
        append(message.text);
      }
      if (message.type === "event") {
        const ev = message.event;
        append('[' + ev.type + '] ' + JSON.stringify(ev.payload));
        if (ev.type === "agent_completed") {
          const changed = ev.payload.changed_files || [];
          files.textContent = Array.isArray(changed) ? changed.join("\n") : "";
          diff.textContent = String(ev.payload.diff || "");
        }
      }
      if (message.type === "reviewData") {
        const changed = message.data.changed_files || [];
        files.textContent = Array.isArray(changed) ? changed.join("\n") : "";
        diff.textContent = String(message.data.diff || "");
        append('Review loaded. Iterations: ' + message.data.iterations);
      }
    });
  </script>
</body>
</html>`;
}

export function deactivate(): void {
  // no-op
}
