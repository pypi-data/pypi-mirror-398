def get_weekday(jd: float) -> str:
    # JD 0.5 is Monday
    # (JD + 1.5) % 7 -> 0: Sunday, 1: Monday, ...
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    idx = int((jd + 1.5) % 7)
    return days[idx]

