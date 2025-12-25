"""Swell-resistant epoxy mix calculator.

A tool to help calculate the correct ratio of epoxy base and hardener,
compensating for measurement inaccuracies by using multiple measurements.
"""

import click


def avg(coll):
    return sum(coll) / len(coll)


def chop_extremes(coll, strip_num):
    coll = sorted(coll)
    return coll[strip_num:-strip_num]


def find_midpoint(coll, min_readings=6):
    """Calculate a stable midpoint from multiple readings.

    For min_readings >= 6: uses trimmed mean (removes 2 extremes from each end).
    For min_readings < 6: uses simple average of all readings.
    """
    if min_readings >= 6:
        assert len(coll) >= 6
        coll = chop_extremes(coll, 2)
    return avg(coll)


def find_hardener(tara, base, hardener, tot_weight, adding, part100, min_readings=6):
    if isinstance(tara, list):
        tara = find_midpoint(tara, min_readings)
    if isinstance(base, list):
        base = find_midpoint(base, min_readings) - tara
    if isinstance(tot_weight, list):
        tot_weight = find_midpoint(tot_weight, min_readings)
        mass_added = tot_weight - base - tara - hardener
        if mass_added <= 0:
            click.echo(f"Error: Weight didn't increase (expected > {base + tara + hardener:.1f}g, got {tot_weight:.1f}g)")
            click.echo("Please check your measurements and try again.")
            return None
        click.echo(f"New {adding} added: {mass_added:.1f}g")
        if adding == "hardener":
            hardener += mass_added
        elif adding == "base":
            base += mass_added
    hardener_needed = base * part100 / 100 - hardener
    click.echo(f"tara: {tara:.1f}g")
    click.echo(f"base: {base:.1f}g")
    click.echo(f"hardener: {hardener:.1f}g")
    click.echo(f"more hardener needed: {hardener_needed:.1f}g")
    click.echo(
        f"total weight needed: {tara + base + hardener + max(hardener_needed, -hardener_needed / part100 * 100):.1f}g"
    )
    return (tara, base, hardener, hardener_needed)


def check_outlier(value, existing_values, threshold=3.0):
    """Check if a value is an outlier compared to existing values.

    Returns True if the value deviates more than threshold from the mean,
    relative to the range of existing values.
    """
    if len(existing_values) < 2:
        return False
    mean = avg(existing_values)
    value_range = max(existing_values) - min(existing_values)
    if value_range < 0.5:  # If values are very close, use absolute threshold
        value_range = 1.0
    deviation = abs(value - mean)
    return deviation > value_range * threshold


def interactive_read_numbers(what, min_readings=6):
    ret = []
    while True:
        number = click.prompt(f"Enter {what}", default="---")
        if number == "---":
            if len(ret) < min_readings:
                click.echo(f"At least {min_readings} reading(s) needed!")
                continue
            break
        if number.lower() == "undo":
            if ret:
                removed = ret.pop()
                click.echo(f"Removed {removed:.1f}. {len(ret)} reading(s) remaining.")
            else:
                click.echo("Nothing to undo.")
            continue
        try:
            number = float(number)
        except ValueError:
            click.echo("Not a number! Try again (or type 'undo' to remove last entry)")
            continue
        if check_outlier(number, ret):
            click.echo(f"Warning: {number} seems quite different from previous readings. Type 'undo' to remove it.")
        ret.append(number)
    return ret


def interactive(min_readings=6):
    click.echo("Tip: Type 'undo' to remove the last entered reading.")
    part100 = float(click.prompt("How many grams of hardener is needed for 100g of base"))
    if min_readings >= 6:
        click.echo("Measure the tara. Enter the observed tara at least six times.")
    else:
        click.echo("Measure the tara.")
    tara = interactive_read_numbers("tara", min_readings)
    if min_readings >= 6:
        click.echo("Add base and enter the observed total weight at least six times.")
    else:
        click.echo("Add base and enter the total weight.")
    base = interactive_read_numbers("total weight base+tara", min_readings)
    hardener = 0
    what_needed = "hardener"
    total_weight = None
    while True:
        result = find_hardener(tara, base, hardener, total_weight, what_needed, part100, min_readings)
        if result is None:
            # Error in measurement, ask for re-entry
            total_weight = interactive_read_numbers(f"total weight tara+base+hardener after adding {what_needed}", min_readings)
            continue
        (tara, base, hardener, hardener_needed) = result
        if hardener_needed < 0:
            what_needed = "base"
            mass_needed = -hardener_needed / part100 * 100
        else:
            what_needed = "hardener"
            mass_needed = hardener_needed
        if mass_needed < 0.25:
            return
        if min_readings >= 6:
            click.echo(f"Try to add {mass_needed:.1f}g {what_needed}. Enter the observed total weight at least six times.")
        else:
            click.echo(f"Try to add {mass_needed:.1f}g {what_needed}. Enter the total weight.")
        total_weight = interactive_read_numbers(f"total weight tara+base+hardener after adding {what_needed}", min_readings)


@click.command()
@click.option(
    "--min-readings", "-n",
    default=6,
    help="Minimum readings per measurement (default: 6 for wave compensation, use 1 for stable conditions)."
)
def cli(min_readings):
    """Interactive epoxy mix calculator.

    On a boat with waves, use the default of 6 readings per measurement
    to filter out wave-induced fluctuations.

    On stable ground, use --min-readings=1 for quick single measurements.
    """
    interactive(min_readings)


if __name__ == "__main__":
    cli()
