import math
from functools import reduce
from loguru import logger

async def skips_calculator(
    target_seconds: int,
    disabled_skips: list[str] | None = None
) -> list[str]:
    """
    Calculates the most efficient way (using the fewest skips) to reach or exceed
    a target time, with an option to exclude specific skips.
    
    Args:
        target_seconds: The target time in seconds to skip.
        disabled_skips: An optional list of skip names (e.g., ["MS3", "MS5"])
            to be excluded from the available pool.
    
    Returns:
        A list of skip names that forms the optimal combination.
        Returns an empty list if there are no available skips or if
        target_seconds is less than or equal to 0.
    """
    logger.debug(f"skips_calculator called with target_seconds={target_seconds}, disabled_skips={disabled_skips}")
    if target_seconds <= 0:
        logger.warning(f"Invalid target_seconds: {target_seconds}")
        return []
    if disabled_skips is None:
        disabled_skips = []
        logger.debug("No disabled skips provided")
    all_skips = [
        ["MS1", 60],      # 1 minuta
        ["MS2", 300],     # 5 minut
        ["MS3", 600],     # 10 minut
        ["MS4", 1800],    # 30 minut
        ["MS5", 3600],    # 1 godzina
        ["MS6", 18000],   # 5 godzin
        ["MS7", 86400]    # 1 dzień
    ]
    available_skips = [skip for skip in all_skips if skip[0] not in disabled_skips]
    logger.debug(f"Available skips after filtering: {[skip[0] for skip in available_skips]}")
    if not available_skips:
        logger.warning("No available skips after filtering")
        return []
    values = [v for _, v in available_skips]
    logger.debug(f"Skip values: {values}")
    gcd_of_values = reduce(math.gcd, values)
    logger.debug(f"GCD of all skip values: {gcd_of_values}")
    final_target = math.ceil(target_seconds / gcd_of_values) * gcd_of_values
    logger.debug(f"Original target: {target_seconds}s, Adjusted final target: {final_target}s")
    sorted_skips = sorted(available_skips, key=lambda x: x[1], reverse=True)
    logger.debug(f"Sorted skips (descending by value): {[(name, value) for name, value in sorted_skips]}")
    result = []
    remaining_time = final_target
    for name, value in sorted_skips:
        count = remaining_time // value
        if count > 0:
            logger.debug(f"Adding {count}x {name} ({value}s each)")
            result.extend([name] * count)
            remaining_time -= value * count
            logger.debug(f"Remaining time after {name}: {remaining_time}s")
            
        if remaining_time == 0:
            logger.debug("Target reached")
            break
    logger.info(f"Calculated skip combination for {target_seconds}s: {result} (total: {final_target}s)")
    return result