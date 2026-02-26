import sys

app_path = r"c:\Users\raipr\OneDrive\Desktop\resume\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "for file in files:" in line:
        start_idx = i
        break

for i in range(start_idx, len(lines)):
    if "=== BATCH SCAN COMPLETE" in lines[i]:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print(f"Could not find start or end index. start={start_idx}, end={end_idx}")
    sys.exit(1)

pre_loop = lines[:start_idx]
loop_body = lines[start_idx+1:end_idx]
post_loop = lines[end_idx:]

new_loop_header = [
    "    file_datas = []\n",
    "    for file in files:\n",
    "        if allowed_file(file.filename):\n",
    "            file_datas.append((file.read(), file.filename))\n",
    "\n",
    "    def _process_file(file_data):\n",
    "        file_bytes, filename = file_data\n",
    "        file_hash = hashlib.sha256(file_bytes).hexdigest()\n",
    "        \n",
    "        if candidate_db.is_duplicate(file_hash):\n",
    "            log.info(f\"Duplicate resume skipped: {filename} ({file_hash[:8]}...)\")\n",
    "            return \"skipped\"\n",
    "\n",
    "        log.info(\"Processing file: %s (%d bytes)\", filename, len(file_bytes))\n"
]

logic_start_idx = 0
for i, line in enumerate(loop_body):
    if "STAGE 1" in line:
        logic_start_idx = i
        break

logic_lines = loop_body[logic_start_idx:]

for i, line in enumerate(logic_lines):
    if "processed_count += 1" in line:
        logic_lines[i] = "        # processed_count += 1\n"
    elif "continue" in line and not "for " in line and not "while " in line:
        logic_lines[i] = line.replace("continue", "return \"error\"")
    elif "file.filename" in line:
        logic_lines[i] = line.replace("file.filename", "filename")

logic_lines.append("        return \"processed\"\n\n")

executor_code = [
    "    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(file_datas) or 1)) as executor:\n",
    "        results = list(executor.map(_process_file, file_datas))\n",
    "    \n",
    "    for res in results:\n",
    "        if res == \"skipped\":\n",
    "            skipped_count += 1\n",
    "        elif res == \"processed\":\n",
    "            processed_count += 1\n",
    "\n"
]

all_new_lines = pre_loop + new_loop_header + logic_lines + executor_code + post_loop

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(all_new_lines)

print("Refactored successfully.")
