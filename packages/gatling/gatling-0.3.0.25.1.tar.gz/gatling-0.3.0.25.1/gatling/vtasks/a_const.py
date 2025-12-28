num_1K = 1024
num_1M = 1024 ** 2
num_1G = 1024 ** 3

network_bytes_per_sec = 1 * num_1M  # bytes/s
disk_bytes_per_sec = 500 * num_1M  # bytes/s

size_1KB = num_1K
size_1MB = num_1M
size_1GB = num_1G

size_target = size_1KB * 0.5


flops_1K = num_1K
flops_1M = num_1M
flops_1G = num_1G
flops_target = flops_1M * 0.5

cpu_flops_per_sec = 2.5 * num_1G

fix_error_rate = 0.05
