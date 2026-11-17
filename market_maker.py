"""
Market-making simulator
=======================
A simple market maker quotes a bid and an ask around a random-walk price.
Random buyers and sellers (and informed traders) trade against
those quotes. The script runs three experiments:
 
  1. Spread:             how wide should the quotes be?
  2. Inventory Skew:     does shifting quotes against inventory reduce risk?
  3. Adverse Selection:  what happens when some traders know the next price?
"""

import numpy as np
import matplotlib.pyplot as plt


def market_maker_simulation(half_spread, start_price = 100, steps = 1000, volatility = 0.01, skew = 0, base = 0.4, informed_prob = 0):

    """
    Parameters
    ----------
    half_spread   : distance of the bid and ask from the true price
    start_price   : starting value of the true price
    steps         : number of time steps in the run
    volatility    : size of each random price move, as a fraction of start_price
    skew          : how far both quotes shift per unit of inventory
                    (positive skew pushes quotes down when long, up when short)
    base          : arrival chance of a trader when a quote sits exactly at the true price
    informed_prob : chance per step that an informed trader (who knows the
                    next price) arrives
 
    Returns
    -------
    prices, cash_history, inventory_history, pnl  (each an array of length `steps`)
    """
    # Generating the true price path
    # Price changes are drawn from the normal distribution
    price_changes = np.random.normal(0, volatility, steps)
    prices = start_price * (1 + np.cumsum(price_changes))

    # Initialising varibales
    cash = 0 # money recived minus money paid
    inventory = 0 # # units held (positive = long, negative = short)
    cash_history = []
    inventory_history = []

    for i in range(len(prices)):

        price = prices[i]

        # The skew term shifts both quotes
        # down when inventory is positive 
        # (to attract buyers and discourage sellers) 
        # and up when inventory is negative.

        bid = price - half_spread - skew * inventory
        ask = price + half_spread - skew * inventory

        # Informed trader: arrives with probability informed_prob, and can see
        # the next price. Only trades if it is profitable for them, which means
        # the market maker loses on every informed trade (adverse selection).
        # The `i < len(prices) - 1` check avoids reading past the last price.

        if i < len(prices) - 1 and informed_prob > np.random.random():
                if prices[i + 1] > ask:    # next price is above the ask: they buy
                    cash += ask
                    inventory -= 1
                elif prices[i + 1] < bid: # next price is below the bid: they sell
                    cash -= bid
                    inventory += 1

        # Random (uninformed) traders. The further a quote is from the true
        # price, the less likely someone trades at it, so wider spreads mean
        # fewer trades. min(..., 1) keeps the probability valid.
        p_buyer = min(base * np.exp(-(ask - price)), 1)
        p_seller = min(base * np.exp(-(price - bid)), 1)

        if np.random.random() < p_buyer:      # a buyer lifts your ask
            cash += ask
            inventory -= 1
        if np.random.random() < p_seller:     # a seller hits your bid
            cash -= bid
            inventory += 1

        cash_history.append(cash)
        inventory_history.append(inventory)

    # Computing profit/loss
    cash_history = np.array(cash_history)
    inventory_history = np.array(inventory_history)
    pnl = cash_history + inventory_history * prices

    return prices, cash_history, inventory_history, pnl

if __name__ == "__main__":
    np.random.seed(52)

# =====================================================================
# Single run: plot price, inventory and PnL over time
# =====================================================================

    prices, cash_history, inventory_history, pnl = market_maker_simulation(half_spread=0.5, skew=0)

    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 8))

    axes[0].plot(prices)
    axes[0].set_ylabel("Price")
    axes[0].set_title("Single simulation run")

    axes[1].plot(inventory_history)
    axes[1].axhline(0, color="grey", linestyle="--")
    axes[1].set_ylabel("Inventory")

    axes[2].plot(pnl)
    axes[2].axhline(0, color="grey", linestyle="--")
    axes[2].set_ylabel("PnL")
    axes[2].set_xlabel("Time step")

    plt.tight_layout()
    plt.savefig("single_run.png", dpi=150)
    plt.show()

