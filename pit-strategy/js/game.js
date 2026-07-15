/* game.js
   State machine: INIT -> RACING -> (PIT_STOP) -> RACING -> ... -> FINISH -> RESULTS
   Wires together Strategy (tyre model), Weather, Rivals (AI) and UI (rendering). */

(function () {
  const { Strategy } = window;
  const { Weather } = window;
  const { Rivals } = window;
  const { UI } = window;

  const TURN_LAPS = 5;
  const NUM_RIVALS = 5;
  const POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1];
  const HIGH_SCORE_KEY = "pit-strategy-highscore";

  let state = null;

  function loadHighScore() {
    try {
      const raw = localStorage.getItem(HIGH_SCORE_KEY);
      if (!raw) return { position: 99, points: 0 };
      return JSON.parse(raw);
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
    const field = Rivals.createField(NUM_RIVALS);
    state = {
      lap: 0,
      weather: "dry",
      player: {
        compound: "medium",
        tyreAge: 0,
        totalTime: 0,
        pitStops: 0,
        position: 4,
      },
      field,
      finished: false,
    };

    UI.hideResults();
    UI.el("race-log").innerHTML = "";
    UI.log("LIGHTS OUT. Race start — 50 laps.", "log-start");
    updatePositions();
    render();
    UI.setActionsEnabled(true);
  }

  function updatePositions() {
    const all = [
      { ref: "player", totalTime: state.player.totalTime },
      ...state.field.map((r, i) => ({ ref: i, totalTime: r.totalTime })),
    ].sort((a, b) => a.totalTime - b.totalTime);

    const playerIndex = all.findIndex((r) => r.ref === "player");
    state.player.position = playerIndex + 1;
  }

  function render() {
    UI.renderHUD(state, Strategy, Weather);
    UI.renderStandings(state, Strategy);
  }

  function simulatePlayerTurn(lapsThisTurn) {
    for (let i = 0; i < lapsThisTurn; i++) {
      state.player.tyreAge += 1;
      const lapTime = Strategy.calculateLapTime(state.player.compound, state.player.tyreAge, state.weather);
      state.player.totalTime += lapTime;

      const pChance = Strategy.punctureChance(state.player.compound, state.player.tyreAge);
      if (Math.random() < pChance * 0.5) {
        state.player.totalTime += 35;
        UI.log(`Lap ${state.lap + i + 1}: vibration through the wheel — tyre is going off badly.`, "log-warn");
      }
    }
  }

  function playTurn(action, chosenCompound) {
    if (!state || state.finished) return;
    UI.setActionsEnabled(false);

    const lapsRemaining = Weather.TOTAL_LAPS - state.lap;
    const lapsThisTurn = Math.min(TURN_LAPS, lapsRemaining);

    // Weather can shift once per turn
    const roll = Weather.rollWeather(state.weather, state.lap);
    if (roll.changed) {
      state.weather = roll.weather;
      UI.log(
        roll.weather === "wet" ? "🌧 Rain has started falling on track!" : "☀ Track is drying out.",
        "log-weather"
      );
    }

    if (action === "pit") {
      state.player.totalTime += Strategy.PIT_LOSS;
      state.player.compound = chosenCompound;
      state.player.tyreAge = 0;
      state.player.pitStops += 1;
      UI.log(
        `Lap ${state.lap}: BOX BOX BOX — fitting ${Strategy.COMPOUNDS[chosenCompound].label} tyres.`,
        "log-pit"
      );
    }

    simulatePlayerTurn(lapsThisTurn);
    Rivals.simulateTurn(state.field, lapsThisTurn, state.weather, Strategy);

    state.lap += lapsThisTurn;
    updatePositions();
    render();

    UI.log(`Lap ${state.lap}: you are running P${state.player.position}.`);

    if (state.lap >= Weather.TOTAL_LAPS) {
      finishRace();
    } else {
      UI.setActionsEnabled(true);
    }
  }

  function finishRace() {
    state.finished = true;
    const finalPosition = UI.renderStandings(state, Strategy);
    const points = finalPosition <= POINTS.length ? POINTS[finalPosition - 1] : 0;

    UI.log(`🏁 CHECKERED FLAG. You finished P${finalPosition} (${points} pts).`, "log-finish");

    const highScore = loadHighScore();
    const isNewHighScore =
      points > highScore.points || (points === highScore.points && finalPosition < highScore.position);

    if (isNewHighScore) {
      saveHighScore({ position: finalPosition, points });
    }

    UI.showResults(finalPosition, points, isNewHighScore, isNewHighScore ? { position: finalPosition, points } : highScore);
    UI.setActionsEnabled(false);
  }

  function onPitClicked() {
    UI.showCompoundModal((compound) => playTurn("pit", compound), state.weather);
  }

  function onStayClicked() {
    playTurn("stay");
  }

  function init() {
    UI.el("btn-pit").addEventListener("click", onPitClicked);
    UI.el("btn-stay").addEventListener("click", onStayClicked);
    UI.el("btn-play-again").addEventListener("click", newGame);
    newGame();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
