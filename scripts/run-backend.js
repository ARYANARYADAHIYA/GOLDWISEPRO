const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";
const venvPython = isWin
  ? path.join(rootDir, ".venv", "Scripts", "python.exe")
  : path.join(rootDir, ".venv", "bin", "python");

const pythonExe = fs.existsSync(venvPython) ? venvPython : "python";
const args = ["-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000", ...process.argv.slice(2)];

const child = spawn(pythonExe, args, { cwd: rootDir, stdio: "inherit", shell: false });
child.on("exit", (code) => process.exit(code ?? 0));
