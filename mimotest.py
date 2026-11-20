from mimo_ai import generate_response
import time
from mimo_voice import speak

print("Testing Mimo...")

start = time.perf_counter()

response = generate_response("angry")

speak(response)

print("Mimo says:", response)
print("Total time:", round(time.perf_counter() - start, 2), "seconds")
