import json
import os

import click
import yaml
from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from ovos_config.config import Configuration, LocalConf, MycroftDefaultConfig
from ovos_config.locations import USER_CONFIG

from ovos_yaml_editor.version import VERSION_STR

app = FastAPI()

# Fetch username and password from environment variables
USER = os.getenv("EDITOR_USERNAME", "admin")  # Default to "admin" if not set
PASSWORD = os.getenv("EDITOR_PASSWORD", "password")  # Default to "password" if not set

security = HTTPBasic()

memory_config = Configuration()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate the user."""
    if credentials.username == USER and credentials.password == PASSWORD:
        return True
    else:
        return False


@app.get("/", response_class=HTMLResponse)
async def get_editor(credentials: HTTPBasicCredentials = Depends(authenticate)):
    """Show the editor only if the user is authenticated."""
    if not credentials:
        return RedirectResponse(url="/login")

    return """
<html>
<head>
    <title>OpenVoiceOS Editor</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/theme/darcula.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background-color: #1e1e1e;
            color: #f1f1f1;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            display: flex;
            align-items: center;
            padding: 20px;
            background-color: #333;
            justify-content: space-between;
        }
        .header img {
            height: 40px;
            margin-right: 10px;
        }
        .header h1 {
            font-size: 24px;
            margin: 0;
        }
        .button-container {
            display: flex;
            justify-content: flex-start;
            gap: 10px;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            background-color: #d32f2f; /* Red buttons */
            color: white;
            border: none;
            border-radius: 4px;
        }
        #tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        #tabs button {
            padding: 10px 20px;
            background-color: #333;
            color: white;
            border: 1px solid #ccc;
            cursor: pointer;
        }
        #tabs button.active {
            background-color: #4CAF50;
        }
        #editor {
            flex-grow: 1;
            border: 1px solid #ccc;
        }
        .CodeMirror {
            background-color: #1e1e1e;
            color: #f1f1f1;
            height: 100%;
        }
        .CodeMirror-gutters {
            background-color: #1e1e1e;
            border-right: 1px solid #ccc;
        }
        footer {
            background-color: #333;
            color: #f1f1f1;
            padding: 10px;
            text-align: center;
            font-size: 14px;
        }
        footer a {
            color: #4CAF50;
            text-decoration: none;
        }
        
        button:disabled {
            background-color: #d3d3d3;  /* Light grey */
            cursor: not-allowed;
        }
        .CodeMirror .cm-keyword {
            color: #c586c0;
        }
        .CodeMirror .cm-string {
            color: #ce9178;
        }
        .CodeMirror .cm-number {
            color: #b5cea8;
        }
        .CodeMirror .cm-variable {
            color: #9cdcfe;
        }
        .CodeMirror .cm-variable-2 {
            color: #c586c0;
        }
        .CodeMirror .cm-variable-3 {
            color: #9cdcfe;
        }
        .CodeMirror .cm-def {
            color: #4ec9b0;
        }
        .CodeMirror .cm-comment {
            color: #6a9955;
        }
        .CodeMirror .cm-error {
            color: #f44747;
            background-color: #ff000030;
        }

    </style>
