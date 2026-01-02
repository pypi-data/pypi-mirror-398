import docker

client = docker.from_env()
container = client.containers.get("brainframe-core-1")
host_config = container.attrs['HostConfig']

# 1. Check NanoCpus
nano_cpus = host_config.get('NanoCpus', 0)
if nano_cpus > 0:
    print(f"Limit: {nano_cpus / 1e9} cores")

# 2. Check Quota/Period (if NanoCpus is 0)
else:
    quota = host_config.get('CpuQuota', 0)
    period = host_config.get('CpuPeriod', 100000)
    if quota > 0:
        print(f"Limit: {quota / period} cores")
    else:
        print("No hard CPU limit set")

# 3. Check Pinned Cores
cpuset = host_config.get('CpusetCpus')
if cpuset:
    print(f"Pinned to cores: {cpuset}")