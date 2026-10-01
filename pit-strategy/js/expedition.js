/* expedition.js
   State machine: INIT -> DIGGING -> (CRAFTING) -> DIGGING -> ... -> FINISH -> RESULTS
   Wires together Tools (wear model), Flooding, Miners (AI) and HUD (rendering). */

(function () {
  const { Tools, Flooding, Miners, HUD } = window;

  const DIG_STEP = 5;      // blocks dug per turn
  const NUM_RIVALS = 5;
  const XP_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1];

  // Legacy key, kept on purpose: the game used to live under this name, and
  // keeping it means players who already have a saved best keep their score.
  const HIGH_SCORE_KEY = "pit-strategy-highscore";

  let state = null;
  let busy = false;

  function loadHighScore() {
    try {
      const raw = localStorage.getItem(HIGH_SCORE_KEY);
      if (!raw) return { position: 99, points: 0 };
      const parsed = JSON.parse(raw);
      if (typeof parsed.position !== "number" || typeof parsed.points !== "number") {
        return { position: 99, points: 0 };
      }
      return parsed;
    } catch (e) {
      return { position: 99, points: 0 };
    }
  }

  function saveHighScore(hs) {
    try {
      localStorage.setItem(HIGH_SCORE_KEY, JSON.stringify(hs));
    } catch (e) {
      /* ignore storage errors (private mode etc.) */
    }
  }

  function newGame() {
    state = {
      depth: 0,
      water: "dry",
      player: { tool: "iron", uses: 0, totalTime: 0, crafts: 0, position: 4 },
      field: Miners.createField(NUM_RIVALS),
      finished: false,
    };
    busy = false;

    HUD.setActionsEnabled(true); // enable first so focus can land on Keep Digging
    HUD.hideResults(HUD.el("btn-dig"));
    HUD.el("expedition-log").textContent = "";
    HUD.log(`TORCHES LIT. The descent begins — ${Flooding.TOTAL_DEPTH} blocks to the Deep Vein.`, "log-start");
    updatePositions();
    render();
  }

  function updatePositions() {
    const all = [
      { ref: "player", totalTime: state.player.totalTime },
      ...state.field.map((r, i) => ({ ref: i, totalTime: r.totalTime })),
    ].sort((a, b) => a.totalTime - b.totalTime);
    state.player.position = all.findIndex((r) => r.ref === "player") + 1;
  }

  function render() {
    HUD.renderHUD(state, Tools, Flooding);
    HUD.renderStandings(state, Tools);
  }

  function simulatePlayerTurn(blocks) {
    for (let i = 0; i < blocks; i++) {
      state.player.uses += 1;
      state.player.totalTime += Tools.digTime(state.player.tool, state.player.uses, state.water);

      const chance = Tools.breakChance(state.player.tool, state.player.uses);
      if (Math.random() < chance * 0.5) {
        state.player.totalTime += 35;
        HUD.log(`Depth ${state.depth + i + 1}: your pickaxe is cracking — a costly detour to repair it.`, "log-warn");
      }
    }
  }

  function playTurn(action, chosenTool) {
    if (!state || state.finished || busy) return;
    busy = true;

    const remaining = Flooding.TOTAL_DEPTH - state.depth;
    const blocks = Math.min(DIG_STEP, remaining);

    // The water level can shift once per turn
    const roll = Flooding.rollWater(state.water, state.depth);
    if (roll.changed) {
      state.water = roll.water;
      HUD.log(
        roll.water === "flooded" ? "The tunnel has flooded — water is rising around you!" : "The water drains away — tunnels are clear.",
        "log-water"
      );
    }

    if (action === "craft") {
      state.player.totalTime += Tools.CRAFT_LOSS;
      state.player.tool = chosenTool;
      state.player.uses = 0;
      state.player.crafts += 1;
      HUD.log(`Depth ${state.depth}: back at the crafting table — fitting a ${Tools.TOOLS[chosenTool].label} pickaxe.`, "log-craft");
    }

    simulatePlayerTurn(blocks);
    Miners.simulateTurn(state.field, blocks, state.water, Tools);

    state.depth += blocks;
    updatePositions();
    render();

    HUD.log(`Depth ${state.depth}: you are ranked #${state.player.position}.`);

    busy = false;
    if (state.depth >= Flooding.TOTAL_DEPTH) finishExpedition();
  }

  function finishExpedition() {
    state.finished = true;
    HUD.setActionsEnabled(false);

    const finalRank = HUD.renderStandings(state, Tools);
    const points = finalRank <= XP_TABLE.length ? XP_TABLE[finalRank - 1] : 0;

    HUD.log(`DEEP VEIN REACHED. You finished #${finalRank} (${points} XP).`, "log-finish");

    const best = loadHighScore();
    const isNewBest = points > best.points || (points === best.points && finalRank < best.position);
    if (isNewBest) saveHighScore({ position: finalRank, points });

    HUD.showResults(finalRank, points, isNewBest, isNewBest ? { position: finalRank, points } : best);
  }

  function onCraftClicked() {
    if (!state || state.finished) return;
    HUD.showToolDialog((tool) => playTurn("craft", tool), state.water);
  }

  function onDigClicked() {
    playTurn("dig");
  }

  function init() {
    HUD.hydrateToolButtons(Tools);
    HUD.bindBackdrop();
    HUD.el("btn-craft").addEventListener("click", onCraftClicked);
    HUD.el("btn-dig").addEventListener("click", onDigClicked);
    HUD.el("btn-play-again").addEventListener("click", newGame);
    newGame();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