</head>
<body>
    <div class="header">
        <div>
            <img src="https://www.openvoiceos.org/_next/static/media/logo.02220a9b.png" alt="OpenVoiceOS Logo">
            <h1>OpenVoiceOS Config Editor</h1>
        </div>
        <div class="button-container">
            <button onclick="reloadConfig()"><i class="fas fa-sync-alt"></i> Reload</button>
            <button onclick="saveConfig()" id="saveButton"><i class="fas fa-save"></i> Save</button>
            <button onclick="resetConfig()"><i class="fas fa-undo"></i> Reset Config</button>
            <button onclick="reportIssue()"><i class="fas fa-exclamation-circle"></i> Report Issue</button>
        </div>
    </div>
    
    <div id="tabs">
        <button class="active" onclick="switchTab('yaml')">YAML</button>
        <button onclick="switchTab('json')">JSON</button>
    </div>
    
    <div id="editor"></div>
    
    <footer>
        <p>© 2025 OpenVoiceOS. <a href="https://github.com/OpenVoiceOS/ovos-yaml-editor">GitHub</a> | <a href="https://github.com/OpenVoiceOS/ovos-yaml-editor/blob/dev/LICENSE">Apache 2.0 License</a></p>
    </footer>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/yaml/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/javascript/json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js"></script>
    <script>

        let editor;
        
        function initEditor(mode) {
            editor = CodeMirror(document.getElementById('editor'), {
                lineNumbers: true,
                gutters: ["CodeMirror-linenumbers", "CodeMirror-lint-markers"],
                mode: mode === 'yaml' ? "yaml" : { name: "javascript", json: true },
                theme: "darcula",
                tabSize: 2,
                lint: true,
                lintOnChange: true,
                lintOptions: {
                    onUpdateLinting: (annotations, _, doc) => {
                        const errors = annotations.filter(a => a.severity === 'error');
                        console.log("Linting errors: ", errors);  // Debugging line
                        if (errors.length > 0) {
                            document.getElementById('saveButton').disabled = true;
                        } else {
                            document.getElementById('saveButton').disabled = false;
                        }
                    }
                }
            });
        }


        function switchTab(tab) {
            document.querySelectorAll("#tabs button").forEach(button => button.classList.remove("active"));
            document.querySelector(`#tabs button:nth-child(${tab === 'yaml' ? 1 : 2})`).classList.add("active");
            editor.setOption("mode", tab === 'yaml' ? "yaml" : "application/json");
            reloadConfig(tab);
        }

        // Fetch the current config and load it into the editor
        async function reloadConfig() {
            const format = editor.getOption("mode") === "yaml" ? "yaml" : "json";
            const response = await fetch(`/config/${format}`);
            const config = await response.text();
            editor.setValue(config);
        }

        // Save the content of the editor
        async function saveConfig() {
            const data = editor.getValue();
            const format = editor.getOption("mode") === "yaml" ? "yaml" : "json";
            const response = await fetch("/config", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ data: data, format: format })
            });
            const result = await response.json();
            if (result.success) {
                alert("Config saved successfully!");
            } else {
                alert("Error saving config: " + result.error);
            }
        }

        async function resetConfig() {
            if (!confirm("Are you sure you want to reset the config to default? This cannot be undone.")) return;
        
            const response = await fetch("/config/reset", {
                method: "POST"
            });
        
            const result = await response.json();
            if (result.success) {
                alert("Config has been reset to default.");
                reloadConfig();  // Refresh the editor with new config
            } else {
                alert("Error resetting config: " + result.error);
            }
        }

        // Report issue function
        function reportIssue() {
            window.open("https://github.com/OpenVoiceOS/ovos-yaml-editor/issues", "_blank");
        }

        // Initialize the editor with YAML mode
        window.onload = () => {
            initEditor("yaml");
            reloadConfig('yaml');
        };
    </script>
</body>
</html>
    """


# Endpoint to get the config as YAML or JSON based on the tab selected
@app.get("/config/{format}")
async def get_config(format: str, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if not credentials:
        return RedirectResponse(url="/login")
    if format == "json":
        return Response(json.dumps(memory_config, indent=2, ensure_ascii=False), media_type="text/plain")
    elif format == "yaml":
        return Response(yaml.dump(dict(memory_config), default_flow_style=False, sort_keys=False), media_type="text/plain")
    else:
        return {"success": False, "error": "Unsupported format"}


@app.post("/config")
async def save_config_post(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if not credentials:
        return RedirectResponse(url="/login")
    body = await request.json()
    try:
        data = body.get("data", "")
        format = body.get("format", "yaml")

        try:
            if format == 'yaml':
                data = yaml.safe_load(data)
            else:
                data = json.loads(data)
        except Exception as e:
            return {"success": False, "error": str(e)}

        conf = LocalConf(USER_CONFIG)
        default_conf = MycroftDefaultConfig()
        for k, v in data.items():
            v2 = default_conf.get(k)
            # only save to file/memory any value that differs from default config
            if v2 is None or v != v2:
                conf[k] = memory_config[k] = v
            # if value changed back to default, remove it from user conf
            elif v == v2 and k in conf:
                conf.pop(k)
        conf.store()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": f"Failed to save config: {e}"}


@app.post("/config/reset")
async def reset_config_post(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if not credentials:
        return RedirectResponse(url="/login")
    try:
        conf = LocalConf(USER_CONFIG)
        conf.clear()
        conf.store()
        memory_config.reset()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": f"Failed to save config: {e}"}


@app.get("/status")
async def status(request: Request):
    return {"version": VERSION_STR}


@click.command()
@click.option('--host', default='127.0.0.1', help='Set to 0.0.0.0 to make externally accessible.')
@click.option('--port', default=9210, type=int, help='Port to run the app on.')
def main(host, port):
    """Run the OpenVoiceOS config editor Web UI."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
