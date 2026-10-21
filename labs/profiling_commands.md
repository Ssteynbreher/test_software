```bash
perf stat -e cycles,instructions,cache-misses \
  qemu-system-arm -m 256 -M romulus-bmc \
  -monitor telnet:127.0.0.1:5555,server,nowait \
  -serial mon:stdio \
  -drive file=romulus.static.mtd,format=raw,if=mtd \
  -net nic \
  -net user,hostfwd=tcp:0.0.0.0:2222-:22,hostfwd=tcp:0.0.0.0:2443-:443,hostfwd=udp:0.0.0.0:2623-:623,hostname=qemu
```

```bash
vmstat 1
```

```bash
nmon
```

Оптимизация запуска QEMU:

- оставить `-nographic`, чтобы не тратить ресурсы на графический вывод;
- выделять OpenBMC ровно необходимый объем памяти, например `-m 256`;
- использовать рабочую копию MTD-образа, чтобы не повреждать исходный файл;
- ограничивать число параллельных нагрузочных пользователей при тестах Redfish;
- закрывать QEMU после тестов в CI/CD, чтобы процесс не оставался в фоне.
