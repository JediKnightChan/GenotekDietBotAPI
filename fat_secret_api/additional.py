def hour_to_meal(hour):
    if 6 <= hour < 12:
        return "breakfast"
    elif 12 <= hour < 18:
        return "dinner"
    else:
        return "lunch"
