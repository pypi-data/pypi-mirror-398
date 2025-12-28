# WASM API - Python SDK

BosBase runs WebAssembly modules using Wasmtime:
https://github.com/bytecodealliance/wasmtime

## Compile a WASM module

If you have the Rust compiler installed:

```bash
rustup target add wasm32-wasip2
cat <<'RS' > hello.rs
fn main() {
    println!("Hello, world!");
}
RS
rustc hello.rs --target wasm32-wasip2
```

You can validate it locally with:

```bash
wasmtime hello.wasm
```

## Execute via the BosBase Scripts API

```python
from bosbase import BosBase

pb = BosBase("http://127.0.0.1:8090")
pb.collection("_superusers").auth_with_password("admin@example.com", "password")

# Run via the dedicated wasm endpoint.
result = pb.scripts.wasm("--dir .", "hello.wasm")
print(result.get("output"))

# Or call the wasmtime CLI through the scripts command runner.
cmd = pb.scripts.command("./wasmtime hello.wasm")
print(cmd.get("output"))
```
