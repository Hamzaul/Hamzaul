/* rivals.js
   Lightweight AI for the field of rival cars. Each rival tracks its own
   tyre/compound/time state and makes a pit decision once per turn based on
   tyre wear, weather, and a bit of randomness so races don't play out
   identically. */

(function () {
  const NAMES = ["VERAK", "OKONNA", "LINDQVIST", "SATO", "PEREIRA", "NOVAK"];

  function createRival(index) {
    return {
      id: `rival-${index}`,
      name: NAMES[index % NAMES.length],
      compound: "medium",
      tyreAge: 0,
      totalTime: 0,
      pitStops: 0,
      out: false, // true if retired (rare, from bad puncture)
    };
  }

  function createField(count) {
    const field = [];
    for (let i = 0; i < count; i++) field.push(createRival(i));
    return field;
  }

  /**
   * Decide whether this rival pits at the end of the current turn, and if
   * so which compound they switch to. Rules of thumb:
   *  - Pit once wear crosses ~75%, sooner if it's raining and they're on
   *    slicks (or dry and they're on wets).
   *  - Occasionally pit early/late at random to vary strategy.
   */
  function decidePitStop(rival, weather, Strategy) {
    const wear = Strategy.wearFraction(rival.compound, rival.tyreAge);
    const wrongTyreForWeather =
      (weather === "wet" && rival.compound !== "wet") ||
      (weather === "dry" && rival.compound === "wet");

    let shouldPit = wear > 0.75 || wrongTyreForWeather;
    if (!shouldPit && wear > 0.55 && Math.random() < 0.12) shouldPit = true;

    if (!shouldPit) return null;

    let nextCompound;
    if (weather === "wet") {
      nextCompound = "wet";
    } else {
      nextCompound = Math.random() < 0.5 ? "medium" : "hard";
    }
    return nextCompound;
  }

  /**
   * Simulate one turn (a block of laps) for every rival.
   */
  function simulateTurn(field, lapsThisTurn, weather, Strategy) {
    field.forEach((rival) => {
      if (rival.out) return;

      for (let i = 0; i < lapsThisTurn; i++) {
        rival.tyreAge += 1;
        const lapTime = Strategy.calculateLapTime(rival.compound, rival.tyreAge, weather);
        rival.totalTime += lapTime;

        const punctureChance = Strategy.punctureChance(rival.compound, rival.tyreAge);
        if (Math.random() < punctureChance * 0.5) {
          rival.totalTime += 35; // limp to the pits
        }
      }

      const nextCompound = decidePitStop(rival, weather, Strategy);
      if (nextCompound) {
        rival.totalTime += Strategy.PIT_LOSS;
        rival.compound = nextCompound;
        rival.tyreAge = 0;
        rival.pitStops += 1;
      }
    });
  }

  window.Rivals = { createField, simulateTurn };
})();
