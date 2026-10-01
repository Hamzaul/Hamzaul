/* miners.js
   Lightweight AI for the field of rival miners. Each rival tracks its own
   tool / wear / time state and makes a "return to the crafting table"
   decision once per turn from tool wear, water level and a little
   randomness, so descents don't play out identically. */

(function () {
  const NAMES = ["COALFOOT", "DEEPDELVER", "GRAVELLE", "IRONJAW", "LODESTAR", "QUARRICK"];

  function createMiner(index) {
    return {
      id: `miner-${index}`,
      name: NAMES[index % NAMES.length],
      tool: "iron",
      uses: 0,
      totalTime: 0,
      crafts: 0,
      out: false, // reserved: retired rival (not currently triggered)
    };
  }

  function createField(count) {
    const field = [];
    for (let i = 0; i < count; i++) field.push(createMiner(i));
    return field;
  }

  /**
   * Decide whether this rival returns to craft at the end of the turn, and
   * which tool it picks. Rules of thumb:
   *  - Craft once wear crosses ~75%, sooner if the tunnel is flooded and the
   *    tool isn't aqua (or it's dry and they're still holding aqua).
   *  - Occasionally craft early at random to vary strategy.
   */
  function decideCraft(miner, water, Tools) {
    const wear = Tools.wearFraction(miner.tool, miner.uses);
    const wrongToolForWater =
      (water === "flooded" && miner.tool !== "aqua") ||
      (water === "dry" && miner.tool === "aqua");

    let shouldCraft = wear > 0.75 || wrongToolForWater;
    if (!shouldCraft && wear > 0.55 && Math.random() < 0.12) shouldCraft = true;
    if (!shouldCraft) return null;

    if (water === "flooded") return "aqua";
    return Math.random() < 0.5 ? "iron" : "diamond";
  }

  /** Simulate one turn (a block of digging) for every rival. */
  function simulateTurn(field, blocksThisTurn, water, Tools) {
    field.forEach((miner) => {
      if (miner.out) return;

      for (let i = 0; i < blocksThisTurn; i++) {
        miner.uses += 1;
        miner.totalTime += Tools.digTime(miner.tool, miner.uses, water);

        const crackChance = Tools.breakChance(miner.tool, miner.uses);
        if (Math.random() < crackChance * 0.5) {
          miner.totalTime += 35; // limp back to repair
        }
      }

      const nextTool = decideCraft(miner, water, Tools);
      if (nextTool) {
        miner.totalTime += Tools.CRAFT_LOSS;
        miner.tool = nextTool;
        miner.uses = 0;
        miner.crafts += 1;
      }
    });
  }

  window.Miners = { createField, simulateTurn };
})();
