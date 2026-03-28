# Contributing to MintKit

First off, thank you for considering contributing to MintKit! Every contribution helps make transparent, honest token launches more accessible to developers everywhere.

---

## Code of Conduct

By participating in this project you agree to keep interactions respectful and constructive. We're building tools that handle real money — honesty and integrity matter here as much as in the code itself.

---

## What We're Looking For

We welcome contributions in these areas:

- **Bug fixes** — found something broken? Please fix it
- **New chain support** — Base, Ethereum L2s, other EVM chains
- **New social platforms** — Instagram, Facebook, Telegram, Discord promotion
- **Better scoring algorithms** — improve trend detection accuracy
- **Documentation** — clearer guides, better examples
- **Tests** — we need more test coverage
- **Security improvements** — wallet handling, key management

---

## What We Won't Accept

MintKit is built on transparency and honest dealing. We will not accept contributions that:

- Add wash trading or fake volume mechanisms
- Remove or weaken disclosure language
- Allow mint authority to remain after launch
- Enable manipulation of buyback timing for insider advantage
- Obscure bot identity in social media posts
- Add pump-and-dump mechanics of any kind

---

## Getting Started

### 1. Fork the repository

Click **Fork** in the top right of the GitHub page.

### 2. Clone your fork

```bash
git clone https://github.com/yourusername/mintkit.git
cd mintkit
```

### 3. Set up your environment

```bash
python -m pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

### 4. Create a branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/base-chain-support`
- `fix/buyback-trigger-bug`
- `docs/api-documentation`

---

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings to all functions
- Keep functions small and focused — one job per function
- Log important actions using the `log` module

### File Structure

```
core/           # Core engine modules
plugins/        # Optional add-on modules
cli/            # CLI interface
config/         # Configuration files
tests/          # Test suite
docs/           # Documentation
```

### Adding a New Chain

1. Create `core/chains/yourchain.py`
2. Implement these functions:
   - `deploy_token(config, wallet)`
   - `create_liquidity_pool(mint, wallet)`
   - `lock_liquidity(lp_address, days)`
   - `execute_buyback(mint, amount)`
   - `burn_tokens(mint, amount)`
3. Add chain option to `config/default.json`
4. Update `core/deployer.py` to support the new chain
5. Add tests in `tests/`

### Adding a New Social Platform

1. Create `core/platforms/yourplatform.py`
2. Implement these functions:
   - `post_launch(deployment)`
   - `post_buyback(buyback)`
3. Always include disclosure language
4. Always disclose bot identity
5. Add platform option to `config/default.json`

---

## Testing

Always test on devnet before submitting a pull request.

```bash
# Run on devnet
python mintkit.py deploy coin_config.example.json

# Check status
python mintkit.py status

# View transparency log
python mintkit.py report FADE
```

We do not have a full test suite yet — writing tests is a great first contribution!

---

## Submitting a Pull Request

1. Make sure your code works on devnet
2. Update documentation if needed
3. Add your changes to the relevant section of `ARCHITECTURE.md`
4. Submit your pull request with a clear description of what you changed and why

### PR Description Template

```
## What this PR does
Brief description of the change.

## Why
Why this change is needed or useful.

## Testing
How you tested this on devnet.

## Checklist
- [ ] Tested on devnet
- [ ] Disclosure language preserved
- [ ] Bot identity still disclosed in all posts
- [ ] No hardcoded API keys
- [ ] Documentation updated
```

---

## Reporting Bugs

Open a GitHub Issue with:

- What you were trying to do
- What you expected to happen
- What actually happened
- Your Python version and OS
- Any error messages from the terminal

---

## Questions

Open a GitHub Discussion if you have questions about the codebase or want to discuss a feature before building it.

---

## License

By contributing to MintKit you agree that your contributions will be licensed under the Apache 2.0 License.

---

*MintKit is built on the belief that automation and transparency can make crypto fairer for everyone. Every contribution moves us closer to that goal.*
