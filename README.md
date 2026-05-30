# BackCRDT

## Development install

```bash
git clean -fdx
micromamba create -n backcrdt -y
micromamba activate backcrdt
micromamba install pip rust -y
pip install maturin
wget https://github.com/Horusiath/ysr/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
mv ysr-main/src/* src/
rm -rf ysr-main
cp src/lib.rs src/lib_original.rs
cat src/lib_backcrdt.rs src/lib_original.rs > /tmp/lib.rs && mv /tmp/lib.rs src/ && pip install -e . --group test
pytest -v
```

After every modification of the Rust code:

```bash
cat src/lib_backcrdt.rs src/lib_original.rs > /tmp/lib.rs && mv /tmp/lib.rs src/ && maturin develop
```
