from explain_ok import explain

@explain
def complex_calc(raw_value, calibration_factor, noise_level, temperature, reference_temp):
    calibrated = raw_value * calibration_factor
    noise_adjusted = calibrated - (noise_level * calibrated)
    temp_factor = 1 + ((temperature - reference_temp) * 0.01)
    final = noise_adjusted * temp_factor
    return final / 100.0

result, explanation = complex_calc(850, 1.12, 0.04, 35, 25)
print(explanation.to_markdown())
