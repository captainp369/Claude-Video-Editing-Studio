#!/bin/bash
# ./render.sh            -> render every example into renders/
# ./render.sh 04 11 13   -> only these numbers
[ -d /opt/homebrew/opt/node@22/bin ] && export PATH=/opt/homebrew/opt/node@22/bin:$PATH   # Apple Silicon Homebrew Node 22
cd "$(dirname "$0")"; mkdir -p renders
nums=("$@"); [ ${#nums[@]} -eq 0 ] && nums=($(ls styles | cut -c1-2))
for n in "${nums[@]}"; do
  d=$(ls styles | grep "^$n-" | head -1); t0=$(date +%s)
  if npx --yes hyperframes@0.6.6 render . -c "styles/$d/example.html" -o "renders/$d.mp4" -w 2 --quiet > "renders/$d.log" 2>&1; then
    echo "$d ok $(( $(date +%s) - t0 ))s"
  else echo "$d FAILED — see renders/$d.log"; fi
done
find . -name '._*' -delete 2>/dev/null
