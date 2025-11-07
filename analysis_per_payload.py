import os
import matplotlib.pyplot as plt
from math import isclose, sqrt, floor
import numpy as np

output_folder = "../wireless-assignment5/output"

data_per_payload = {}

def load_data():
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)

        short_name = filename[len("payload"):]
        lowdash_index = short_name.index("_")
        payload_size = short_name[:lowdash_index]
        if not payload_size in data_per_payload:
            data_per_payload[payload_size] = {}

        distance = short_name[lowdash_index + 1:short_name.index("cm")]

        data = []
        if os.path.isfile(file_path):
            with open(file_path, "r") as f:
                for line in f:
                    data.append(float(line.strip()))
        def change_timeout(el):
            if isclose(el, 10.0):
                return 10000.0
            return el    
        data = list(map(change_timeout, data))
        data_per_payload[payload_size][distance] = data

def generate_plots():
    for payload_size in data_per_payload:
        min_length = min(map(len, data_per_payload[payload_size].values()))
        data_arrays = []
        for dist in data_per_payload[payload_size]:
            data = data_per_payload[payload_size][dist][:min_length]
            #def is_not_timeout(el):
            #    return not isclose(el, 10000.0)
            #data = list(filter(is_not_timeout, data))
            data_arrays.append((float(dist.replace("_", ".")), data))
        
        data_arrays.sort(key=lambda v: v[0])
        plt.figure()
        for data in data_arrays[:len(data_arrays) // 2]:
            plt.plot(range(len(data[1])), data[1], label=f"Distance: {data[0]} cm")

        plt.title(f"Payload size: {payload_size} byte(s)")
        plt.legend()
        plt.show()

        plt.figure()
        for data in data_arrays[len(data_arrays) // 2:]:
            plt.plot(range(len(data[1])), data[1], label=f"Distance: {data[0]} cm")

        plt.title(f"Payload size: {payload_size} byte(s)")
        plt.legend()
        plt.show()

def mean(values):
    return sum(values) / len(values)

def stddev(values, m):
    return sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))

def confidence_interval(values):
    m = mean(values)
    s = stddev(values, m)
    n = len(values)

    z = 1.96  
    margin = z * (s / sqrt(n))

    return (m - margin, m + margin)

load_data()

distances = [2.5, 10, 20, 30, 40, 50, 55]

measurements = [
    [data_per_payload["1"]["2_5"], data_per_payload["100"]["2_5"], data_per_payload["180"]["2_5"]],
    [data_per_payload["1"]["10"], data_per_payload["100"]["10"], data_per_payload["180"]["10"]],
    [data_per_payload["1"]["20"], data_per_payload["100"]["20"], data_per_payload["180"]["20"]],
    [data_per_payload["1"]["30"], data_per_payload["100"]["30"], data_per_payload["180"]["30"]],
    [data_per_payload["1"]["40"], data_per_payload["100"]["40"], data_per_payload["180"]["40"]],
    [data_per_payload["1"]["50"], data_per_payload["100"]["50"], data_per_payload["180"]["50"]],
    [data_per_payload["1"]["55"], data_per_payload["100"]["55"], data_per_payload["180"]["55"]],
]

def closest_interval_to_mean(values, fraction):
    """Return (mean, lo, hi) where lo..hi is interval covering fraction of values
       that are closest (by absolute deviation) to the mean."""
    m = mean(values)
    def sort_by_dist_to_mean(a):
        return abs(a - m)
    sorted_vals = sorted(values, key=sort_by_dist_to_mean)
    k = max(1, int(floor(fraction * len(values))))
    vals_to_take = sorted_vals[:k]
    lo, hi = min(vals_to_take), max(vals_to_take)
    return (m, lo, hi)

n_dist = len(distances)
n_groups = 3

x = np.arange(n_dist)

width = 0.15
offsets = np.linspace(-width, width, n_groups)

fig, ax = plt.subplots(figsize=(10,6))
for g in range(n_groups):
    means = []
    low50 = []; high50 = []
    low80 = []; high80 = []

    for i in range(n_dist):
        mu, lo50, hi50 = closest_interval_to_mean(measurements[i][g], 0.5)
        _,  lo80, hi80 = closest_interval_to_mean(measurements[i][g], 0.9)

        means.append(mu)
        low50.append(lo50); high50.append(hi50)
        low80.append(lo80); high80.append(hi80)

    xs = x + offsets[g]

    for xi, lo, hi in zip(xs, low80, high80):
        ax.vlines(xi, lo, hi, linewidth=1, color=f"C{g}")

    for xi, lo, hi in zip(xs, low50, high50):
        ax.vlines(xi, lo, hi, linewidth=6, color=f"C{g}")

    ax.plot(xs, means, "o", markerfacecolor='black', markeredgecolor=f"C{g}", markeredgewidth=2, markersize=8, label=f"Payload {g+1}")

ax.set_xticks(x)
ax.set_xticklabels([str(d) for d in distances])
ax.set_xlabel('Distance (cm)')
ax.set_ylabel('Measured delay (ms)')
ax.set_title('50% interval closest to the mean per distance and payload')
ax.legend(loc="upper left")
ax.grid(axis='y', linestyle=':', alpha=0.5)

plt.tight_layout()
plt.show()

print("Confidence Interval for payload size 1 and distance <= 40 cm:")
min_length = min(map(len, data_per_payload["1"].values()))
data = data_per_payload["1"]["2_5"][:min_length] \
    + data_per_payload["1"]["10"][:min_length] \
    + data_per_payload["1"]["20"][:min_length] \
    + data_per_payload["1"]["30"][:min_length] \
    + data_per_payload["1"]["40"][:min_length]
print(confidence_interval(data))

distances = ["2_5", "10", "20", "30", "40", "50", "55"]
print("Standard deviations for payload size 1 and each of the distances:")
for dist in distances:
    m = mean(data_per_payload["1"][dist][:min_length])
    print("mean (d:", dist, "): ", round(m, 3))
    print("stddev: ", round(stddev(data_per_payload["1"][dist][:min_length], m), 3))

print("Standard deviations for payload size 100 and each of the distances:")
min_length = min(map(len, data_per_payload["100"].values()))
for dist in distances:
    m = mean(data_per_payload["100"][dist][:min_length])
    print("mean (d:", dist, "): ", round(m, 3))
    print("stddev: ", round(stddev(data_per_payload["100"][dist][:min_length], m), 3))

print("Standard deviations for payload size 180 and each of the distances:")
min_length = min(map(len, data_per_payload["180"].values()))
for dist in distances:
    m = mean(data_per_payload["180"][dist][:min_length])
    print("mean (d:", dist, "): ", round(m, 3))
    print("stddev: ", round(stddev(data_per_payload["180"][dist][:min_length], m), 3))

generate_plots()
