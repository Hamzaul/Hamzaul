/* hud.js
   All DOM reads/writes live here so expedition.js can stay focused on state.
   Also owns dialog behaviour: focus trap, Escape, background inert, and
   returning focus to whatever opened the dialog. */

(function () {
  const el = (id) => document.getElementById(id);

  function fmtTime(seconds) {
    const sign = seconds < 0 ? "-" : "+";
    return `${sign}${Math.abs(seconds).toFixed(1)}s`;
  }

  /* ---------- HUD ---------- */

  function setWear(pctEl, trackEl, barEl, wearFraction) {
    const pct = Math.min(100, Math.round(wearFraction * 100));
    pctEl.textContent = `${pct}%`;
    barEl.style.width = `${pct}%`;
    trackEl.setAttribute("aria-valuenow", String(pct));
    trackEl.setAttribute("aria-valuetext", `${pct}% worn`);
    barEl.classList.remove("wear-ok", "wear-warn", "wear-danger");
    if (pct < 55) barEl.classList.add("wear-ok");
    else if (pct < 90) barEl.classList.add("wear-warn");
    else barEl.classList.add("wear-danger");
  }

  function renderHUD(state, Tools, Flooding) {
    el("hud-depth").textContent = `${state.depth} / ${Flooding.TOTAL_DEPTH}`;
    el("hud-rank").textContent = `#${state.player.position}`;

    const tool = Tools.TOOLS[state.player.tool];
    const badge = el("hud-tool-badge");
    badge.style.setProperty("--tool", tool.color);
    el("hud-tool-name").textContent = `${tool.label} PICKAXE`;

    const wear = Tools.wearFraction(state.player.tool, state.player.uses);
    setWear(el("hud-wear-pct"), el("hud-wear-track"), el("hud-wear-bar"), wear);

    const leaderTime = state.field.length ? Math.min(...state.field.map((r) => r.totalTime)) : 0;
    const gap = state.player.totalTime - leaderTime;
    el("hud-gap").textContent = state.player.position === 1 ? "LEADING" : fmtTime(gap);

    const risk = Flooding.forecast(state.water, state.depth, 10);
    el("hud-water").textContent =
      state.water === "flooded" ? "FLOODED — AQUA PICK ADVISED" : `${risk}% flood risk (next 10 blocks)`;
    el("hud-water-cell").classList.toggle("water-active", state.water === "flooded");
    document.body.classList.toggle("flooded", state.water === "flooded");

    const ready = state.field.filter((r) => {
      const w = Tools.wearFraction(r.tool, r.uses);
      return w > 0.55 && w < 0.85 && !r.out;
    }).length;
    el("hud-rival-window").textContent = `${ready} of ${state.field.length} rivals about to head back to craft`;

    el("hud-crafts").textContent = state.player.crafts;
  }

  function renderStandings(state, Tools) {
    const rows = [
      { name: "YOU", totalTime: state.player.totalTime, isPlayer: true, tool: state.player.tool },
      ...state.field.map((r) => ({ name: r.name, totalTime: r.totalTime, isPlayer: false, tool: r.tool })),
    ].sort((a, b) => a.totalTime - b.totalTime);

    const leaderTime = rows[0].totalTime;
    const tbody = el("standings-body");
    tbody.textContent = "";
    rows.forEach((row, i) => {
      const tr = document.createElement("tr");
      if (row.isPlayer) tr.classList.add("standings-player");
      const tool = Tools.TOOLS[row.tool];

      const rank = document.createElement("td");
      rank.textContent = `#${i + 1}`;
      const name = document.createElement("td");
      name.textContent = row.name;
      const toolCell = document.createElement("td");
      const chip = document.createElement("span");
      chip.className = "tool-chip";
      chip.textContent = tool.short;
      chip.style.setProperty("--tool", tool.color);
      chip.setAttribute("role", "img");
      chip.setAttribute("aria-label", `${tool.label} pickaxe`);
      toolCell.appendChild(chip);
      const gap = document.createElement("td");
      gap.textContent = i === 0 ? "—" : fmtTime(row.totalTime - leaderTime);

      tr.append(rank, name, toolCell, gap);
      tbody.appendChild(tr);
    });

    return rows.findIndex((r) => r.isPlayer) + 1;
  }

  function log(message, cls) {
    const logEl = el("expedition-log");
    const line = document.createElement("div");
    line.className = `log-line${cls ? " " + cls : ""}`;
    line.textContent = message;
    logEl.prepend(line);
    while (logEl.children.length > 40) logEl.removeChild(logEl.lastChild);
  }

  /* ---------- Dialogs ---------- */

  let activeDialog = null;
  let lastFocus = null;

  function focusables(root) {
    return Array.from(root.querySelectorAll('button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'));
  }

  function onKeydown(e) {
    if (!activeDialog) return;
    if (e.key === "Escape" && activeDialog.dataset.dismissible === "true") {
      e.preventDefault();
      closeDialog(activeDialog);
      return;
    }
    if (e.key !== "Tab") return;
    const items = focusables(activeDialog);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (!activeDialog.contains(document.activeElement)) {
      e.preventDefault();
      first.focus();
    } else if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function setBackgroundInert(on) {
    const app = el("app");
    if ("inert" in app) app.inert = on;
    else app.setAttribute("aria-hidden", on ? "true" : "false");
  }

  function openDialog(overlay, initialFocus) {
    lastFocus = document.activeElement;
    overlay.classList.remove("hidden");
    setBackgroundInert(true);
    activeDialog = overlay;
    document.addEventListener("keydown", onKeydown);
    const target = initialFocus || focusables(overlay)[0];
    if (target) target.focus();
  }

  function closeDialog(overlay, focusTarget) {
    overlay.classList.add("hidden");
    setBackgroundInert(false);
    activeDialog = null;
    document.removeEventListener("keydown", onKeydown);
    const target = focusTarget || lastFocus;
    if (target && typeof target.focus === "function") target.focus();
  }

  function showToolDialog(onPick, water) {
    const dialog = el("tool-dialog");
    dialog.querySelectorAll("[data-tool]").forEach((btn) => {
      btn.onclick = () => {
        closeDialog(dialog);
        onPick(btn.getAttribute("data-tool"));
      };
    });
    el("tool-cancel").onclick = () => closeDialog(dialog);
    el("flood-hint").classList.toggle("hidden", water !== "flooded");
    const preferred = water === "flooded" ? dialog.querySelector('[data-tool="aqua"]') : dialog.querySelector('[data-tool="iron"]');
    openDialog(dialog, preferred);
  }

  function setActionsEnabled(enabled) {
    el("btn-craft").disabled = !enabled;
    el("btn-dig").disabled = !enabled;
  }

  function showResults(finalRank, points, isNewHighScore, highScore) {
    const overlay = el("results-dialog");
    el("results-rank").textContent = `#${finalRank}`;
    el("results-points").textContent = `${points} XP`;
    el("results-best").textContent = `BEST: #${highScore.position} · ${highScore.points} XP`;
    el("results-badge").classList.toggle("hidden", !isNewHighScore);
    openDialog(overlay, el("btn-play-again"));
  }

  function hideResults(focusTarget) {
    const overlay = el("results-dialog");
    if (!overlay.classList.contains("hidden")) closeDialog(overlay, focusTarget);
  }

  /** Fill the tool dialog's stat lines from the single source of truth (Tools). */
  function hydrateToolButtons(Tools) {
    el("tool-dialog").querySelectorAll("[data-tool]").forEach((btn) => {
      const tool = Tools.TOOLS[btn.getAttribute("data-tool")];
      btn.style.setProperty("--tool", tool.color);
      btn.querySelector(".tool-stats").textContent =
        `+${tool.pace.toFixed(1)}s/BLOCK · LASTS ${tool.durability}`;
    });
  }

  /** Backdrop click closes the dismissible dialog. */
  function bindBackdrop() {
    const dialog = el("tool-dialog");
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) closeDialog(dialog);
    });
  }

  window.HUD = {
    el, renderHUD, renderStandings, log, showToolDialog, setActionsEnabled,
    showResults, hideResults, hydrateToolButtons, bindBackdrop,
  };
})();
