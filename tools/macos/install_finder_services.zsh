#!/bin/zsh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
TRANSCRIBE_SCRIPT="$PROJECT_DIR/skill/scripts/transcribe.py"
SERVICES_DIR="$HOME/Library/Services"

mkdir -p "$SERVICES_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="/usr/bin/python3"
fi

write_info_plist() {
  local workflow_dir="$1"
  local menu_title="$2"
  mkdir -p "$workflow_dir/Contents"
  cat > "$workflow_dir/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSServices</key>
  <array>
    <dict>
      <key>NSBackgroundColorName</key>
      <string>background</string>
      <key>NSIconName</key>
      <string>NSActionTemplate</string>
      <key>NSMenuItem</key>
      <dict>
        <key>default</key>
        <string>$menu_title</string>
      </dict>
      <key>NSMessage</key>
      <string>runWorkflowAsService</string>
      <key>NSRequiredContext</key>
      <dict>
        <key>NSApplicationIdentifier</key>
        <string>com.apple.finder</string>
      </dict>
      <key>NSSendFileTypes</key>
      <array>
        <string>public.audio</string>
        <string>public.movie</string>
        <string>com.apple.m4a-audio</string>
        <string>public.mpeg-4</string>
      </array>
    </dict>
  </array>
</dict>
</plist>
PLIST
}

write_workflow() {
  local workflow_dir="$1"
  local title="$2"
  local extra_args="$3"
  local escaped_python="${PYTHON_BIN//&/&amp;}"
  local escaped_script="${TRANSCRIBE_SCRIPT//&/&amp;}"
  local command="'$escaped_python' '$escaped_script' $extra_args \$ARGS"

  cat > "$workflow_dir/Contents/document.wflow" <<WFLOW
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>AMApplicationBuild</key>
  <string>521.1</string>
  <key>AMApplicationVersion</key>
  <string>2.10</string>
  <key>AMDocumentVersion</key>
  <string>2</string>
  <key>actions</key>
  <array>
    <dict>
      <key>action</key>
      <dict>
        <key>AMAccepts</key>
        <dict>
          <key>Container</key>
          <string>List</string>
          <key>Optional</key>
          <true/>
          <key>Types</key>
          <array>
            <string>com.apple.cocoa.string</string>
          </array>
        </dict>
        <key>AMActionVersion</key>
        <string>2.0.3</string>
        <key>AMApplication</key>
        <array>
          <string>Automator</string>
        </array>
        <key>AMProvides</key>
        <dict>
          <key>Container</key>
          <string>List</string>
          <key>Types</key>
          <array>
            <string>com.apple.cocoa.string</string>
          </array>
        </dict>
        <key>ActionBundlePath</key>
        <string>/System/Library/Automator/Run Shell Script.action</string>
        <key>ActionName</key>
        <string>Run Shell Script</string>
        <key>ActionParameters</key>
        <dict>
          <key>COMMAND_STRING</key>
          <string>ARGS=""
for f in "\$@"; do
  if [ -f "\$f" ]; then
    escaped=\$(printf "%q" "\$f")
    ARGS="\$ARGS \$escaped"
  fi
done

if [ -z "\$ARGS" ]; then
  osascript -e 'display notification "No audio files selected" with title "$title"'
  exit 0
fi

osascript &lt;&lt;APPLESCRIPT
tell application "Terminal"
  activate
  set theTab to do script "clear; echo '$title'; echo ''; $command; echo ''; echo 'Done. Press any key to close.'; read -k1; exit"
  set custom title of theTab to "$title"
end tell
APPLESCRIPT</string>
          <key>CheckedForUserDefaultShell</key>
          <true/>
          <key>inputMethod</key>
          <integer>1</integer>
          <key>shell</key>
          <string>/bin/zsh</string>
          <key>source</key>
          <string></string>
        </dict>
        <key>BundleIdentifier</key>
        <string>com.apple.RunShellScript</string>
        <key>CFBundleVersion</key>
        <string>2.0.3</string>
        <key>CanShowSelectedItemsWhenRun</key>
        <false/>
        <key>CanShowWhenRun</key>
        <true/>
        <key>Class Name</key>
        <string>RunShellScriptAction</string>
        <key>UUID</key>
        <string>$(uuidgen)</string>
      </dict>
      <key>isViewVisible</key>
      <integer>1</integer>
    </dict>
  </array>
  <key>connectors</key>
  <dict/>
  <key>workflowMetaData</key>
  <dict>
    <key>applicationBundleID</key>
    <string>com.apple.finder</string>
    <key>applicationPath</key>
    <string>/System/Library/CoreServices/Finder.app</string>
    <key>inputTypeIdentifier</key>
    <string>com.apple.Automator.fileSystemObject</string>
    <key>outputTypeIdentifier</key>
    <string>com.apple.Automator.nothing</string>
    <key>presentationMode</key>
    <integer>15</integer>
    <key>serviceApplicationBundleID</key>
    <string>com.apple.finder</string>
    <key>serviceApplicationPath</key>
    <string>/System/Library/CoreServices/Finder.app</string>
    <key>serviceInputTypeIdentifier</key>
    <string>com.apple.Automator.fileSystemObject</string>
    <key>serviceOutputTypeIdentifier</key>
    <string>com.apple.Automator.nothing</string>
    <key>serviceProcessesInput</key>
    <false/>
    <key>workflowTypeIdentifier</key>
    <string>com.apple.Automator.servicesMenu</string>
  </dict>
</dict>
</plist>
WFLOW
}

install_service() {
  local name="$1"
  local title="$2"
  local extra_args="$3"
  local workflow_dir="$SERVICES_DIR/$name.workflow"
  write_info_plist "$workflow_dir" "$title"
  write_workflow "$workflow_dir" "$title" "$extra_args"
  plutil -lint "$workflow_dir/Contents/Info.plist" "$workflow_dir/Contents/document.wflow" >/dev/null
  echo "Installed: $workflow_dir"
}

install_service "Transcribe Audio" "Transcribe Audio" ""
install_service "Transcribe Audio by Persons" "Transcribe Audio by Persons" "--persons"

touch "$SERVICES_DIR"
echo "Finder Quick Actions installed. If they do not appear immediately, relaunch Finder."
