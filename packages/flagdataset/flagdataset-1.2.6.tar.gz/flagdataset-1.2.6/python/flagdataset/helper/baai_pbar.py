def pbar_show(fr, width=60)-> str:
    p1 = "#" * int(fr * width)
    p2 = "-" * (width - int(fr * width))
    return f"{p1}{p2}"

def pbar_time(time_s) -> str:
    if time_s <= 0:
        return "00:00"

    total_seconds = int(time_s)

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    elif hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def pbar_description(progress, rate_fmt, remaining) -> str:
    args = (
        progress.require_count,
        progress.download_submit_count,
        progress.download_count,
        progress.required_part_count,
        progress.download_part_count,
        progress.required_merged_count,
        progress.download_merged_count
     )

    return f"[ download (%s/%s/%s), part (%s/%s), merge (%s/%s): {rate_fmt},{remaining} ]" % args

def pbar_monitor(*args) -> str:
    pass