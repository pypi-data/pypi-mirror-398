
# sataid

Paket Python untuk membaca dan memvisualisasikan data citra satelit dengan antarmuka sederhana namun struktur internal yang tersamarkan.

## Instalasi

```bash
pip install sataid
```

## Penggunaan

```python
import sataid as sat

fname = '/path/to/file/IR20240908.Z0000'
sat = sat.read_sataid(fname)

sat.description()
sat.plot(cartopy=True, cmap='jet')
```