# ==========================================================================
# Experiment 1: Spread
# Run many simulations at each spread and compare mean and std of final PnL.
# ==========================================================================
    spreads = [0.1, 0.25, 0.5, 1.0, 1.25, 1.5, 2.0]
    n_runs = 1000 

    means = [] # mean final PnL for each spread
    stds = []  # standard deviation of final PnL for each spread (a measure of risk)

    for half_spread in spreads:
        final_pnls = []

        for n in range(n_runs):
            _, _, _, pnl = market_maker_simulation(half_spread)
            final_pnls.append(pnl[-1])

        means.append(np.mean(final_pnls))
        stds.append(np.std(final_pnls))
        print(f"half_spread = {half_spread:<5}  "
            f"mean PnL = {means[-1]:8.1f}  std = {stds[-1]:7.1f}  mean/std = {means[-1]/stds[-1]:.2f}")


# Dots are the mean; the bars show +/- 1 standard deviation across runs.
    plt.errorbar(spreads, means, yerr=stds, marker="o", capsize=4)
    plt.axhline(0, color="grey", linestyle="--")
    plt.xlabel("Half-spread")
    plt.ylabel("Final PnL (mean ± 1 std)")
    plt.title("Final PnL vs Spread")
    plt.savefig("spread_experiment.png", dpi=150)
    plt.show()

# =====================================================================
# Experiment 2: Inventory Skew
# Track both profit and how far inventory drifts from zero.
# =====================================================================
    skews = [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]

    means_pnl = []
    stds_pnl = []
    means_inventory = []
    stds_inventory = []

    for skew in skews:
        final_pnls = []
        final_inventories = []

        for _ in range(n_runs):
        # Fix the half-spread at 0.5
            _, _, inventory_history, pnl = market_maker_simulation(half_spread = 0.5, skew=skew)
            final_pnls.append(pnl[-1])
            final_inventories.append(inventory_history[-1])

        means_pnl.append(np.mean(final_pnls))
        stds_pnl.append(np.std(final_pnls))
        means_inventory.append(np.mean(final_inventories))
        stds_inventory.append(np.std(final_inventories))

        print(f"skew = {skew:<5} "
            f"mean PnL = {means_pnl[-1]:8.1f}  std PnL = {stds_pnl[-1]:7.1f} "
            f"mean Inventory = {means_inventory[-1]:8.1f}  std Inventory = {stds_inventory[-1]:7.1f}")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].errorbar(skews, means_pnl, yerr=stds_pnl, marker="o", capsize=4)
    axes[0].axhline(0, color="grey", linestyle="--")
    axes[0].set_xlabel("Skew")
    axes[0].set_ylabel("Final PnL (mean ± 1 std)")
    axes[0].set_title("Profit vs skew")

    axes[1].plot(skews, stds_inventory, marker="o")
    axes[1].set_xlabel("Skew")
    axes[1].set_ylabel("Std of final inventory")
    axes[1].set_title("Inventory risk vs skew")

    plt.tight_layout()
    plt.savefig("skew_experiment.png", dpi=150)
    plt.show() 

# =====================================================================
# Experiment 3: Adverse Selection
# Vary the chance of an informed trader arriving each step, and for each
# level, change the spread.
# =====================================================================
    informed_probs = [0, 0.1, 0.3, 0.5, 1.0]
    spreads = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
    n_runs = 1000   # test small first, then raise to 300-500

    for informed_prob in informed_probs:
        means = []
        stds = []

        for half_spread in spreads:
            final_pnls = []

            for _ in range(n_runs):
                _, _, _, pnl = market_maker_simulation(half_spread, informed_prob=informed_prob)
                final_pnls.append(pnl[-1])

            means.append(np.mean(final_pnls))
            stds.append(np.std(final_pnls))
            print(f"informed_prob = {informed_prob:<4} half_spread = {half_spread:<5} "
                f"mean PnL = {means[-1]:8.1f}  std = {stds[-1]:7.1f}")

        plt.plot(spreads, means, marker="o", label=f"informed_prob = {informed_prob}")

    plt.axhline(0, color="grey", linestyle="--")
    plt.xlabel("Half-spread")
    plt.ylabel("Mean final PnL")
    plt.title("PnL vs spread with informed traders")
    plt.legend()
    plt.savefig("adverse_selection_experiment.png", dpi=150)
    plt.show()